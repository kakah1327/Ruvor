"""Camada 2: as metricas de comportamento derivadas da `silver`, no esquema `gold`.

O esquema vai embutido no `db_table`, com aspas no meio, como em `assets`: e o contrato da
D-38 — mudar as aspas muda o esquema em que a tabela nasce. A chave primaria nao e
declarada: o `DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

`behavior_metric` e so-acrescimo (D-16 estendida a camada 2): recalcular insere linha nova,
nenhum caminho do codigo faz `update` ou `delete`. Os baldes do histograma pendem da linha
que os originou, e por isso — e so por isso — a FK deles e `CASCADE`, nao `PROTECT`: o balde
nao tem vida propria.
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models


class BehaviorMetric(models.Model):
    """Uma linha por `(asset, calculated_at)`: as metricas de comportamento daquela execucao.

    `calculated_at` nao leva `auto_now_add`: quem grava escreve o `now()`, uma vez por
    execucao, como `Asset.created_at` faz. `as_of_date` e o ultimo pregao **deste ativo**,
    nunca o ultimo da tabela inteira.

    Nulo aqui e sempre "nao da para calcular" (RF-12), nunca zero disfarcado. As tres
    colunas de dividendo sao a excecao declarada: quem nao pagou nada grava `0`, porque ai
    da para calcular e o resultado e zero.
    """

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="behavior_metrics",
    )
    calculated_at = models.DateTimeField()
    as_of_date = models.DateField()
    first_price_date = models.DateField()
    price_count = models.IntegerField()
    return_1m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    return_3m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    return_6m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    return_12m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    return_36m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    return_60m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    return_120m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    return_ytd = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    volatility_12m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    volatility_60m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    max_drawdown = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    max_drawdown_peak_date = models.DateField(null=True)
    max_drawdown_trough_date = models.DateField(null=True)
    max_drawdown_recovery_date = models.DateField(null=True)
    max_drawdown_recovery_sessions = models.IntegerField(null=True)
    beta_60m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    correlation_60m = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    benchmark_observations = models.IntegerField(null=True)
    skewness = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    excess_kurtosis = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    statistical_observations = models.IntegerField(null=True)
    dividends_12m = models.DecimalField(max_digits=18, decimal_places=6)
    dividend_payments_12m = models.IntegerField()
    dividend_yield_12m = models.DecimalField(max_digits=18, decimal_places=10)
    avg_volume_21d = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    avg_volume_252d = models.DecimalField(max_digits=20, decimal_places=2, null=True)

    class Meta:
        db_table = 'gold"."behavior_metric'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["asset", "calculated_at"],
                name="behavior_metric_asset_calculated_at",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["asset", "-calculated_at"], name="behavior_metric_asset_recent"
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.calculated_at:%Y-%m-%d %H:%M:%S}"


class ReturnHistogramBin(models.Model):
    """Um balde do histograma de retornos. Sempre 42 por linha de metrica, indice 0 a 41.

    Unico em `(metric, bin_index)`, e nao em `(metric, lower_bound)`: `lower_bound` e nulo
    no balde aberto da esquerda, e no PostgreSQL um `NULL` nao colide com outro `NULL` num
    indice unico — dois baldes abertos a esquerda passariam pela restricao.
    """

    metric = models.ForeignKey(
        BehaviorMetric,
        on_delete=models.CASCADE,
        related_name="bins",
    )
    bin_index = models.IntegerField()
    lower_bound = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    upper_bound = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    count = models.IntegerField()

    class Meta:
        db_table = 'gold"."return_histogram_bin'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["metric", "bin_index"], name="return_histogram_bin_metric_index"
            )
        ]

    def __str__(self) -> str:
        return f"{self.metric_id} #{self.bin_index}"
