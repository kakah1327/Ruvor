"""As rotas da carteira sob `/api/v1/` (M2.2a, RF-08 a RF-12, RF-19 a RF-21).

Cada view confere a forma pelo serializador de entrada, chama o servico de
`apps/portfolios/services.py` e traduz o `PortfolioError` dele para o `ApiError` da D-86 pelo
`STATUS_BY_CODE`. A regra mora nos servicos; o corpo da resposta, nos serializadores de saida.

Toda view e `AccountReady` -- anonimo recebe 401 -- e declara `api_key_scope` no corpo (RF-19):
`"read"` deixa a chave de leitura listar e ler, e a regra do metodo seguro barra a escrita com
403; a de `holdings`, so com `PUT`, declara `None`.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, ClassVar

from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import AccountReady
from apps.accounts.tenancy import organization_scope
from apps.accounts.views import _query_int
from apps.api.errors import ApiError
from apps.portfolios import services
from apps.portfolios.errors import PortfolioError
from apps.portfolios.models import (
    Portfolio,
    PortfolioHolding,
    PortfolioRiskResult,
    PortfolioRiskRun,
)
from apps.portfolios.serializers import (
    HoldingsIn,
    PortfolioCreateIn,
    PortfolioListOut,
    PortfolioOneOut,
    PortfolioRiskOut,
    PortfolioUpdateIn,
)
from apps.risk import config as risk_config

# O status de cada codigo de `PortfolioError` (RF-20). Codigo fora daqui e defeito de programa:
# `KeyError`, que o tratador responde como 500.
STATUS_BY_CODE: dict[str, int] = {
    "invalid_parameter": 400,
    "portfolio_not_found": 404,
    "invalid_holdings": 400,
    "insufficient_history": 409,
    "portfolio_risk_up_to_date": 409,
    "portfolio_compute_busy": 429,
    "portfolio_queue_full": 429,
}


def portfolio_error_to_api(err: PortfolioError) -> ApiError:
    return ApiError(STATUS_BY_CODE[err.code], err.code, err.message, err.details)


def _data(serializer_class: type[Serializer[None]], request: Request) -> dict[str, Any]:
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    data: dict[str, Any] = serializer.validated_data
    return data


def _user(request: Request) -> User:
    user = request.user
    assert isinstance(user, User)
    return user


def portfolio_out(portfolio: Portfolio) -> dict[str, Any]:
    """O dict que o `PortfolioOut` le: a versao corrente e as posicoes dela, em ordem de ticker,
    por uma consulta so."""
    with organization_scope(portfolio.organization_id):
        version = services.current_version(portfolio)
        holdings = (
            PortfolioHolding.objects.filter(version=version)
            .select_related("asset")
            .order_by("asset__ticker")
        )
        return {
            "id": portfolio.public_id,
            "name": portfolio.name,
            "notional": portfolio.notional,
            "version": version.number,
            "holdings": [
                {"ticker": h.asset.ticker, "name": h.asset.name, "weight": h.weight}
                for h in holdings
            ],
            "created_at": portfolio.created_at,
            "updated_at": portfolio.updated_at,
            "version_created_at": version.created_at,
            "created_by": {
                "email": portfolio.created_by.email,
                "name": portfolio.created_by.name,
            },
        }


def _one(portfolio: Portfolio, status: int = 200) -> Response:
    return Response(
        PortfolioOneOut({"portfolio": portfolio_out(portfolio)}).data, status=status
    )


class PortfoliosView(APIView):
    """`GET portfolios` lista as da organizacao e `POST` cria (RF-08, RF-10)."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = "read"  # RF-19: a chave lista

    @extend_schema(
        operation_id="v1_portfolios_list",  # sem ele, colide com o de `portfolios/{id}`
        parameters=[
            OpenApiParameter("limit", OpenApiTypes.INT, default=50),
            OpenApiParameter("offset", OpenApiTypes.INT, default=0),
        ],
        responses={200: PortfolioListOut},
    )
    def get(self, request: Request) -> Response:
        limit = _query_int(request, "limit", 50)
        offset = _query_int(request, "offset", 0)
        try:
            count, found = services.list_portfolios(
                _user(request), limit=limit, offset=offset
            )
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        body = {
            "count": count,
            "limit": limit,
            "offset": offset,
            "results": [portfolio_out(p) for p in found],
        }
        return Response(PortfolioListOut(body).data)

    @extend_schema(request=PortfolioCreateIn, responses={201: PortfolioOneOut})
    def post(self, request: Request) -> Response:
        data = _data(PortfolioCreateIn, request)
        try:
            portfolio = services.create_portfolio(
                _user(request),
                name=data["name"],
                notional=data.get("notional"),
                holdings=data["holdings"],
            )
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        return _one(portfolio, status=201)


class PortfolioView(APIView):
    """`GET`, `PATCH` e `DELETE` de `portfolios/{id}` (RF-10, RF-11)."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = "read"  # RF-19: a chave le

    @extend_schema(responses={200: PortfolioOneOut})
    def get(self, request: Request, id: str) -> Response:
        try:
            portfolio = services.get_portfolio(_user(request), id)
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        return _one(portfolio)

    @extend_schema(request=PortfolioUpdateIn, responses={200: PortfolioOneOut})
    def patch(self, request: Request, id: str) -> Response:
        changes = _data(PortfolioUpdateIn, request)
        try:
            portfolio = services.update_portfolio(_user(request), id, changes)
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        return _one(portfolio)

    @extend_schema(responses={204: None})
    def delete(self, request: Request, id: str) -> Response:
        try:
            services.archive_portfolio(_user(request), id)
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        return Response(status=204)


class PortfolioHoldingsView(APIView):
    """`PUT portfolios/{id}/holdings` troca a composicao (RF-12). So pela sessao."""

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = None  # RF-19: so `PUT`, a chave nao alcanca

    @extend_schema(request=HoldingsIn, responses={200: PortfolioOneOut})
    def put(self, request: Request, id: str) -> Response:
        data = _data(HoldingsIn, request)
        try:
            portfolio = services.replace_holdings(_user(request), id, data["holdings"])
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        return _one(portfolio)


# --- o risco (RF-13, RF-16, RF-17) --------------------------------------------------------


def _level(
    alpha: Decimal, results: list[PortfolioRiskResult], notional: Decimal | None
) -> dict[str, Any]:
    """Um nivel do `summary`, pela regra do relatorio (M4.1, RF-03), sobre os `Decimal`."""
    computed = sorted(
        (r for r in results if r.var_latest is not None), key=lambda r: r.model_name
    )
    values = [r.var_latest for r in computed if r.var_latest is not None]
    var_min = min(values) if values else None
    var_max = max(values) if values else None
    return {
        "alpha": alpha,
        "computed": [r.model_name for r in computed],
        "var_min": var_min,
        "var_max": var_max,
        "loss_brl_min": services.loss_brl(notional, var_min),
        "loss_brl_max": services.loss_brl(notional, var_max),
        # lista, sem eleger nenhum (D-65); vazia e resultado legitimo
        "not_rejected": sorted(r.model_name for r in results if r.adequate is True),
    }


def _run_out(
    run: PortfolioRiskRun, number: int, notional: Decimal | None
) -> dict[str, Any]:
    results = list(run.results.all())  # pre-carregados em `model_name`, `-alpha`
    return {
        "id": run.pk,
        "version": number,
        "status": run.status,
        "calculated_at": run.calculated_at,
        "finished_at": run.finished_at,
        "engine_version": run.engine_version,
        "seed": run.seed,
        "train_window_days": run.train_window_days,
        "first_date": run.first_date,
        "as_of_date": run.as_of_date,
        "session_count": run.session_count,
        "train_count": run.train_count,
        "test_count": run.test_count,
        "requested_models": run.requested_models,
        "series_sha256": run.series_sha256,
        "price_run_id": run.price_run_id,
        "requested_by": {
            "email": run.requested_by.email,
            "name": run.requested_by.name,
        },
        "results": [
            {
                "model_name": r.model_name,
                "model_category": r.model_category,
                "alpha": r.alpha,
                "hyperparameters": r.hyperparameters,
                "var_latest": r.var_latest,
                "var_mean": r.var_mean,
                "violations": r.violations,
                "expected_violations": r.expected_violations,
                "kupiec_passed": r.kupiec_passed,
                "kupiec_p_value": r.kupiec_p_value,
                "christoffersen_passed": r.christoffersen_passed,
                "christoffersen_p_value": r.christoffersen_p_value,
                "dq_passed": r.dq_passed,
                "dq_p_value": r.dq_p_value,
                "adequate": r.adequate,
                "error": r.error,
                "loss_brl": services.loss_brl(notional, r.var_latest),
            }
            for r in results
        ],
        "summary": [
            _level(alpha, [r for r in results if r.alpha == alpha], notional)
            for alpha in sorted({r.alpha for r in results}, reverse=True)
        ],
    }


def portfolio_risk_out(risk: services.PortfolioRisk) -> dict[str, Any]:
    """O dict que o `PortfolioRiskOut` le. A perda em reais e calculada aqui, com o `notional`
    atual -- nunca gravada (RF-17)."""
    portfolio = risk.portfolio
    notional = portfolio.notional
    number = risk.version.number
    with organization_scope(portfolio.organization_id):
        progress = risk.in_progress
        return {
            "portfolio_risk": {
                "portfolio_id": portfolio.public_id,
                "version": number,
                "notional": notional,
                "latest": None
                if risk.latest is None
                else _run_out(risk.latest, number, notional),
                "in_progress": None
                if progress is None
                else {
                    "id": progress.pk,
                    "version": number,
                    "calculated_at": progress.calculated_at,
                    "requested_models": progress.requested_models,
                    "results_written": progress.results.count(),
                    "results_expected": len(progress.requested_models)
                    * len(risk_config.ALPHAS),
                },
            }
        }


class PortfolioRiskView(APIView):
    """`GET portfolios/{id}/risk` le e `POST` pede o risco da versao corrente (RF-13, RF-16).

    `"read"` com `POST`: a chave le, e a regra do metodo seguro barra o pedido (RF-19).
    """

    permission_classes = [AccountReady]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo
    api_key_scope: ClassVar[str | None] = "read"  # RF-19: a chave le o risco

    def _body(self, request: Request, id: str) -> dict[str, Any]:
        try:
            risk = services.read_risk(_user(request), id, timezone.now())
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        return PortfolioRiskOut(portfolio_risk_out(risk)).data

    @extend_schema(responses={200: PortfolioRiskOut})
    def get(self, request: Request, id: str) -> Response:
        return Response(self._body(request, id))

    @extend_schema(request=None, responses={202: PortfolioRiskOut})
    def post(self, request: Request, id: str) -> Response:
        try:
            services.request_risk(_user(request), id, timezone.now())
        except PortfolioError as err:
            raise portfolio_error_to_api(err) from err
        # depois do commit e do `on_commit`: com o corretor recusando, ja traz a `failed`
        return Response(self._body(request, id), status=202)
