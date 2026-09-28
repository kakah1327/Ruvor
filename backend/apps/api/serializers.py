"""Os serializadores das rotas de leitura (RF-11). Cada corpo e uma lista fechada: o que
esta aqui e o que a rota devolve, nem mais nem menos — o V-11 confere campo a campo.

Decimal sai como string (o padrao do DRF, D-86) e instante no fuso de `TIME_ZONE`, com o
deslocamento. Os nomes de campo sao os das colunas.

Este modulo nao importa o motor, nem direta nem indiretamente (RF-10).
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.analytics.models import BehaviorMetric, ReturnHistogramBin
from apps.assets.models import Asset, CorporateEvent, Price

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


class AssetItemSerializer(serializers.ModelSerializer[Asset]):
    """O item da busca. `has_prices` vem da anotacao que a view poe no `queryset`."""

    has_prices = serializers.BooleanField(read_only=True)

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
