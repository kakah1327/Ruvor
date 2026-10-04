"""As views da API: a view final de `/api/`, as rotas de leitura de `/api/v1/` (RF-11), o
`/risk` (RF-13) e o pedido de calculo sob demanda, o `POST` do `/risk` (RF-14 a RF-19).

Toda view declara `permission_classes` no proprio corpo (D-86, V-09): o padrao do
`REST_FRAMEWORK` e `IsAuthenticated`, e uma view que esquecesse a sua nasceria fechada.

Este modulo nao importa o motor, nem direta nem indiretamente (RF-10): nada de `engine`,
`pandas`, `apps.risk.tasks`, `apps.risk.compute`, `apps.risk.snapshots` ou
`apps.assets.tasks`. O V-10 (`tests/api/test_sem_motor.py`) confere.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, ClassVar, NoReturn

from django.conf import settings
from django.db import transaction
from django.db.models import (
    BooleanField,
    Case,
    Exists,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.schema import ApiErrorSerializer
from apps.analytics.models import BehaviorMetric, ReturnHistogramBin, StressEpisode
from apps.api.errors import ApiError
from apps.api.models import ComputeRequest
from apps.api.ondemand import (
    OPEN_STATUSES,
    enqueue_chain,
    expire_stale,
    lock_on_demand,
    timeout,
)
from apps.api.permissions import ReadOpenWriteAccountReady
from apps.api.serializers import (
    HAS_RISK_DESCRIPTION,
    AssetDetailSerializer,
    AssetEventsOut,
    AssetItemSerializer,
    AssetListOut,
    AssetMetricsOut,
    AssetPricesOut,
    AssetRiskOut,
    BehaviorMetricSerializer,
    ComputeRequestSerializer,
    CorporateEventSerializer,
    DisclosureItemOut,
    DisclosuresOut,
    FundamentalsOut,
    IndicatorOut,
    InProgressRunSerializer,
    LatestRunSerializer,
    PeersOut,
    PriceSerializer,
)
from apps.assets.models import Asset, CorporateEvent, Price
from apps.fundamentals.models import Company, Disclosure, FundamentalIndicator
from apps.risk.models import RiskResult, RiskRun

# A paginacao da busca (RF-12).
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
# A paginacao dos comunicados (M1.6c, RF-03).
DISCLOSURES_DEFAULT_LIMIT = 10

_INTEGER = re.compile(r"-?[0-9]+")


# Nao e rota: e a resposta de rota inexistente (M4.2, RF-12).
@extend_schema(exclude=True)
class ApiNotFound(APIView):
    """A view final de `/api/` (D-86): rota inexistente responde `not_found` no formato
    da API, com `DEBUG` ligado ou nao — nao depende do `handler404` do Django, que o
    `DEBUG` ligado ignora.

    Levanta `NotFound` em todo metodo de `http_method_names`, para que um metodo sem
    tratador nao vire 405 numa rota que nao existe.
    """

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    def get(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def post(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def put(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def head(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    # O mesmo `ignore` dos stubs do DRF no `APIView.options`: o `View` do Django tipa o
    # pedido como `HttpRequest`, e o DRF entrega o `Request` dele.
    def options(  # type: ignore[override]
        self, request: Request, *args: Any, **kwargs: Any
    ) -> NoReturn:
        raise NotFound

    def trace(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound


def _invalid(parameter: str, message: str) -> ApiError:
    return ApiError(400, "invalid_parameter", message, {"parameter": parameter})


def _int_param(request: Request, name: str, default: int, low: int, high: int) -> int:
    """Um inteiro da query string entre `low` e `high`; ausente, o padrao. So digitos, com
    sinal opcional — o `int()` sozinho aceitaria espaco e sublinhado.
    """
    raw = request.query_params.get(name)
    if raw is None:
        return default
    if not _INTEGER.fullmatch(raw):
        raise _invalid(name, f"O parâmetro {name} precisa ser um número inteiro.")
    value = int(raw)
    if not low <= value <= high:
        raise _invalid(name, f"O parâmetro {name} precisa estar entre {low} e {high}.")
    return value


def _date_param(request: Request, name: str) -> date | None:
    raw = request.query_params.get(name)
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise _invalid(
            name, f"O parâmetro {name} precisa ser uma data no formato AAAA-MM-DD."
        ) from None


def _bool_param(request: Request, name: str) -> bool | None:
    raw = request.query_params.get(name)
    if raw is None:
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    raise _invalid(name, f"O parâmetro {name} aceita só true ou false.")


def _with_has_prices(assets: QuerySet[Asset]) -> QuerySet[Asset]:
    return assets.annotate(
        has_prices=Exists(Price.objects.filter(asset=OuterRef("pk")))
    )


# As execucoes fechadas: as que o `latest` considera (RF-13).
CLOSED_RUN_STATUSES = (RiskRun.Status.OK, RiskRun.Status.PARTIAL, RiskRun.Status.FAILED)


def _with_has_risk(assets: QuerySet[Asset]) -> QuerySet[Asset]:
    """RF-03 do M1.7: a execucao fechada mais recente (o `latest` do `/risk`) e `ok` ou `partial`."""
    latest_closed_status = Subquery(
        RiskRun.objects.filter(asset=OuterRef("pk"), status__in=CLOSED_RUN_STATUSES)
        .order_by("-calculated_at")
        .values("status")[:1]
    )
    return assets.annotate(latest_closed_status=latest_closed_status).annotate(
        has_risk=Case(
            When(
                latest_closed_status__in=(RiskRun.Status.OK, RiskRun.Status.PARTIAL),
                then=Value(True),
            ),
            default=Value(False),
            output_field=BooleanField(),
        )
    )


def _asset(ticker: str) -> Asset:
    """O ativo do catalogo pelo ticker, sem distincao de caixa; ausente, 404."""
    wanted = ticker.upper()
    asset = _with_has_prices(Asset.objects.filter(ticker=wanted)).first()
    if asset is None:
        raise ApiError(
            404, "asset_not_found", f"Ativo {wanted} não existe.", {"ticker": wanted}
        )
    return asset


def search_assets(q: str) -> QuerySet[Asset]:
    """A busca do RF-12: `q` aparado; ticker igual (grupo 0), prefixo de ticker (grupo 1),
    nome ou nome de pregao contendo `q` (grupo 2); ordem `(grupo, ticker)`. `q` vazio lista
    o catalogo inteiro, por ticker.
    """
    q = q.strip()
    assets = Asset.objects.all()
    if not q:
        return assets.order_by("ticker")
    upper = q.upper()
    return (
        assets.filter(
            Q(ticker__startswith=upper)
            | Q(name__unaccent__icontains=q)
            | Q(trading_name__unaccent__icontains=q)
        )
        .annotate(
            search_group=Case(
                When(ticker=upper, then=Value(0)),
                When(ticker__startswith=upper, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )
        .order_by("search_group", "ticker")
    )


class AssetListView(APIView):
    """`GET /api/v1/assets?q=&has_risk=&limit=&offset=`: a busca no catalogo, paginada
    (RF-12), com o filtro `has_risk` do M1.7 (RF-04).
    """

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(
        operation_id="v1_assets_search",  # M4.2: sem ele, colide com `/assets/{ticker}`
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR),
            OpenApiParameter(
                "has_risk",
                OpenApiTypes.BOOL,
                description=(
                    "Filtra pelo has_risk do item: true, só os ativos com ele "
                    "verdadeiro; false, só os com ele falso; ausente, todos. Só true "
                    "ou false, em minúsculas. " + HAS_RISK_DESCRIPTION
                ),
            ),
            OpenApiParameter("limit", OpenApiTypes.INT, default=DEFAULT_LIMIT),
            OpenApiParameter("offset", OpenApiTypes.INT, default=0),
        ],
        responses={200: AssetListOut},
    )
    def get(self, request: Request) -> Response:
        limit = _int_param(request, "limit", DEFAULT_LIMIT, 1, MAX_LIMIT)
        offset = _int_param(request, "offset", 0, 0, 2**63 - 1)
        has_risk = _bool_param(request, "has_risk")
        found = _with_has_risk(search_assets(request.query_params.get("q", "")))
        if has_risk is not None:
            # o plugin dos stubs nao enxerga a anotacao atras do `QuerySet[Asset]` que
            # `_with_has_risk` devolve, e acusa o campo; ele existe em tempo de execucao
            found = found.filter(has_risk=has_risk)  # type: ignore[misc]
        page = _with_has_prices(found)[offset : offset + limit]
        return Response(
            {
                "count": found.count(),
                "limit": limit,
                "offset": offset,
                "results": AssetItemSerializer(page, many=True).data,
            }
        )


class AssetDetailView(APIView):
    """`GET /api/v1/assets/{ticker}`: a identidade e o ultimo pregao."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(responses={200: AssetDetailSerializer})  # M4.2, RF-12
    def get(self, request: Request, ticker: str) -> Response:
        return Response(AssetDetailSerializer(_asset(ticker)).data)


class AssetPricesView(APIView):
    """`GET /api/v1/assets/{ticker}/prices?from=&to=`: a serie diaria no intervalo, inteira
    — sem paginacao, excecao declarada a D-86 (RF-11).
    """

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(  # M4.2, RF-12
        parameters=[
            OpenApiParameter("from", OpenApiTypes.DATE),
            OpenApiParameter("to", OpenApiTypes.DATE),
        ],
        responses={200: AssetPricesOut},
    )
    def get(self, request: Request, ticker: str) -> Response:
        start = _date_param(request, "from")
        end = _date_param(request, "to")
        if start is not None and end is not None and start > end:
            raise _invalid("from", "O parâmetro from não pode ser posterior a to.")
        asset = _asset(ticker)
        prices = Price.objects.filter(asset=asset)
        if start is not None:
            prices = prices.filter(date__gte=start)
        if end is not None:
            prices = prices.filter(date__lte=end)
        return Response(
            {
                "ticker": asset.ticker,
                "from": None if start is None else start.isoformat(),
                "to": None if end is None else end.isoformat(),
                "results": PriceSerializer(prices.order_by("date"), many=True).data,
            }
        )


class AssetEventsView(APIView):
    """`GET /api/v1/assets/{ticker}/events`: proventos e desdobramentos, inteiros."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(responses={200: AssetEventsOut})  # M4.2, RF-12
    def get(self, request: Request, ticker: str) -> Response:
        asset = _asset(ticker)
        events = CorporateEvent.objects.filter(asset=asset).order_by("date", "kind")
        return Response(
            {
                "ticker": asset.ticker,
                "results": CorporateEventSerializer(events, many=True).data,
            }
        )


class AssetMetricsView(APIView):
    """`GET /api/v1/assets/{ticker}/metrics`: a ultima linha de `gold.behavior_metric` e os
    baldes do histograma e os episodios de estresse (M3.3); `metric` nulo se o ativo nunca foi
    calculado.
    """

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(responses={200: AssetMetricsOut})  # M4.2, RF-12
    def get(self, request: Request, ticker: str) -> Response:
        asset = _asset(ticker)
        metric = (
            BehaviorMetric.objects.filter(asset=asset)
            .prefetch_related(
                Prefetch(
                    "bins",
                    queryset=ReturnHistogramBin.objects.order_by("bin_index"),
                ),
                Prefetch(
                    "stress_episodes",
                    queryset=StressEpisode.objects.order_by("start_date"),
                ),
            )
            .order_by("-calculated_at")
            .first()
        )
        return Response(
            {
                "ticker": asset.ticker,
                "metric": None
                if metric is None
                else BehaviorMetricSerializer(metric).data,
            }
        )


class AssetFundamentalsView(APIView):
    """`GET /api/v1/assets/{ticker}/fundamentals` (M1.6c, RF-02): a linha de
    `gold.fundamental_indicator` de maior `calculated_at` e a comparacao **dela** com os
    pares -- a ligacao um-para-um, nunca a comparacao mais recente do ativo. `indicator`
    nulo se o ativo nunca foi calculado; `peers` nulo se aquele indicador ficou sem
    comparacao.
    """

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(responses={200: FundamentalsOut})
    def get(self, request: Request, ticker: str) -> Response:
        asset = _asset(ticker)
        indicator = (
            FundamentalIndicator.objects.filter(asset=asset)
            .select_related("statement", "peer_comparison")
            .order_by("-calculated_at")
            .first()
        )
        # sem comparacao, o acesso levanta `RelatedObjectDoesNotExist`, um `AttributeError`
        peers = (
            None if indicator is None else getattr(indicator, "peer_comparison", None)
        )
        return Response(
            {
                "ticker": asset.ticker,
                "indicator": None
                if indicator is None
                else IndicatorOut(indicator).data,
                "peers": None if peers is None else PeersOut(peers).data,
            }
        )


class AssetDisclosuresView(APIView):
    """`GET /api/v1/assets/{ticker}/disclosures?category=&limit=&offset=` (M1.6c, RF-03):
    os comunicados da companhia a CVM, paginados.

    A ligacao e por valor, `silver.disclosure.code_cvm = silver.asset.code_cvm` (D-126),
    **sem passar por `silver.company`**, que nao tem a companhia sem ITR/DFP. Ordem
    `-delivered_on`, desempate por `link`. `company` nulo so quando o ativo nao tem
    `code_cvm`; o nome vem de `silver.company` e, sem linha la, do comunicado mais recente
    de qualquer categoria.
    """

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "category", OpenApiTypes.STR, enum=Disclosure.Category.values
            ),
            OpenApiParameter(
                "limit", OpenApiTypes.INT, default=DISCLOSURES_DEFAULT_LIMIT
            ),
            OpenApiParameter("offset", OpenApiTypes.INT, default=0),
        ],
        responses={200: DisclosuresOut},
    )
    def get(self, request: Request, ticker: str) -> Response:
        category = request.query_params.get("category", "")
        if category and category not in Disclosure.Category.values:
            raise _invalid(
                "category",
                "O parâmetro category precisa ser um de: "
                + ", ".join(Disclosure.Category.values)
                + ".",
            )
        limit = _int_param(request, "limit", DISCLOSURES_DEFAULT_LIMIT, 1, MAX_LIMIT)
        offset = _int_param(request, "offset", 0, 0, 2**63 - 1)
        asset = _asset(ticker)
        if not asset.code_cvm:
            return Response(
                {
                    "ticker": asset.ticker,
                    "company": None,
                    "count": 0,
                    "limit": limit,
                    "offset": offset,
                    "results": [],
                }
            )
        every = Disclosure.objects.filter(code_cvm=asset.code_cvm).order_by(
            "-delivered_on", "link"
        )
        name = (
            Company.objects.filter(code_cvm=asset.code_cvm)
            .values_list("name", flat=True)
            .first()
        )
        if name is None:
            name = every.values_list("company_name", flat=True).first()
        found = every.filter(category=category) if category else every
        return Response(
            {
                "ticker": asset.ticker,
                "company": {"code_cvm": asset.code_cvm, "name": name},
                "count": found.count(),
                "limit": limit,
                "offset": offset,
                "results": DisclosureItemOut(
                    found[offset : offset + limit], many=True
                ).data,
            }
        )


def risk_body(asset: Asset, now: datetime) -> dict[str, Any]:
    """O corpo do `/risk` (RF-13): o do `GET` e o de todo 202 do `POST`.

    - `latest`: a execucao fechada (`ok`, `partial`, `failed`) de maior `calculated_at`,
      com o manifesto e os resultados -- `model_name`, depois `alpha` decrescente
    - `in_progress`: a `running` de maior `calculated_at`, **se** for mais nova que o
      `latest` (ou nao ha `latest`) **e** tiver comecado dentro do prazo do RF-18; senao
      nula -- a `running` fora disso e execucao presa
    - `request`: o ultimo pedido sob demanda, com o `status` calculado (o aberto vencido sai
      `expired`, sem gravar: o `GET` nao escreve no banco)
    - `covered`: o ativo tem preco (D-51)
    """
    latest = (
        RiskRun.objects.filter(asset=asset, status__in=CLOSED_RUN_STATUSES)
        .select_related("price_run")
        .prefetch_related(
            Prefetch(
                "results",
                queryset=RiskResult.objects.order_by("model_name", "-alpha"),
            )
        )
        .order_by("-calculated_at")
        .first()
    )

    running = (
        RiskRun.objects.filter(asset=asset, status=RiskRun.Status.RUNNING)
        .order_by("-calculated_at")
        .first()
    )
    in_progress = None
    if (
        running is not None
        and (latest is None or running.calculated_at > latest.calculated_at)
        and running.calculated_at >= now - timeout()
    ):
        in_progress = running

    request = (
        ComputeRequest.objects.filter(asset=asset).order_by("-requested_at").first()
    )

    return {
        "ticker": asset.ticker,
        "covered": Price.objects.filter(asset=asset).exists(),
        "latest": None if latest is None else LatestRunSerializer(latest).data,
        "in_progress": None
        if in_progress is None
        else InProgressRunSerializer(in_progress).data,
        "request": None
        if request is None
        else ComputeRequestSerializer(request, context={"now": now}).data,
    }


def _before_insert() -> None:
    """Ponto de desvio dos testes concorrentes (V-14, V-15): entre as decisoes do `POST` e o
    `insert`, sob a trava. Nao faz nada; o `POST` o chama pelo nome global."""


class AssetRiskView(APIView):
    """`/api/v1/assets/{ticker}/risk`.

    - `GET`: o que existe e o que esta a caminho (RF-13). Le e nao escreve: o pedido vencido
      sai `expired` no corpo e continua aberto no banco (RF-18).
    - `POST`: o pedido de calculo sob demanda, so para ativo nunca calculado (RF-14), na
      ordem literal do RF-17 -- a trava global, a expiracao dos vencidos, as decisoes e o
      `insert`, numa transacao; o enfileiramento no `on_commit` (RF-19). So com conta pronta
      (M2.1b, RF-01; D-140): sem sessao, 401 `not_authenticated`; com a senha provisoria por
      trocar, 403 `password_change_required`. O `GET` segue aberto.
    """

    permission_classes = [  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
        ReadOpenWriteAccountReady
    ]
    api_key_scope: ClassVar[str | None] = (
        "read"  # M4.2, RF-07: a chave le (so metodo seguro)
    )

    @extend_schema(responses={200: AssetRiskOut})  # M4.2, RF-12
    def get(self, request: Request, ticker: str) -> Response:
        return Response(risk_body(_asset(ticker), timezone.now()))

    @extend_schema(  # M4.2, RF-12; o 401 e o 403, M2.1b, RF-01
        request=None,
        responses={
            202: AssetRiskOut,
            401: OpenApiResponse(
                ApiErrorSerializer, description="Sem sessão: `not_authenticated`."
            ),
            403: OpenApiResponse(
                ApiErrorSerializer,
                description=(
                    "Senha provisória por trocar: `password_change_required`; ou chave "
                    "de leitura: `api_key_not_allowed`."
                ),
            ),
        },
    )
    def post(self, request: Request, ticker: str) -> Response:
        """Decide **dentro** do `atomic` e levanta o erro **depois** de sair dele: um
        `ApiError` de dentro desfaria o `expire_stale`, e os vencidos tem de ficar gravados
        (RF-18). O corpo do 202 e lido depois do `atomic` -- e do `on_commit` --, e por isso
        mostra o pedido `failed` quando o broker recusa (RF-19).
        """
        asset = _asset(ticker)
        if asset.status == Asset.Status.INACTIVE:
            raise ApiError(
                422,
                "asset_inactive",
                f"Ativo {asset.ticker} está inativo.",
                {"ticker": asset.ticker},
            )
        now = timezone.now()
        with transaction.atomic():
            lock_on_demand()
            expire_stale(now)
            # a permissao so deixa chegar aqui quem tem conta pronta (D-140): o
            # `isinstance` so estreita o tipo para a FK, e o ramo `None` nao acontece
            error = _decide(
                asset, now, request.user if isinstance(request.user, User) else None
            )
        if error is not None:
            raise error
        return Response(risk_body(asset, now), status=202)


def _decide(asset: Asset, now: datetime, requested_by: User | None) -> ApiError | None:
    """Os passos 4 a 6 do RF-17, sob a trava e depois do `expire_stale`: devolve o 409 ou o
    429 -- para o `POST` levantar fora do `atomic` --, ou `None` para o 202, inserindo o
    pedido novo quando e o caso. `requested_by` e quem pediu (M2.1a, RF-26), sempre um
    usuario desde a D-140, que fecha o `POST` ao anonimo: so o pedido novo o grava; os dois
    202 sem pedido novo nao mudam nada."""
    if ComputeRequest.objects.filter(asset=asset, status__in=OPEN_STATUSES).exists():
        return None  # 202: o pedido aberto do ativo
    last_closed = (
        RiskRun.objects.filter(asset=asset, status__in=CLOSED_RUN_STATUSES)
        .order_by("-calculated_at")
        .values_list("calculated_at", flat=True)
        .first()
    )
    running = RiskRun.objects.filter(
        asset=asset, status=RiskRun.Status.RUNNING, calculated_at__gte=now - timeout()
    )
    if last_closed is not None:
        running = running.filter(calculated_at__gt=last_closed)
    if running.exists():
        return None  # 202, sem pedido novo: a `running` valida do ativo (RF-14)
    if last_closed is not None:
        return ApiError(
            409,
            "asset_already_covered",
            f"Ativo {asset.ticker} já tem risco calculado; quem o recalcula é a rotina "
            "diária.",
            risk_body(asset, now),
        )
    maximum: int = settings.RUVOR_ON_DEMAND_MAX
    if ComputeRequest.objects.filter(status__in=OPEN_STATUSES).count() >= maximum:
        return ApiError(
            429,
            "on_demand_queue_full",
            f"A fila de cálculo sob demanda está cheia ({maximum} pedidos abertos).",
            {"max": maximum},
        )
    _before_insert()
    req = ComputeRequest.objects.create(
        asset=asset,
        status=ComputeRequest.Status.QUEUED,
        requested_at=now,
        requested_by=requested_by,
    )
    request_id = req.pk
    # o nome global, que os testes substituem em `apps.api.views.enqueue_chain`
    transaction.on_commit(lambda: enqueue_chain(request_id))
    return None
