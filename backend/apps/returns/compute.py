"""O calculo do retorno (M5.1, RF-09 a RF-11): laco por ativo, transacao por ativo, escrita e
relatorio, no molde de `apps/risk/compute.py`.

Reaproveita do risco, pelo import: `_resolve` (o conjunto do `recalcular_cobertos`, com o
`InvalidTickers` dele, antes de qualquer escrita), `_bars` (o filtro do `clean_prices`
sobre o `adj_close`), `Q10` e a regra do `price_run` (`max(bar.run_id for bar in bars)`).
O piso e `apps.risk.config.MIN_SESSIONS`, e a janela de treino e
`apps.risk.config.TRAIN_WINDOW_DAYS`: uma fonte so.

- **o registry de retorno e carregado antes de ser consultado**, e a lista e
  `RETURN_MODELS`, literal: modelo pedido que o registry nao oferece levanta
  `ReturnModelsMissing` antes de qualquer escrita (D-66);
- **abaixo de `MIN_SESSIONS`, o ativo e pulado e nada e gravado**;
- **uma transacao por ativo**: `write_returns` -- chamada pelo nome global, o ponto que os
  testes substituem -- cria a `return_run` e os dois `return_result` juntos;
- **quantiza primeiro, decide depois** (RF-09): o veredito compara com `SIGNIFICANCE` o
  mesmo `Decimal` de 10 casas que vai a coluna, nunca o `float` cru;
- a data da previsao e `next_weekday(as_of_date)`, sem calendario de feriados (RF-03a).

Nenhum `return_result` e alterado nem apagado (D-16): so `create`.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from importlib.metadata import version

from django.db import transaction
from django.utils import timezone
from engine.returns import (
    ReturnExperimentConfig,
    ReturnExperimentResult,
    ReturnModelResult,
    get_return_model,
    list_return_models,
    load_all_return_model_modules,
    run_return_experiment,
)

from apps.accounts.models import User
from apps.assets.models import Asset, Price
from apps.returns.config import RETURN_MODELS, SIGNIFICANCE
from apps.returns.models import ReturnResult, ReturnRun
from apps.risk import config as risk_config
from apps.risk.compute import Q10, InvalidTickers, _bars, _resolve
from apps.risk.provider import SilverPriceProvider

__all__ = [
    "InvalidTickers",
    "ReturnModelsMissing",
    "ReturnsFailed",
    "ReturnsReport",
    "next_weekday",
    "run_compute_returns",
    "write_returns",
]

#: o nome da distribuicao instalada, de onde sai o `engine_version` do manifesto
DISTRIBUTION_NAME = "ruvor-engine"

NO_CANDIDATES = "nenhum ativo ativo com preco; informe tickers"
SKIPPED_INACTIVE = "inativo"
SKIPPED_SHORT_SERIES = f"serie curta (minimo {risk_config.MIN_SESSIONS})"


class ReturnModelsMissing(Exception):
    """Modelo de `RETURN_MODELS` que o registry nao oferece (D-66). Nada foi escrito."""

    def __init__(self, models: list[str]) -> None:
        super().__init__(", ".join(models))
        self.models = models


@dataclass(frozen=True)
class AssetResult:
    """Uma linha do relatorio: o que aconteceu com um ativo."""

    ticker: str
    price_count: int
    as_of_date: date | None
    results: int
    beats: int
    failed: int
    elapsed: float | None
    error: str | None
    skipped: bool
    reason: str = ""

    def render(self) -> str:
        quando = "-" if self.as_of_date is None else f"ate {self.as_of_date}"
        if self.skipped:
            cauda = f"pulado: {self.reason}"
        elif self.error is not None:
            cauda = f"FALHOU ({self.error})"
        else:
            cauda = (
                f"{self.results} modelos, {self.beats} batem a referencia, "
                f"{self.failed} falhos  {self.elapsed:.1f}s"
            )
        return f"{self.ticker:<12}{self.price_count:>8} pregoes  {quando:<14}  {cauda}"


@dataclass(frozen=True)
class ReturnsReport:
    """O relatorio de uma execucao: uma linha por ativo e o resumo."""

    results: list[AssetResult]
    elapsed: float

    @property
    def failed(self) -> bool:
        return any(r.error for r in self.results)

    def render(self) -> str:
        lines = [r.render() for r in self.results]
        processed = [r for r in self.results if not r.skipped]
        if not processed:
            if not any(r.reason == SKIPPED_SHORT_SERIES for r in self.results):
                lines.append(NO_CANDIDATES)
            return "\n".join(lines)
        total = len(self.results)
        skipped = sum(1 for r in self.results if r.skipped)
        failed = sum(1 for r in self.results if r.error)
        ok = total - skipped - failed
        lines.append(
            f"retorno: {total} ativos, {ok} ok, {failed} falhos, "
            f"{skipped} pulados, {self.elapsed:.1f}s"
        )
        return "\n".join(lines)


class ReturnsFailed(Exception):
    """Algum ativo falhou. `report` e o relatorio inteiro, para a casca imprimir."""

    def __init__(self, report: ReturnsReport) -> None:
        super().__init__(", ".join(r.ticker for r in report.results if r.error))
        self.report = report


def next_weekday(d: date) -> date:
    # sexta -> segunda, sabado -> segunda, demais -> +1
    step = {4: 3, 5: 2}.get(d.weekday(), 1)
    return d + timedelta(days=step)


def run_compute_returns(
    tickers: list[str],
    *,
    requested_by: User | None = None,
    now: Callable[[], datetime] = timezone.now,
) -> ReturnsReport:
    """Calcula e grava a validacao e a previsao dos ativos pedidos, um de cada vez.

    `calculated_at` e o `now()` de **uma** chamada, comum a todos os ativos dela.
    """
    load_all_return_model_modules()  # carregar antes de consultar
    available = list_return_models()
    missing = [m for m in RETURN_MODELS if m not in available]
    if missing:
        raise ReturnModelsMissing(missing)  # falha alto, antes de qualquer escrita

    assets, skipped = _resolve(tickers)  # InvalidTickers antes de qualquer escrita
    started = time.monotonic()
    calculated_at = now()
    results = [
        _compute_asset(asset, calculated_at, requested_by, now) for asset in assets
    ]
    results.extend(_skipped(a, SKIPPED_INACTIVE) for a in skipped)
    report = ReturnsReport(results, time.monotonic() - started)
    if report.failed:
        raise ReturnsFailed(report)
    return report


def _skipped(
    asset: Asset,
    reason: str,
    *,
    price_count: int = 0,
    as_of_date: date | None = None,
) -> AssetResult:
    return AssetResult(
        asset.ticker, price_count, as_of_date, 0, 0, 0, None, None, True, reason
    )


def _compute_asset(
    asset: Asset,
    calculated_at: datetime,
    requested_by: User | None,
    now: Callable[[], datetime],
) -> AssetResult:
    bars = _bars(asset)
    if len(bars) < risk_config.MIN_SESSIONS:
        return _skipped(
            asset,
            SKIPPED_SHORT_SERIES,
            price_count=len(bars),
            as_of_date=bars[-1].date if bars else None,
        )
    started = time.monotonic()
    try:
        experiment = ReturnExperimentConfig(
            ticker=asset.ticker,
            # a janela inteira, as duas bordas inclusivas: o intervalo do provedor
            start=bars[0].date.isoformat(),
            end=bars[-1].date.isoformat(),
            model_names=list(RETURN_MODELS),
            train_window_days=risk_config.TRAIN_WINDOW_DAYS,
        )
        result = run_return_experiment(experiment, SilverPriceProvider())
        finished_at = now()
        with transaction.atomic():  # a execucao e os dois resultados entram juntos
            write_returns(
                asset,
                calculated_at,
                finished_at,
                bars,
                result,
                requested_by=requested_by,
            )
    except Exception as exc:
        return AssetResult(
            asset.ticker,
            len(bars),
            bars[-1].date,
            0,
            0,
            0,
            time.monotonic() - started,
            f"{type(exc).__name__}: {exc}",
            False,
        )
    as_of_date = bars[-1].date
    rows = [_fields(run, as_of_date) for run in result.runs]
    return AssetResult(
        asset.ticker,
        len(bars),
        as_of_date,
        len(result.runs),
        sum(1 for row in rows if row["beats_reference"] is True),
        sum(1 for run in result.runs if run.error),
        time.monotonic() - started,
        None,
        False,
    )


def _q(x: float | None) -> Decimal | None:
    """O `float` do motor em `Decimal` de 10 casas. `str(float(x))`, como o `_decimal` do
    risco: um `np.float64` passa por `float` primeiro -- o `repr` dele, no numpy 2, e
    `np.float64(...)`, que o `Decimal` recusa (revisao de implementacao da T3)."""
    if x is None:
        return None
    return Decimal(str(float(x))).quantize(Q10, rounding=ROUND_HALF_EVEN)


def _fields(run: ReturnModelResult, as_of_date: date) -> dict[str, object]:
    """As colunas de numero, o veredito e a previsao de um resultado (RF-09, RF-10).

    Com `error`, toda coluna de numero, a data e os dois booleanos ficam nulos.
    """
    error = run.error or ""
    ev = None if error else run.evaluation
    if ev is None:
        # sem avaliacao nao ha o que gravar: o resultado e de falha
        error = error or "sem avaliacao"
        return {
            "mse": None,
            "mse_reference": None,
            "r2_os": None,
            "direction_days": None,
            "hit_rate": None,
            "up_share": None,
            "forecast_up_share": None,
            "dm_statistic": None,
            "dm_p_value": None,
            "cw_statistic": None,
            "cw_p_value": None,
            "pt_statistic": None,
            "pt_p_value": None,
            "beats_reference": None,
            "direction_skill": None,
            "next_forecast": None,
            "next_forecast_date": None,
            "error": error,
        }
    # quantiza primeiro, decide depois: o veredito ve o mesmo Decimal que vai a coluna
    dm_p = _q(ev.dm_p_value)
    pt_p = _q(ev.pt_p_value)
    beats_reference = None if error else (dm_p is not None and dm_p < SIGNIFICANCE)
    direction_skill = None if (error or pt_p is None) else pt_p < SIGNIFICANCE
    next_forecast = _q(run.next_value)
    next_forecast_date = next_weekday(as_of_date)
    return {
        "mse": _q(ev.mse),
        "mse_reference": _q(ev.mse_reference),
        "r2_os": _q(ev.r2_os),
        "direction_days": ev.direction_days,
        "hit_rate": _q(ev.hit_rate),
        "up_share": _q(ev.up_share),
        "forecast_up_share": _q(ev.forecast_up_share),
        "dm_statistic": _q(ev.dm_statistic),
        "dm_p_value": dm_p,
        "cw_statistic": _q(ev.cw_statistic),
        "cw_p_value": _q(ev.cw_p_value),
        "pt_statistic": _q(ev.pt_statistic),
        "pt_p_value": pt_p,
        "beats_reference": beats_reference,
        "direction_skill": direction_skill,
        "next_forecast": next_forecast,
        "next_forecast_date": next_forecast_date,
        "error": "",
    }


def write_returns(
    asset: Asset,
    calculated_at: datetime,
    finished_at: datetime,
    bars: Sequence[Price],
    result: ReturnExperimentResult,
    *,
    requested_by: User | None = None,
) -> ReturnRun:
    """A execucao e os resultados dela. Sempre `create` (D-16).

    `bars` sao as linhas de `silver.price` que sobreviveram ao criterio do `clean_prices`
    -- dai saem as datas, as contagens e o `price_run`. Quem chama abre a transacao.
    """
    train_window_days = risk_config.TRAIN_WINDOW_DAYS
    run = ReturnRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=finished_at,
        engine_version=version(DISTRIBUTION_NAME),
        train_window_days=train_window_days,
        as_of_date=bars[-1].date,
        first_price_date=bars[0].date,
        price_count=len(bars),
        train_count=train_window_days,
        # `log_returns` descarta o primeiro pregao: P precos dao P - 1 retornos
        test_count=len(bars) - 1 - train_window_days,
        # o **maior** `run` entre as linhas usadas: a coleta mais recente que tocou a janela
        price_run_id=max(bar.run_id for bar in bars),
        requested_by=requested_by,
    )
    for model_run in result.runs:
        ReturnResult.objects.create(
            run=run,
            model_name=model_run.model_name,
            # instancia nova, leitura pura
            hyperparameters=get_return_model(model_run.model_name)().hyperparameters,
            **_fields(model_run, run.as_of_date),
        )
    return run
