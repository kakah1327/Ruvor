"""Os serializadores das rotas de leitura (RF-11) e do `/risk` (RF-13). Cada corpo e uma lista fechada: o que
esta aqui e o que a rota devolve, nem mais nem menos — o V-11 confere campo a campo.

Decimal sai como string (o padrao do DRF, D-86) e instante no fuso de `TIME_ZONE`, com o
deslocamento. Os nomes de campo sao os das colunas.

Este modulo nao importa o motor, nem direta nem indiretamente (RF-10).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.analytics.models import BehaviorMetric, ReturnHistogramBin
from apps.api.models import ComputeRequest
from apps.api.ondemand import effective_status, expired_reason, is_expired
from apps.assets.models import Asset, CollectionRun, CorporateEvent, Price
from apps.fundamentals.models import (
    Disclosure,
    FinancialStatement,
    FundamentalIndicator,
    PeerComparison,
)
from apps.risk.config import ALPHAS
from apps.risk.models import RiskResult, RiskRun

# As 26 colunas de metrica de `gold.behavior_metric`, com o nome da coluna, na ordem de
# `apps/analytics/models.py`. O V-11 confere contra `BehaviorMetric._meta`.
METRIC_COLUMNS = (
    "return_1m",
    "return_3m",
    "return_6m",
    "return_12m",
    "return_36m",
    "return_60m",
    "return_120m",
    "return_ytd",
    "volatility_12m",
    "volatility_60m",
    "max_drawdown",
    "max_drawdown_peak_date",
    "max_drawdown_trough_date",
    "max_drawdown_recovery_date",
    "max_drawdown_recovery_sessions",
    "beta_60m",
    "correlation_60m",
    "benchmark_observations",
    "skewness",
    "excess_kurtosis",
    "statistical_observations",
    "dividends_12m",
    "dividend_payments_12m",
    "dividend_yield_12m",
    "avg_volume_21d",
    "avg_volume_252d",
)


# A regra do `has_risk` (M1.7, RF-03), na descricao do parametro da busca e do campo do item
# (RF-06): o esquema OpenAPI a diz nos dois lugares.
HAS_RISK_DESCRIPTION = (
    "Verdadeiro quando o último cálculo fechado terminou `ok` ou `partial`: a execução "
    "de risco mais recente com status `ok`, `partial` ou `failed` — a mesma que o `/risk` "
    "devolve como `latest`. Uma execução `running` não conta."
)


class AssetItemSerializer(serializers.ModelSerializer[Asset]):
    """O item da busca. `has_prices` e `has_risk` vem das anotacoes que a view poe no
    `queryset`.
    """

    has_prices = serializers.BooleanField(read_only=True)
    has_risk = serializers.BooleanField(read_only=True, help_text=HAS_RISK_DESCRIPTION)

    class Meta:
        model = Asset
        fields = (
            "ticker",
            "name",
            "trading_name",
            "kind",
            "sector",
            "status",
            "has_prices",
            "has_risk",
        )


class LastPriceSerializer(serializers.ModelSerializer[Price]):
    """O ultimo pregao, dentro da identidade do ativo."""

    class Meta:
        model = Price
        fields = ("date", "close", "adj_close")


class AssetDetailSerializer(serializers.ModelSerializer[Asset]):
    """A identidade do ativo (camada 1). `has_prices` vem da anotacao da view; `last_price`
    e nulo quando o ativo nao tem preco.
    """

    has_prices = serializers.BooleanField(read_only=True)
    last_price = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = (
            "ticker",
            "name",
            "trading_name",
            "kind",
            "sector",
            "subsector",
            "segment",
            "listing_segment",
            "status",
            "has_prices",
            "last_price",
        )

    @extend_schema_field(LastPriceSerializer(allow_null=True))  # M4.2, RF-12
    def get_last_price(self, asset: Asset) -> dict[str, Any] | None:
        last = Price.objects.filter(asset=asset).order_by("-date").first()
        return None if last is None else dict(LastPriceSerializer(last).data)


class PriceSerializer(serializers.ModelSerializer[Price]):
    class Meta:
        model = Price
        fields = ("date", "open", "high", "low", "close", "adj_close", "volume")


class CorporateEventSerializer(serializers.ModelSerializer[CorporateEvent]):
    class Meta:
        model = CorporateEvent
        fields = ("date", "kind", "amount", "numerator", "denominator")


class HistogramBinSerializer(serializers.ModelSerializer[ReturnHistogramBin]):
    class Meta:
        model = ReturnHistogramBin
        fields = ("bin_index", "lower_bound", "upper_bound", "count")


class BehaviorMetricSerializer(serializers.ModelSerializer[BehaviorMetric]):
    """A linha de metrica: o cabecalho, as 26 colunas e os baldes. A view entrega os baldes
    ja ordenados por `bin_index` (prefetch ordenado).
    """

    histogram = HistogramBinSerializer(source="bins", many=True, read_only=True)

    class Meta:
        model = BehaviorMetric
        fields = (
            "calculated_at",
            "as_of_date",
            "first_price_date",
            "price_count",
            *METRIC_COLUMNS,
            "histogram",
        )


# --- /risk (RF-13) -------------------------------------------------------------------------


class PriceRunSerializer(serializers.ModelSerializer[CollectionRun]):
    """A coleta de preco que a execucao usou, com a data dela (D-15)."""

    class Meta:
        model = CollectionRun
        fields = ("id", "source", "started_at", "finished_at")


class RiskResultSerializer(serializers.ModelSerializer[RiskResult]):
    """Um resultado por (modelo, nivel) -- inclusive o que falhou, com o `error`."""

    class Meta:
        model = RiskResult
        fields = (
            "model_name",
            "model_category",
            "alpha",
            "hyperparameters",
            "var_latest",
            "var_mean",
            "violations",
            "expected_violations",
            "kupiec_passed",
            "kupiec_p_value",
            "christoffersen_passed",
            "christoffersen_p_value",
            "dq_passed",
            "dq_p_value",
            "basel_zone",
            "adequate",
            "error",
            "reused_snapshots",
            "trained_snapshots",
        )


class LatestRunSerializer(serializers.ModelSerializer[RiskRun]):
    """A ultima execucao fechada: o manifesto inteiro e os resultados. A view entrega os
    resultados ja ordenados -- `model_name`, depois `alpha` decrescente (prefetch ordenado).
    """

    price_run = PriceRunSerializer(read_only=True)
    results = RiskResultSerializer(many=True, read_only=True)

    class Meta:
        model = RiskRun
        fields = (
            "id",
            "calculated_at",
            "finished_at",
            "status",
            "engine_version",
            "seed",
            "train_window_days",
            "as_of_date",
            "first_price_date",
            "price_count",
            "train_count",
            "test_count",
            "price_run",
            "requested_models",
            "full_recompute",
            "results",
        )


class InProgressRunSerializer(serializers.ModelSerializer[RiskRun]):
    """A execucao em andamento: quantos resultados ja gravou e quantos espera
    (`len(requested_models) * len(ALPHAS)`).
    """

    results_written = serializers.SerializerMethodField()
    results_expected = serializers.SerializerMethodField()

    class Meta:
        model = RiskRun
        fields = (
            "id",
            "calculated_at",
            "requested_models",
            "results_written",
            "results_expected",
        )

    def get_results_written(self, run: RiskRun) -> int:
        return run.results.count()

    def get_results_expected(self, run: RiskRun) -> int:
        return len(run.requested_models) * len(ALPHAS)


class ComputeRequestSerializer(serializers.ModelSerializer[ComputeRequest]):
    """O ultimo pedido sob demanda. O `status` e o **calculado** (RF-18): o pedido gravado
    aberto e vencido pelo relogio sai `expired`, sem gravar, e com o motivo de expirado
    (`expirado (N min)`, o da lista fechada do RF-15) -- o corpo e coerente com o que o
    pedido vai ser quando alguem o fechar. `finished_at` continua nulo: ninguem o fechou.
    O instante vem do contexto, `now`.
    """

    status = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField()
    risk_run_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = ComputeRequest
        fields = (
            "id",
            "status",
            "requested_at",
            "finished_at",
            "reason",
            "error",
            "risk_run_id",
        )

    def get_status(self, req: ComputeRequest) -> str:
        now: datetime = self.context["now"]
        return effective_status(req, now)

    def get_reason(self, req: ComputeRequest) -> str:
        now: datetime = self.context["now"]
        return expired_reason() if is_expired(req, now) else req.reason


# --- /fundamentals e /disclosures (M1.6c, RF-02 e RF-03) -----------------------------------

# Os seis indicadores que a comparacao com os pares posiciona, na ordem de
# `apps/fundamentals/models.py`: `{ind}_peer_median`, `{ind}_percentile`, `{ind}_peer_count`.
PEER_INDICATORS = ("roe", "net_margin", "ebit_margin", "net_debt_to_equity", "pe", "pb")


class StatementOut(serializers.ModelSerializer[FinancialStatement]):
    """O balanco de onde o indicador saiu."""

    class Meta:
        model = FinancialStatement
        fields = ("reference_date", "source", "scope")


class IndicatorOut(serializers.ModelSerializer[FundamentalIndicator]):
    """A linha de `gold.fundamental_indicator`, com os nomes das colunas (D-86), na ordem do
    modelo; `statement` e o balanco, aninhado."""

    statement = StatementOut(read_only=True)

    class Meta:
        model = FundamentalIndicator
        fields = (
            "calculated_at",
            "statement",
            "account_plan",
            "scope",
            "revenue_ttm",
            "ebit_ttm",
            "net_income_ttm",
            "equity_parent",
            "total_assets",
            "gross_debt",
            "cash",
            "net_debt",
            "net_margin",
            "ebit_margin",
            "roe",
            "net_debt_to_equity",
            "price_date",
            "close",
            "shares_total",
            "eps",
            "bvps",
            "pe",
            "pb",
            "per_share_missing",
            "market_cap",
            "market_cap_missing",
        )


class PeerIndicatorOut(serializers.Serializer[PeerComparison]):
    """A posicao de um indicador entre os pares: as tres colunas `{ind}_*` agrupadas.

    Declarado com `source="*"` e o nome do indicador: le as tres colunas da comparacao.
    Os decimais saem com as casas da coluna (`decimal_places=None` nao quantiza)."""

    median = serializers.DecimalField(
        max_digits=None, decimal_places=None, allow_null=True
    )
    percentile = serializers.DecimalField(
        max_digits=None, decimal_places=None, allow_null=True
    )
    count = serializers.IntegerField(allow_null=True)

    def __init__(self, *args: Any, indicator: str = "", **kwargs: Any) -> None:
        self.indicator = indicator
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance: PeerComparison) -> dict[str, Any]:
        return {
            "median": getattr(instance, f"{self.indicator}_peer_median"),
            "percentile": getattr(instance, f"{self.indicator}_percentile"),
            "count": getattr(instance, f"{self.indicator}_peer_count"),
        }


class PeersOut(serializers.ModelSerializer[PeerComparison]):
    """A comparacao do proprio indicador com os pares (M3.2)."""

    roe = PeerIndicatorOut(indicator="roe", source="*", read_only=True)
    net_margin = PeerIndicatorOut(indicator="net_margin", source="*", read_only=True)
    ebit_margin = PeerIndicatorOut(indicator="ebit_margin", source="*", read_only=True)
    net_debt_to_equity = PeerIndicatorOut(
        indicator="net_debt_to_equity", source="*", read_only=True
    )
    pe = PeerIndicatorOut(indicator="pe", source="*", read_only=True)
    pb = PeerIndicatorOut(indicator="pb", source="*", read_only=True)

    class Meta:
        model = PeerComparison
        fields = (
            "peer_level",
            "group_sector",
            "group_subsector",
            "group_segment",
            *PEER_INDICATORS,
        )


class DisclosureItemOut(serializers.ModelSerializer[Disclosure]):
    class Meta:
        model = Disclosure
        fields = (
            "delivered_on",
            "reference_date",
            "category",
            "kind",
            "species",
            "title",
            "link",
        )


# --- os envelopes, so descricao, para o esquema OpenAPI (M4.2, RF-12) -----------------------
# As views montam o corpo a mao; estes serializadores so o descrevem, reusando os de item.


class AssetListOut(serializers.Serializer[None]):
    count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    results = AssetItemSerializer(many=True)


class AssetPricesOut(serializers.Serializer[None]):
    ticker = serializers.CharField()
    # `from` e palavra reservada: o campo entra pelo `get_fields`, na ordem do corpo
    to = serializers.DateField(allow_null=True)
    results = PriceSerializer(many=True)

    def get_fields(self) -> dict[str, serializers.Field[Any, Any, Any, Any]]:
        fields = super().get_fields()
        return {
            "ticker": fields["ticker"],
            "from": serializers.DateField(allow_null=True),
            "to": fields["to"],
            "results": fields["results"],
        }


class AssetEventsOut(serializers.Serializer[None]):
    ticker = serializers.CharField()
    results = CorporateEventSerializer(many=True)


class AssetMetricsOut(serializers.Serializer[None]):
    ticker = serializers.CharField()
    metric = BehaviorMetricSerializer(allow_null=True)


class AssetRiskOut(serializers.Serializer[None]):
    """`risk_body`."""

    ticker = serializers.CharField()
    covered = serializers.BooleanField()
    latest = LatestRunSerializer(allow_null=True)
    in_progress = InProgressRunSerializer(allow_null=True)
    request = ComputeRequestSerializer(allow_null=True)


class FundamentalsOut(serializers.Serializer[None]):
    ticker = serializers.CharField()
    indicator = IndicatorOut(allow_null=True)
    peers = PeersOut(allow_null=True)


class CompanyOut(serializers.Serializer[None]):
    code_cvm = serializers.CharField()
    name = serializers.CharField(allow_null=True)


class DisclosuresOut(serializers.Serializer[None]):
    ticker = serializers.CharField()
    company = CompanyOut(allow_null=True)
    count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    results = DisclosureItemOut(many=True)
