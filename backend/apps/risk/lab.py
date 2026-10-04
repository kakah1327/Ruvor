"""O experimento fixo da decada de um ativo (M2.4, RF-01, RF-03, RF-04, RF-07, RF-08, RF-10).

Os nove modelos nos dois niveis, pelo **mesmo** `run_models` da producao (`apps/risk/compute.py`),
sobre a serie da decada (`apps/risk/decade.py`) -- com os retratos, que ele le e grava como na
producao --, recortados em trechos de 252 retornos e guardados uma vez por identidade em
`gold.lab_run`, `gold.lab_result` e `gold.lab_year`.

**Este modulo importa o motor**: roda no `worker`. A `web` nunca o importa (a rota le
`apps/risk/models.py` e `apps/risk/decade.py`; `tests/api/test_sem_motor.py` o proibe).

- **os anos** (`split_years`): o periodo de teste e o do `runner` -- `fetch_returns` sobre a serie,
  `iloc[252:]` e o `reindex(var_series.index).dropna()` (`engine/src/engine/experiments/runner.py`)
  --, cortado em trechos de `LAB_YEAR_DAYS` a partir da posicao 0. So os niveis de
  `LAB_JUDGED_ALPHAS` (95%) e so os trechos com pelo menos `LAB_YEAR_MIN_JUDGED` retornos levam o
  Kupiec, o Christoffersen e o veredito (o par da D-64); os outros, nulos;
- **a soma**: as violacoes dos trechos somam as da decada (o Kupiec do `ModelRunResult`); se nao,
  `LabSumMismatch`, e o experimento inteiro vira um `lab_run` `failed`, sem resultado nenhum;
- **a identidade** (`identity_for`) e o **devido** (`lab_due`): so um `ok` da identidade de agora
  tira o devido -- `partial` e `failed` nao (opcao (a) do RF-07);
- **a escrita** (`write_lab`): numa transacao, sob a trava do ativo (`lock_asset`, a mesma da
  abertura e do fecho do risco), segurada **so** ali; dentro dela, relida a existencia de um `ok`
  da identidade -- havendo, nada e gravado.

A zona de Basileia nao e gravada (RF-08); o DQ, so na decada.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from importlib.metadata import version
from typing import Any

import pandas as pd
from django.db import IntegrityError, transaction
from django.utils import timezone
from engine.backtesting import get_backtest, load_all_backtest_modules
from engine.backtesting.base import BacktestResult
from engine.data.preprocessing import fetch_returns
from engine.experiments.runner import ExperimentResult, ModelRunResult
from engine.models import get_model, list_models, load_all_model_modules

from apps.api.ondemand import lock_asset
from apps.assets.models import Asset
from apps.risk import config
from apps.risk.compute import (
    DISTRIBUTION_NAME,
    EXPENSIVE,
    MODELS,
    Q4,
    Q6,
    Q10,
    ModelsMissing,
    SnapshotCounts,
    _backtest,
    _decimal,
    _manifest,
    _verdict,
    run_models,
    status_for,
)
from apps.risk.decade import Decade, decade_of, valid_bars
from apps.risk.models import LabResult, LabRun, LabYear
from apps.risk.provider import SilverPriceProvider
from apps.risk.snapshots import (
    SnapshotKey,
    canonical_hash,
    library_versions,
    price_fingerprint,
)

#: o nome da restricao unica parcial do RF-07; o `IntegrityError` dela e "ja calculado"
IDENTITY_CONSTRAINT = "lab_run_identity_ok"

#: o `error` do `failed` cuja serie mudou entre a leitura e o fim do calculo (revisao de
#: implementacao, M1): o proximo fecho refaz, sobre a serie nova
SERIES_CHANGED = "série mudou durante o cálculo"


class LabSumMismatch(Exception):
    """A soma das violacoes dos trechos nao e a da decada num (modelo, nivel) (RF-03)."""

    def __init__(
        self, model_name: str, alpha: float, years_sum: int, decade: int | None
    ) -> None:
        super().__init__(
            f"soma das violacoes dos anos diverge da decada em {model_name} a {alpha}: "
            f"anos {years_sum}, decada {decade}"
        )
        self.model_name = model_name
        self.alpha = alpha
        self.years_sum = years_sum
        self.decade = decade


# --- os anos de teste (RF-03) --------------------------------------------------------------


@dataclass(frozen=True)
class YearSlice:
    """Um trecho do periodo de teste de um (modelo, nivel). Sem testes quando nao julgado."""

    index: int
    start_date: date
    end_date: date
    test_count: int
    violations: int
    expected: float
    kupiec: BacktestResult | None
    christoffersen: BacktestResult | None

    @property
    def adequate(self) -> bool | None:
        """O veredito da D-64, Kupiec **e** Christoffersen; nulo no trecho nao julgado."""
        if self.kupiec is None or self.christoffersen is None:
            return None
        return self.kupiec.passed and self.christoffersen.passed


def split_years(
    test: pd.Series, var_series: pd.Series, alpha: float
) -> list[YearSlice]:
    """Os trechos de `LAB_YEAR_DAYS` retornos, a partir da posicao 0, do teste alinhado ao VaR.

    `test` e o periodo de teste do `runner` (os retornos depois da janela de treino); o
    alinhamento e o dele, literal. `alpha` e o `float` de `config.ALPHAS`, comparado com
    `LAB_JUDGED_ALPHAS` por igualdade exata.
    """
    aligned = test.reindex(var_series.index).dropna()  # runner.py, literal
    var = var_series.reindex(aligned.index)
    judged_level = alpha in config.LAB_JUDGED_ALPHAS
    slices: list[YearSlice] = []
    for index, start in enumerate(range(0, len(aligned), config.LAB_YEAR_DAYS)):
        r = aligned.iloc[start : start + config.LAB_YEAR_DAYS]
        v = var.iloc[start : start + config.LAB_YEAR_DAYS]
        violations = int((r < -v).sum())
        judged = judged_level and len(r) >= config.LAB_YEAR_MIN_JUDGED
        kupiec = get_backtest("kupiec")().run(r, v, alpha) if judged else None
        christoffersen = (
            get_backtest("christoffersen")().run(r, v, alpha) if judged else None
        )
        slices.append(
            YearSlice(
                index=index,
                start_date=r.index[0].date(),
                end_date=r.index[-1].date(),
                test_count=len(r),
                violations=violations,
                expected=len(r) * alpha,
                kupiec=kupiec,
                christoffersen=christoffersen,
            )
        )
    return slices


def years_by_result(
    result: ExperimentResult, test: pd.Series
) -> dict[tuple[str, float], list[YearSlice]]:
    """Os trechos de cada (modelo, nivel) sem erro, com a soma conferida (RF-03).

    Qualquer (modelo, nivel) com a soma diferente das violacoes do Kupiec da decada levanta
    `LabSumMismatch` -- um corte desalinhado num modelo poe em duvida o corte de todos.
    """
    years: dict[tuple[str, float], list[YearSlice]] = {}
    for model_run in result.runs:
        if model_run.error or model_run.estimate is None:
            continue
        slices = split_years(test, model_run.estimate.var_series, model_run.alpha)
        kupiec = _backtest(model_run, "kupiec")
        decade_violations = None if kupiec is None else kupiec.details.get("violations")
        years_sum = sum(s.violations for s in slices)
        if years_sum != decade_violations:
            raise LabSumMismatch(
                model_run.model_name, model_run.alpha, years_sum, decade_violations
            )
        years[(model_run.model_name, model_run.alpha)] = slices
    return years


def period_of_test(asset: Asset, decade: Decade) -> pd.Series:
    """O periodo de teste da decada, pela mesma chamada do `runner`; uma vez por experimento."""
    series = decade.series
    returns = fetch_returns(
        SilverPriceProvider(),
        asset.ticker,
        series[0].date.isoformat(),
        series[-1].date.isoformat(),
    )
    return returns.iloc[config.TRAIN_WINDOW_DAYS :]


# --- a identidade e o devido (RF-07, RF-09) ------------------------------------------------


@dataclass(frozen=True)
class LabIdentity:
    """A identidade do experimento (RF-07): os sete campos da restricao `lab_run_identity_ok`."""

    asset_id: int
    engine_version: str
    seed: int
    train_window_days: int
    first_price_date: date
    decade_end: date
    library_versions: dict[str, str]
    library_versions_hash: str

    def fields(self) -> dict[str, Any]:
        """Os sete campos, no formato do `filter` de `LabRun`."""
        return {
            "asset_id": self.asset_id,
            "engine_version": self.engine_version,
            "seed": self.seed,
            "train_window_days": self.train_window_days,
            "first_price_date": self.first_price_date,
            "decade_end": self.decade_end,
            "library_versions_hash": self.library_versions_hash,
        }


def identity_for(asset: Asset, decade: Decade) -> LabIdentity:
    """A identidade de agora: a versao do motor e as das bibliotecas, lidas no processo."""
    versions = library_versions()
    return LabIdentity(
        asset_id=asset.pk,
        engine_version=version(DISTRIBUTION_NAME),
        seed=config.DEFAULT_SEED,
        train_window_days=config.TRAIN_WINDOW_DAYS,
        first_price_date=decade.first_price_date,
        decade_end=decade.end_date,
        library_versions=versions,
        library_versions_hash=canonical_hash(versions),
    )


@dataclass(frozen=True)
class LabOutcome:
    """O desfecho de `run_lab`: gravado, ou pulado com o motivo (`kind`).

    `run` so no gravado (o `lab_run`, de qualquer `status`); `decade` nos pulados por decada
    incompleta (a data em que completa e `decade.end_date`) e por serie curta.
    """

    WRITTEN = "written"
    ALREADY = "already"  # ha `ok` da identidade de agora: nada gravado
    INACTIVE = "inactive"
    NO_PRICES = "no_prices"
    INCOMPLETE = "incomplete"
    SHORT = "short"

    kind: str
    run: LabRun | None = None
    decade: Decade | None = None
    elapsed: float = 0.0

    @property
    def skipped(self) -> bool:
        return self.kind != self.WRITTEN


def _due(asset: Asset) -> tuple[LabIdentity, Decade] | LabOutcome:
    if asset.status != Asset.Status.ACTIVE:
        return LabOutcome(LabOutcome.INACTIVE)
    decade = decade_of(valid_bars(asset))
    if decade is None:
        return LabOutcome(LabOutcome.NO_PRICES)
    if not decade.complete:
        return LabOutcome(LabOutcome.INCOMPLETE, decade=decade)
    if not decade.sufficient:
        return LabOutcome(LabOutcome.SHORT, decade=decade)
    ident = identity_for(asset, decade)
    # So `ok` conta (opcao (a) do RF-07): `partial` e `failed` nao tiram o devido.
    if LabRun.objects.filter(status=LabRun.Status.OK, **ident.fields()).exists():
        return LabOutcome(LabOutcome.ALREADY, decade=decade)
    return ident, decade


def lab_due(asset: Asset) -> tuple[LabIdentity, Decade] | None:
    """A identidade e a decada do experimento devido; `None` se nao ha experimento devido.

    `None`: o ativo nao `active`; sem pregao valido; a decada incompleta ou curta; ou um
    `lab_run` `ok` com os sete campos da identidade de agora.
    """
    due = _due(asset)
    return None if isinstance(due, LabOutcome) else due


# --- as linhas --------------------------------------------------------------------------


def _result_row(model_run: ModelRunResult, counts: tuple[int, int] | None) -> LabResult:
    """Um `lab_result` sem `run`, no molde de `compute._row` (RF-04).

    Com `error`, os numeros e o `adequate` sao nulos. O que `risk_result` guarda e nao fala
    da decada -- `var_latest`, `var_mean`, `basel_zone` -- nao existe aqui.
    """
    error = model_run.error or ""
    failed = bool(error)
    kupiec = None if failed else _backtest(model_run, "kupiec")
    christoffersen = None if failed else _backtest(model_run, "christoffersen")
    dq = None if failed else _backtest(model_run, "dq")
    details: dict[str, Any] = {} if kupiec is None else kupiec.details
    pair = counts if model_run.model_name in EXPENSIVE and not failed else None
    return LabResult(
        model_name=model_run.model_name,
        model_category=get_model(model_run.model_name).category.value,
        alpha=Decimal(str(model_run.alpha)).quantize(Q4),
        hyperparameters=get_model(model_run.model_name)().hyperparameters,
        test_count=details.get("n_obs"),
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
        adequate=_verdict(model_run),
        error=error,
        reused_snapshots=None if pair is None else pair[0],
        trained_snapshots=None if pair is None else pair[1],
    )


def _year_rows(slices: Sequence[YearSlice]) -> list[LabYear]:
    return [
        LabYear(
            index=s.index,
            start_date=s.start_date,
            end_date=s.end_date,
            test_count=s.test_count,
            violations=s.violations,
            expected_violations=Decimal(str(s.expected)).quantize(Q6),
            kupiec_passed=None if s.kupiec is None else s.kupiec.passed,
            kupiec_p_value=(
                None if s.kupiec is None else _decimal(s.kupiec.p_value, Q10)
            ),
            christoffersen_passed=(
                None if s.christoffersen is None else s.christoffersen.passed
            ),
            christoffersen_p_value=(
                None
                if s.christoffersen is None
                else _decimal(s.christoffersen.p_value, Q10)
            ),
            adequate=s.adequate,
        )
        for s in slices
    ]


def _key(model_name: str, alpha: Decimal | float) -> tuple[str, Decimal]:
    return model_name, Decimal(str(alpha)).quantize(Q4)


# --- a escrita, sob a trava (RF-10) --------------------------------------------------------


def _after_lab_lock() -> None:
    """Ponto de desvio dos testes concorrentes, entre a trava do ativo e a conferencia do
    `ok`. Nao faz nada; e chamado pelo nome global deste modulo."""


def write_lab(
    ident: LabIdentity,
    decade: Decade,
    *,
    origin: str,
    calculated_at: datetime,
    finished_at: datetime,
    status: str,
    error: str,
    results: Sequence[LabResult],
    years: Mapping[tuple[str, Decimal], Sequence[LabYear]],
) -> LabRun | None:
    """Grava a execucao, os resultados e os anos numa transacao; `None` se ja ha `ok`.

    `results` sao `LabResult` sem `run`; `years`, os `LabYear` sem `result`, pela chave
    (`model_name`, `alpha` em `Decimal(6,4)`) do resultado. A trava do ativo e segurada so
    aqui, nunca durante o calculo; dentro dela, a conferencia do `ok` decide: havendo, nada e
    gravado -- nem `partial`, nem `failed`.
    """
    series = decade.series
    asset = Asset.objects.get(pk=ident.asset_id)
    manifest = _manifest(asset, calculated_at, ident.seed, series)
    manifest.pop("requested_by_id")
    # a identidade sai de `ident`, a que `lab_due` conferiu, e nao de outra leitura
    manifest.update(ident.fields())
    manifest.pop("asset_id")
    test_count = int(manifest["test_count"])
    with transaction.atomic():
        # apps/api/ondemand.py -- pg_advisory_xact_lock(7102, asset_id)
        lock_asset(ident.asset_id)
        _after_lab_lock()
        if LabRun.objects.filter(status=LabRun.Status.OK, **ident.fields()).exists():
            return None
        run = LabRun.objects.create(
            **manifest,
            finished_at=finished_at,
            status=status,
            origin=origin,
            library_versions=ident.library_versions,
            year_count=math.ceil(max(test_count, 0) / config.LAB_YEAR_DAYS),
            price_fingerprint=price_fingerprint(series, len(series) - 1),
            requested_models=list(MODELS),
            error=error,
        )
        for row in results:
            row.run = run
        created = LabResult.objects.bulk_create(list(results))
        year_rows: list[LabYear] = []
        for row in created:
            for year in years.get(_key(row.model_name, row.alpha), ()):
                year.result = row
                year_rows.append(year)
        LabYear.objects.bulk_create(year_rows)
    return run


# --- o experimento (RF-10) -----------------------------------------------------------------


def series_changed(asset: Asset, decade: Decade) -> bool:
    """A serie da decada, relida agora, nao e a que o calculo usou.

    `valid_bars` relido e cortado no mesmo `decade_end`; a impressao digital (as datas e os
    `adj_close` de todos os pregoes) comparada com a de `decade.series`. Um pregao novo
    **depois** do fim nao conta -- a decada completa nao muda com ele; um provento que reajusta
    o historico (D-53), ou um pregao corrigido dentro da decada, conta.
    """
    now_series = [b for b in valid_bars(asset) if b.date <= decade.end_date]
    if len(now_series) != len(decade.series):
        return True
    used = price_fingerprint(decade.series, len(decade.series) - 1)
    return price_fingerprint(now_series, len(now_series) - 1) != used


def _is_identity_violation(exc: IntegrityError) -> bool:
    diag = getattr(exc.__cause__, "diag", None)
    return getattr(diag, "constraint_name", None) == IDENTITY_CONSTRAINT


def run_lab(
    asset: Asset, *, origin: str, now: Callable[[], datetime] = timezone.now
) -> LabOutcome:
    """O experimento do ativo, se devido: calcula, recorta e grava (RF-10).

    Pula sem gravar se nao e devido. O registry e carregado e conferido antes de calcular
    (D-66): faltando modelo, grava o `lab_run` `failed` sem calcular. Uma excecao no calculo,
    no recorte ou na soma vira o `lab_run` `failed` com `error`, sem resultados; a serie que
    mudou durante o calculo (`series_changed`) tambem, com `SERIES_CHANGED`. O
    `IntegrityError` da restricao da identidade e "ja calculado". Outras excecoes da escrita
    sobem: quem chama -- a tarefa -- nunca levanta.
    """
    started = time.monotonic()
    due = _due(asset)
    if isinstance(due, LabOutcome):
        return due
    ident, decade = due

    # O filho do prefork nasce sem o registry: carregar antes de consultar.
    load_all_model_modules()
    load_all_backtest_modules()
    missing = [m for m in MODELS if m not in list_models()]

    calculated_at = now()
    status = LabRun.Status.FAILED
    error = ""
    results: list[LabResult] = []
    years: dict[tuple[str, Decimal], list[LabYear]] = {}
    if missing:
        error = f"modelos ausentes do registry: {ModelsMissing(missing)}"
    else:
        key = SnapshotKey(
            asset=asset,
            seed=ident.seed,
            engine_version=ident.engine_version,
            train_window_days=ident.train_window_days,
            first_price_date=ident.first_price_date,
            library_versions=ident.library_versions,
        )
        try:
            result, counts = run_models(key, decade.series, MODELS, full=False)
            slices = years_by_result(result, period_of_test(asset, decade))
        except LabSumMismatch as exc:
            error = str(exc)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        else:
            if series_changed(asset, decade):
                error = SERIES_CHANGED
            else:
                status = _status(result)
                results = _results(result, counts)
                years = {
                    _key(name, alpha): _year_rows(s)
                    for (name, alpha), s in slices.items()
                }
    finished_at = now()
    try:
        run = write_lab(
            ident,
            decade,
            origin=origin,
            calculated_at=calculated_at,
            finished_at=finished_at,
            status=status,
            error=error,
            results=results,
            years=years,
        )
    except IntegrityError as exc:
        if not _is_identity_violation(exc):
            raise
        run = None
    elapsed = time.monotonic() - started
    if run is None:
        return LabOutcome(LabOutcome.ALREADY, decade=decade, elapsed=elapsed)
    return LabOutcome(LabOutcome.WRITTEN, run=run, decade=decade, elapsed=elapsed)


def _status(result: ExperimentResult) -> LabRun.Status:
    with_error = sum(1 for r in result.runs if r.error)
    expected = len(MODELS) * len(config.ALPHAS)  # 18
    return LabRun.Status(status_for(expected, len(result.runs), with_error))


def _results(result: ExperimentResult, counts: SnapshotCounts) -> list[LabResult]:
    return [_result_row(r, counts.get((r.model_name, r.alpha))) for r in result.runs]
