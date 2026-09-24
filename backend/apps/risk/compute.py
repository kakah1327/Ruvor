"""A orquestracao do risco: laco por ativo, transacao por ativo, escrita e relatorio.

O molde e `apps/analytics/compute.py`, do M1.3 -- selecao de ativos, `InvalidTickers`
antes de qualquer escrita, uma transacao por ativo e o relatorio com o resumo ao fim.

Quatro pontos em que este modulo diverge do molde, todos do plano:

- **o registry e carregado antes de ser consultado**: `list_models()` le um dicionario que
  so e populado por `load_all_model_modules()`, e o mesmo vale para os backtests, que o
  `run_experiment` resolve por `get_backtest`. Sem as duas chamadas toda execucao
  levantaria `ModelsMissing` com os nove;
- **o piso de `MIN_SESSIONS` pregoes**: ativo com serie curta e pulado e **nao grava linha
  nenhuma** -- execucao sem resultado nao e manifesto de coisa alguma (RF-10b);
- **a serie que manda e a que o motor ve**: o piso, o `price_count` e as datas saem das
  linhas que sobrevivem ao criterio do `clean_prices`, nao da contagem do banco;
- **`hyperparameters` vem de uma instancia nova**, `get_model(nome)().hyperparameters`,
  criada fora do `runner`: e leitura pura, e acrescentar o campo ao `ModelRunResult` seria
  uma quinta alteracao num motor que autoriza quatro e que a D-21 congela.

`write_risk` e chamada pelo nome global, como `write_metrics` no M1.3: e o ponto que o
teste da transacao por ativo substitui com `monkeypatch.setattr`.

`gold.risk_run` e `gold.risk_result` sao so-acrescimo (D-16, RF-11): nenhum caminho daqui
faz `update` ou `delete`. Recalcular insere execucao nova.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from importlib.metadata import version
from typing import Any

from django.db import transaction
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.backtesting.base import BacktestResult
from engine.experiments.runner import (
    ExperimentConfig,
    ExperimentResult,
    ModelRunResult,
    run_experiment,
)
from engine.models import get_model, list_models, load_all_model_modules

from apps.assets.models import Asset, Price
from apps.risk import config
from apps.risk.models import RiskResult, RiskRun
from apps.risk.provider import SilverPriceProvider

# Os nove modelos, escritos literalmente porque o RF-17 compara o **pedido** com o
# registry: um padrao que dissesse `list_models()` compararia o registry consigo mesmo, e
# a denuncia de registry incompleto nunca dispararia. A lista e a mesma que
# `list_models()` devolve num ambiente completo, e o teste confere uma contra a outra.
MODELS: tuple[str, ...] = (
    "caviar",
    "egarch",
    "garch_1_1",
    "garchnet",
    "gru",
    "historical",
    "lstm",
    "monte_carlo",
    "parametric",
)

#: o nome da distribuicao instalada, de onde sai o `engine_version` do manifesto
DISTRIBUTION_NAME = "ruvor-engine"

Q4 = Decimal("0.0001")
Q6 = Decimal("0.000001")
Q10 = Decimal("0.0000000001")

NO_CANDIDATES = "nenhum ativo ativo com preco; informe tickers"

SKIPPED_INACTIVE = "inativo"
SKIPPED_SHORT_SERIES = f"serie curta (minimo {config.MIN_SESSIONS})"


class InvalidTickers(Exception):
    """Ticker desconhecido ou inativo pedido por argumento (RF-18). Nada foi escrito."""

    def __init__(self, tickers: list[str]) -> None:
        super().__init__(", ".join(tickers))
        self.tickers = tickers


class ModelsMissing(Exception):
    """Modelo pedido que o registry nao oferece (RF-17). Nada foi escrito.

    Com os nove por padrao e o registry incompleto que ele denuncia; com `--model`, o nome
    errado. E o oposto do `except ImportError: continue` do motor, adequado para uma
    biblioteca e inaceitavel para uma execucao que se diz completa.
    """

    def __init__(self, models: list[str]) -> None:
        super().__init__(", ".join(models))
        self.models = models


@dataclass(frozen=True)
class AssetResult:
    """Uma linha do relatorio: o que aconteceu com um ativo.

    `price_count` e `as_of_date` descrevem a serie que o motor **viu** -- a de depois do
    criterio do `clean_prices`. No pulado por `inativo` sao `0` e `None`, porque a serie
    nao chegou a ser lida; no pulado por serie curta sao os da serie lida, que e o que
    explica o pulo.
    """

    ticker: str
    price_count: int
    as_of_date: date | None
    results: int
    adequate: int
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
                f"{self.results} resultados, {self.adequate} adequados, "
                f"{self.failed} falhos  {self.elapsed:.1f}s"
            )
        return f"{self.ticker:<12}{self.price_count:>8} pregoes  {quando:<14}  {cauda}"


@dataclass(frozen=True)
class RiskReport:
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
            # "informe tickers" so sai a quem nao informou nenhum: quem informou nao tem
            # pulo por `inativo` -- `_resolve` aborta antes --, entao todo pulo dele e por
            # serie curta, e e isso que distingue os dois ramos.
            if not any(r.reason == SKIPPED_SHORT_SERIES for r in self.results):
                lines.append(NO_CANDIDATES)
            return "\n".join(lines)
        total = len(self.results)  # inclui os pulados, como no M1.3
        skipped = sum(1 for r in self.results if r.skipped)
        failed = sum(1 for r in self.results if r.error)
        ok = total - skipped - failed
        lines.append(
            f"risco: {total} ativos, {ok} ok, {failed} falhos, "
            f"{skipped} pulados, {self.elapsed:.1f}s"
        )
        return "\n".join(lines)


class RiskFailed(Exception):
    """Algum ativo falhou. `report` e o relatorio inteiro, para a casca imprimir."""

    def __init__(self, report: RiskReport) -> None:
        super().__init__(", ".join(r.ticker for r in report.results if r.error))
        self.report = report


def run_compute_risk(
    tickers: list[str],
    *,
    seed: int | None = None,
    models: list[str] | None = None,
    now: Callable[[], datetime] = timezone.now,
) -> RiskReport:
    """Calcula e grava o risco dos ativos pedidos, um de cada vez.

    `calculated_at` e o `now()` de **uma** chamada, compartilhado por todos os ativos da
    execucao: e o que faz "uma execucao" ser identificavel em `gold.risk_run`.
    """
    # Carregar antes de consultar: `list_models()` le o dicionario que estas duas
    # populam, e o `run_experiment` resolve os backtests por `get_backtest`.
    load_all_model_modules()
    load_all_backtest_modules()
    requested = list(MODELS) if models is None else list(models)
    missing = [m for m in requested if m not in list_models()]
    if missing:
        raise ModelsMissing(missing)  # falha alto, antes de qualquer escrita (RF-17)

    assets, skipped = _resolve(tickers)  # InvalidTickers antes de qualquer escrita
    effective_seed = config.DEFAULT_SEED if seed is None else seed
    started = time.monotonic()
    calculated_at = now()
    results = [
        _compute_asset(asset, calculated_at, effective_seed, requested, now)
        for asset in assets
    ]
    # Os pulados por `inativo` vao depois dos processados, como no M1.3.
    results.extend(_skipped(a, SKIPPED_INACTIVE) for a in skipped)
    report = RiskReport(results, time.monotonic() - started)
    if report.failed:
        raise RiskFailed(report)
    return report


def _resolve(tickers: list[str]) -> tuple[list[Asset], list[Asset]]:
    """`(assets, skipped)`, os dois em ordem de ticker (RF-18).

    Com argumentos: deduplica, ordena, e qualquer ticker ausente ou nao-`active` aborta
    com `InvalidTickers`. **Nao filtra por preco**: quem pula o ativo de serie curta --
    ou sem serie nenhuma -- e o piso de `MIN_SESSIONS`, com motivo proprio.

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


def _bars(asset: Asset) -> list[Price]:
    """As linhas de `silver.price` que o motor vai ver, em ordem de data.

    O filtro e o criterio do `clean_prices` do motor -- nao nulo e maior que zero --
    aplicado sobre a coluna que o provedor entrega como `close`, que e o **`adj_close`**.
    Medir o piso, as datas e o `price_count` sobre esta lista elimina por construcao a
    divergencia entre o que o banco tem e o que o motor calculou.
    """
    return [
        p
        for p in Price.objects.filter(asset=asset).order_by("date")
        if p.adj_close is not None and p.adj_close > 0
    ]


def _compute_asset(
    asset: Asset,
    calculated_at: datetime,
    seed: int,
    models: list[str],
    now: Callable[[], datetime],
) -> AssetResult:
    bars = _bars(asset)
    # O piso do RF-10b, medido sobre a serie depois da limpeza. Abaixo dele a Basileia
    # levantaria em todos os resultados -- ou o proprio `run_experiment` levantaria --, e
    # execucao sem resultado nao e manifesto de coisa alguma: nada e gravado.
    if len(bars) < config.MIN_SESSIONS:
        return _skipped(
            asset,
            SKIPPED_SHORT_SERIES,
            price_count=len(bars),
            as_of_date=bars[-1].date if bars else None,
        )
    started = time.monotonic()
    experiment = ExperimentConfig(
        ticker=asset.ticker,
        # A janela inteira da serie, em ISO, com as duas bordas inclusivas: e o intervalo
        # que o `SilverPriceProvider` implementa.
        start=bars[0].date.isoformat(),
        end=bars[-1].date.isoformat(),
        model_names=list(models),
        backtest_names=list(config.BACKTESTS),
        alphas=list(config.ALPHAS),
        train_window_days=config.TRAIN_WINDOW_DAYS,
        seed=seed,
    )
    try:
        result = run_experiment(experiment, SilverPriceProvider())
        finished_at = now()
        with transaction.atomic():  # a execucao e os resultados entram juntos (RF-12)
            write_risk(asset, calculated_at, finished_at, seed, bars, result)
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
    return AssetResult(
        asset.ticker,
        len(bars),
        bars[-1].date,
        len(result.runs),
        sum(1 for r in result.runs if _verdict(r) is True),
        sum(1 for r in result.runs if r.error),
        time.monotonic() - started,
        None,
        False,
    )


def _backtest(model_run: ModelRunResult, name: str) -> BacktestResult | None:
    for backtest in model_run.backtests:
        if backtest.test_name == name:
            return backtest
    return None


def _verdict(model_run: ModelRunResult) -> bool | None:
    """O veredito, literal: Kupiec **e** Christoffersen, nulo quando houve erro (RF-13).

    DQ e Basileia sao gravados e **nao entram** (RF-14).
    """
    error = model_run.error or ""
    kupiec = _backtest(model_run, "kupiec")
    christoffersen = _backtest(model_run, "christoffersen")
    kupiec_passed = None if kupiec is None else kupiec.passed
    christoffersen_passed = None if christoffersen is None else christoffersen.passed
    return None if error else (kupiec_passed and christoffersen_passed)


def _decimal(value: float | None, quantum: Decimal) -> Decimal | None:
    return None if value is None else Decimal(str(float(value))).quantize(quantum)


def _row(run: RiskRun, model_run: ModelRunResult) -> RiskResult:
    """Uma linha de `gold.risk_result`, a partir do `ModelRunResult`.

    Quando `error` nao e vazio, **todas as colunas de numero sao nulas** (RF-10, V-12): e
    assim que se distingue "o modelo falhou" de "o modelo rodou e foi reprovado".

    `violations` e `expected_violations` sao os do **Kupiec**, que conta o periodo de
    teste inteiro -- os da Basileia sao outros numeros, sobre os ultimos 250 pregoes, e a
    leitura regulatoria fica em `basel_zone`.
    """
    error = model_run.error or ""
    failed = bool(error)
    kupiec = None if failed else _backtest(model_run, "kupiec")
    christoffersen = None if failed else _backtest(model_run, "christoffersen")
    dq = None if failed else _backtest(model_run, "dq")
    basileia = None if failed else _backtest(model_run, "basileia")
    estimate = None if failed else model_run.estimate
    details: dict[str, Any] = {} if kupiec is None else kupiec.details
    return RiskResult(
        run=run,
        model_name=model_run.model_name,
        model_category=get_model(model_run.model_name).category.value,
        # Float no motor, Decimal na coluna. O `str` e obrigatorio: `Decimal(0.05)` nao e
        # `0.0500`.
        alpha=Decimal(str(model_run.alpha)).quantize(Q4),
        # Instancia nova, criada fora do runner: leitura pura, e todos os nove
        # construtores tem padrao para tudo.
        hyperparameters=get_model(model_run.model_name)().hyperparameters,
        var_latest=(
            None if estimate is None else _decimal(estimate.var_series.iloc[-1], Q10)
        ),
        var_mean=(
            None if estimate is None else _decimal(estimate.var_series.mean(), Q10)
        ),
        violations=details.get("violations"),
        expected_violations=_decimal(details.get("expected"), Q6),
        kupiec_passed=None if kupiec is None else kupiec.passed,
        kupiec_p_value=None if kupiec is None else _decimal(kupiec.p_value, Q10),
        christoffersen_passed=(
            None if christoffersen is None else christoffersen.passed
        ),
        christoffersen_p_value=(
            None if christoffersen is None else _decimal(christoffersen.p_value, Q10)
        ),
        dq_passed=None if dq is None else dq.passed,
        dq_p_value=None if dq is None else _decimal(dq.p_value, Q10),
        basel_zone=None if basileia is None else basileia.details.get("zone"),
        adequate=_verdict(model_run),
        error=error,
    )


def write_risk(
    asset: Asset,
    calculated_at: datetime,
    finished_at: datetime,
    seed: int,
    bars: Sequence[Price],
    result: ExperimentResult,
) -> RiskRun:
    """A execucao e os resultados dela. Sempre `create`, nunca `update` (RF-11).

    `bars` sao as linhas de `silver.price` que sobreviveram ao criterio do `clean_prices`
    -- dai saem as datas, as contagens e o `price_run`.
    """
    train_window_days = result.config.train_window_days
    # `log_returns` descarta o primeiro pregao: P precos dao P-1 retornos, e o que sobra
    # depois da janela de treino e o periodo de teste.
    test_count = len(bars) - 1 - train_window_days
    run = RiskRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=finished_at,
        engine_version=version(DISTRIBUTION_NAME),
        seed=seed,
        train_window_days=train_window_days,
        as_of_date=bars[-1].date,
        first_price_date=bars[0].date,
        price_count=len(bars),
        train_count=train_window_days,
        test_count=test_count,
        # O **maior** `run` entre as linhas usadas, nao o `run` da linha de maior data:
        # `Price.run` so avanca quando a linha nasce ou muda de valor, e o que interessa a
        # auditoria e qual foi a coleta mais recente que tocou a janela.
        price_run_id=max(bar.run_id for bar in bars),
        # Sempre nula: nao ha usuario autenticado antes do M2.1, e a D-15 fica cumprida
        # pela metade, declaradamente.
        requested_by=None,
    )
    RiskResult.objects.bulk_create([_row(run, model_run) for model_run in result.runs])
    return run
