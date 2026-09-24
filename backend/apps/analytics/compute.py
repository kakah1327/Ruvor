"""A orquestracao do calculo: laco por ativo, transacao por ativo, escrita e relatorio.

O molde e `apps/assets/prices.py`, com tres divergencias deliberadas, todas do plano:

- **sem `SOURCE` e sem `CollectionRun`**: `gold.behavior_metric` nao tem FK para coleta, e
  manifesto esta fora do escopo deste bloco. Copiar a constante do molde convidaria a criar
  uma execucao em `bronze` que nenhuma tabela referencia;
- **`_resolve` e `InvalidTickers` sao reescritos aqui**, nao importados de `apps/assets/`. A
  regra e a mesma, mas `_resolve` e privado e de outro app: importa-lo acoplaria `analytics`
  a superficie interna de `assets` e faria a excecao levantada ser
  `apps.assets.prices.InvalidTickers` -- que o `except InvalidTickers` da casca, importando
  daqui, nao pegaria;
- **`total` do resumo inclui os pulados**, ao contrario de `PricesReport.render()`. O exemplo
  da spec ("O comando") e contrato e exige `4 ativos, 3 ok, 0 falhos, 1 pulados` com quatro
  linhas acima.

`write_metrics` e chamada pelo nome global, como `write_conformed` em `prices.py`: e o ponto
que o teste da transacao por ativo substitui com `monkeypatch.setattr`.

`gold.behavior_metric` e so-acrescimo (RF-02): nenhum caminho daqui faz `update` ou `delete`.
Recalcular insere linha nova.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from django.db import transaction
from django.utils import timezone

from apps.analytics.metrics import (
    IBOV_TICKER,
    RETURN_WINDOWS,
    VOLATILITY_WINDOWS,
    Bar,
    Dividend,
    Metrics,
    compute,
)
from apps.analytics.models import BehaviorMetric, ReturnHistogramBin
from apps.assets.models import Asset, CorporateEvent, Price

# As colunas anulaveis que entram em `null_columns` quando saem nulas, na ordem da tabela
# da spec. As da queda ficam de fora: `max_drawdown`, `peak_date` e `trough_date` nunca sao
# nulas -- a serie nunca chega vazia --, e nulo nas duas de recuperacao e informacao (a
# queda nao foi recuperada), nao falta de historico.
NULLABLE_COLUMNS: tuple[str, ...] = (
    *(f"return_{months}m" for months in RETURN_WINDOWS),
    "return_ytd",
    *(f"volatility_{months}m" for months in VOLATILITY_WINDOWS),
    "beta_60m",
    "correlation_60m",
    "benchmark_observations",
    "skewness",
    "excess_kurtosis",
    "statistical_observations",
    "avg_volume_21d",
    "avg_volume_252d",
)

# As tres do indice so entram quando havia indice com que comparar: no proprio IBOV o nulo
# e identidade, e na ausencia do indice o relatorio ja traz a linha de aviso do RF-16 --
# repeti-la em todo ativo seria ruido.
BENCHMARK_COLUMNS = ("beta_60m", "correlation_60m", "benchmark_observations")

BENCHMARK_WARNING = "aviso: IBOV sem preco — beta e correlacao nulos em todos os ativos"
NO_CANDIDATES = "nenhum ativo ativo com preco; informe tickers"

SKIPPED_INACTIVE = "inativo"
SKIPPED_NO_PRICE = "sem preco"


class InvalidTickers(Exception):
    """Ticker desconhecido ou inativo pedido por argumento (RF-15). Nada foi escrito."""

    def __init__(self, tickers: list[str]) -> None:
        super().__init__(", ".join(tickers))
        self.tickers = tickers


@dataclass(frozen=True)
class AssetResult:
    """Uma linha do relatorio: o que aconteceu com um ativo.

    `price_count` e `as_of_date` sao `0` e `None` no ativo pulado, e a convencao da spec e
    que isso significa "nada foi **considerado**", nao "nao tem preco": o `inativo` do
    exemplo tem serie, ela e que nao foi lida.
    """

    ticker: str
    price_count: int
    as_of_date: date | None
    null_columns: list[str]
    error: str | None
    skipped: bool
    reason: str = ""

    def render(self) -> str:
        quando = "-" if self.as_of_date is None else f"ate {self.as_of_date}"
        if self.skipped:
            cauda = f"pulado: {self.reason}"
        elif self.error is not None:
            cauda = f"FALHOU ({self.error})"
        elif self.null_columns:
            cauda = f"ok  (nulas: {', '.join(self.null_columns)})"
        else:
            cauda = "ok"
        return f"{self.ticker:<12}{self.price_count:>8} pregoes  {quando:<14}  {cauda}"


@dataclass(frozen=True)
class MetricsReport:
    """O relatorio de uma execucao: uma linha por ativo, o aviso do RF-16 e o resumo."""

    results: list[AssetResult]
    elapsed: float
    benchmark_missing: bool = False

    @property
    def failed(self) -> bool:
        return any(r.error for r in self.results)

    def render(self) -> str:
        lines = [r.render() for r in self.results]
        processed = [r for r in self.results if not r.skipped]
        if not processed:
            # "informe tickers" so sai a quem nao informou nenhum: manda-la a quem acabou
            # de informar um e o relatorio mentindo. Quem informou tickers nao tem pulo
            # por `inativo` -- `_resolve` aborta antes --, entao todo pulo dele e por falta
            # de preco, e e isso que distingue os dois ramos.
            if not any(r.reason == SKIPPED_NO_PRICE for r in self.results):
                lines.append(NO_CANDIDATES)
            return "\n".join(lines)
        if self.benchmark_missing:
            lines.append(BENCHMARK_WARNING)
        total = len(self.results)  # inclui os pulados, ao contrario do molde
        skipped = sum(1 for r in self.results if r.skipped)
        failed = sum(1 for r in self.results if r.error)
        ok = total - skipped - failed
        lines.append(
            f"metricas: {total} ativos, {ok} ok, {failed} falhos, "
            f"{skipped} pulados, {self.elapsed:.1f}s"
        )
        return "\n".join(lines)


class MetricsFailed(Exception):
    """Algum ativo falhou. `report` e o relatorio inteiro, para a casca imprimir."""

    def __init__(self, report: MetricsReport) -> None:
        super().__init__(", ".join(r.ticker for r in report.results if r.error))
        self.report = report


def run_compute_metrics(
    tickers: list[str], *, now: Callable[[], datetime] = timezone.now
) -> MetricsReport:
    """Calcula e grava as metricas dos ativos pedidos, um de cada vez.

    `calculated_at` e o `now()` de **uma** chamada, compartilhado por todos os ativos da
    execucao: e o que faz "uma execucao" ser identificavel em `gold.behavior_metric`.
    """
    assets, skipped = _resolve(tickers)  # InvalidTickers antes de qualquer escrita
    started = time.monotonic()
    calculated_at = now()
    # O acessor e contrato (spec, "Qual ativo e o Ibovespa"): com .get(), catalogo com dois
    # indices falha alto, e a mutacao que troca o criterio por `kind` levanta
    # MultipleObjectsReturned de forma deterministica -- ordenacao nao blinda nada, porque
    # .first() sem ordering aplica order_by("pk") e o IBOV da migration tem pk baixa.
    try:
        benchmark_asset: Asset | None = Asset.objects.get(ticker=IBOV_TICKER)
    except Asset.DoesNotExist:
        benchmark_asset = None  # RF-16: aviso, nunca erro
    # Indice sem nenhum preco e o mesmo que indice ausente (RF-16): a serie vazia vira
    # `None`, e nao lista vazia. `beta_and_correlation` so trata `None` como "sem indice";
    # com `[]` ela emparelharia contra nada e gravaria `benchmark_observations = 0`, que a
    # spec reserva para "nao ha com que comparar" -- e ali o contrato e nulo.
    benchmark_bars = (
        None if benchmark_asset is None else (_bars(benchmark_asset) or None)
    )
    benchmark_missing = benchmark_bars is None
    results = [_compute_asset(a, calculated_at, benchmark_bars) for a in assets]
    # Os pulados por `inativo` vao depois dos processados: e a ordem do exemplo da spec,
    # que traz os tres calculados e so entao o `BAZZ4 ... pulado: inativo`.
    results.extend(_skipped(a, SKIPPED_INACTIVE) for a in skipped)
    report = MetricsReport(
        results, time.monotonic() - started, benchmark_missing=benchmark_missing
    )
    if report.failed:
        raise MetricsFailed(report)
    return report


def _resolve(tickers: list[str]) -> tuple[list[Asset], list[Asset]]:
    """`(assets, skipped)`, os dois em ordem de ticker (RF-15).

    Com argumentos: deduplica, ordena, e qualquer ticker ausente ou nao-`active` aborta
    com `InvalidTickers`. **Nao filtra por preco**: o ativo `active` sem nenhuma linha em
    `silver.price` e devolvido como processavel, e quem o pula -- com motivo proprio -- e o
    guarda de serie vazia em `_compute_asset`.

    Sem argumentos: os ativos com preco; os `inactive` sao pulados, os `active` sao os
    pedidos. Ativo sem preco nenhum nao e candidato e **nao aparece** no relatorio.
    """
    if tickers:
        wanted = sorted(set(tickers))
        found = {a.ticker: a for a in Asset.objects.filter(ticker__in=wanted)}
        offenders = [
            t
            for t in wanted
            if t not in found or found[t].status != Asset.Status.ACTIVE
        ]
        if offenders:
            raise InvalidTickers(offenders)
        return [found[t] for t in wanted], []
    candidates = (
        Asset.objects.filter(prices__isnull=False).distinct().order_by("ticker")
    )
    assets = [a for a in candidates if a.status == Asset.Status.ACTIVE]
    skipped = [a for a in candidates if a.status != Asset.Status.ACTIVE]
    return assets, skipped


def _skipped(asset: Asset, reason: str) -> AssetResult:
    return AssetResult(asset.ticker, 0, None, [], None, True, reason)


def _bars(asset: Asset) -> list[Bar]:
    """A serie inteira do ativo, em ordem de data, no `Bar` de `metrics`."""
    return [
        Bar(
            date=p.date,
            close=p.close,
            adj_close=p.adj_close,
            volume=p.volume,
            log_return=p.log_return,
        )
        for p in Price.objects.filter(asset=asset).order_by("date")
    ]


def _dividends(asset: Asset) -> list[Dividend]:
    """Os dividendos do ativo, em ordem de data.

    `amount` nulo e descartado ao montar a lista: pagamento sem valor nao e pagamento que
    se possa somar, e o `Dividend` de `metrics` nao aceita `amount` anulavel.
    """
    events = CorporateEvent.objects.filter(
        asset=asset, kind=CorporateEvent.Kind.DIVIDEND
    ).order_by("date")
    return [
        Dividend(date=e.date, amount=e.amount) for e in events if e.amount is not None
    ]


def _compute_asset(
    asset: Asset, calculated_at: datetime, benchmark_bars: list[Bar] | None
) -> AssetResult:
    bars = _bars(asset)
    # Antes de calcular: serie vazia e pulo, com motivo proprio. Nunca linha em gold com
    # as_of_date nulo -- a coluna e NOT NULL, e "metrica de ativo sem preco" nao existe.
    if not bars:
        return _skipped(asset, SKIPPED_NO_PRICE)
    # O indice nao tem beta consigo mesmo (RF-08): entra sem benchmark, como qualquer ativo
    # num catalogo sem IBOV (RF-16). Os dois casos dao a mesma tripla nula, e quem os
    # distingue e o relatorio, nao o calculo.
    benchmark = None if asset.ticker == IBOV_TICKER else benchmark_bars
    try:
        metrics = compute(bars, _dividends(asset), benchmark)
        with transaction.atomic():  # a linha e os 42 baldes entram juntos (RF-04)
            write_metrics(asset, calculated_at, metrics)
    except Exception as exc:
        return AssetResult(
            asset.ticker,
            len(bars),
            bars[-1].date,
            [],
            f"{type(exc).__name__}: {exc}",
            False,
        )
    return AssetResult(
        asset.ticker,
        metrics.price_count,
        metrics.as_of_date,
        _null_columns(_column_values(metrics), with_benchmark=benchmark is not None),
        None,
        False,
    )


def _column_values(metrics: Metrics) -> dict[str, object]:
    """O desmonte de `Metrics` nas colunas de `gold.behavior_metric`.

    `returns` e `volatility` sao dicionarios de chave fechada; a queda vira cinco colunas.
    `as_of_date`, `first_price_date` e `price_count` ficam de fora: nao sao metrica e nunca
    sao nulos.
    """
    values: dict[str, object] = {
        f"return_{months}m": metrics.returns[f"{months}m"] for months in RETURN_WINDOWS
    }
    values["return_ytd"] = metrics.returns["ytd"]
    for months in VOLATILITY_WINDOWS:
        values[f"volatility_{months}m"] = metrics.volatility[f"{months}m"]
    drawdown = metrics.drawdown
    values["max_drawdown"] = drawdown.depth
    values["max_drawdown_peak_date"] = drawdown.peak_date
    values["max_drawdown_trough_date"] = drawdown.trough_date
    values["max_drawdown_recovery_date"] = drawdown.recovery_date
    values["max_drawdown_recovery_sessions"] = drawdown.recovery_sessions
    values["beta_60m"] = metrics.beta_60m
    values["correlation_60m"] = metrics.correlation_60m
    values["benchmark_observations"] = metrics.benchmark_observations
    values["skewness"] = metrics.skewness
    values["excess_kurtosis"] = metrics.excess_kurtosis
    values["statistical_observations"] = metrics.statistical_observations
    values["dividends_12m"] = metrics.dividends_12m
    values["dividend_payments_12m"] = metrics.dividend_payments_12m
    values["dividend_yield_12m"] = metrics.dividend_yield_12m
    values["avg_volume_21d"] = metrics.avg_volume_21d
    values["avg_volume_252d"] = metrics.avg_volume_252d
    return values


def _null_columns(values: dict[str, object], *, with_benchmark: bool) -> list[str]:
    """As colunas nulas **por falta de historico**, na ordem da tabela da spec."""
    return [
        column
        for column in NULLABLE_COLUMNS
        if values[column] is None
        and (with_benchmark or column not in BENCHMARK_COLUMNS)
    ]


def write_metrics(
    asset: Asset, calculated_at: datetime, metrics: Metrics
) -> BehaviorMetric:
    """A linha de metrica e os 42 baldes dela. Sempre `create`, nunca `update` (RF-02)."""
    metric = BehaviorMetric.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        as_of_date=metrics.as_of_date,
        first_price_date=metrics.first_price_date,
        price_count=metrics.price_count,
        **_column_values(metrics),
    )
    ReturnHistogramBin.objects.bulk_create(
        [
            ReturnHistogramBin(
                metric=metric,
                bin_index=b.index,
                lower_bound=b.lower,
                upper_bound=b.upper,
                count=b.count,
            )
            for b in metrics.histogram
        ]
    )
    return metric
