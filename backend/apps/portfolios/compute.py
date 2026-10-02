"""A conversao do resultado do motor nas colunas da carteira (M2.2a, RF-23). So no `worker`.

**As regras sao as de `_row`** (`apps/risk/compute.py`), copiadas e nao chamadas: `_row` e privada
da `marco1` e presa a `RiskRun`, e este bloco nao altera `apps/risk/`. Quando `error` nao e vazio,
todas as colunas de numero sao nulas; `violations` e `expected_violations` sao os do Kupiec; o
veredito e Kupiec **e** Christoffersen (D-64); os quantizadores `Q4`, `Q6` e `Q10` sao os do ativo.
Sem as duas colunas de retrato: a carteira nao usa retratos.

O teste de paridade (`tests/portfolios/test_conversao.py`) passa os mesmos `ModelRunResult` pelas
duas e compara campo a campo: se a `marco1` mudar `_row`, ele reprova na PR dela.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from engine.backtesting.base import BacktestResult
from engine.experiments.runner import ModelRunResult
from engine.models import get_model

from apps.portfolios.models import PortfolioRiskResult, PortfolioRiskRun
from apps.risk import config as risk_config
from apps.risk.compute import Q4, Q6, Q10


def _backtest(model_run: ModelRunResult, name: str) -> BacktestResult | None:
    for backtest in model_run.backtests:
        if backtest.test_name == name:
            return backtest
    return None


def _verdict(model_run: ModelRunResult) -> bool | None:
    """Kupiec **e** Christoffersen, nulo quando houve erro. DQ e Basileia nao entram."""
    error = model_run.error or ""
    kupiec = _backtest(model_run, "kupiec")
    christoffersen = _backtest(model_run, "christoffersen")
    kupiec_passed = None if kupiec is None else kupiec.passed
    christoffersen_passed = None if christoffersen is None else christoffersen.passed
    return None if error else (kupiec_passed and christoffersen_passed)


def _decimal(value: float | None, quantum: Decimal) -> Decimal | None:
    return None if value is None else Decimal(str(float(value))).quantize(quantum)


def row(run: PortfolioRiskRun, model_run: ModelRunResult) -> PortfolioRiskResult:
    """Uma linha de `gold.portfolio_risk_result`, a partir do `ModelRunResult`."""
    error = model_run.error or ""
    failed = bool(error)
    kupiec = None if failed else _backtest(model_run, "kupiec")
    christoffersen = None if failed else _backtest(model_run, "christoffersen")
    dq = None if failed else _backtest(model_run, "dq")
    basileia = None if failed else _backtest(model_run, "basileia")
    estimate = None if failed else model_run.estimate
    details: dict[str, Any] = {} if kupiec is None else kupiec.details
    return PortfolioRiskResult(
        run=run,
        model_name=model_run.model_name,
        model_category=get_model(model_run.model_name).category.value,
        alpha=Decimal(str(model_run.alpha)).quantize(Q4),
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


def failed_rows(
    run: PortfolioRiskRun, model_name: str, error: str
) -> list[PortfolioRiskResult]:
    """O par de erro do modelo: um `row` por nivel, com `error` e os numeros nulos."""
    return [
        row(run, ModelRunResult(model_name=model_name, alpha=alpha, error=error))
        for alpha in risk_config.ALPHAS
    ]
