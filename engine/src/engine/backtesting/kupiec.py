"""Teste de Kupiec (1995) — Proportion of Failures (POF): compara a taxa de violacoes
observada contra a esperada por `alpha`, via razao de verossimilhancas qui-quadrado(1).
"""

from __future__ import annotations

import pandas as pd
from scipy.special import xlogy
from scipy.stats import chi2

from engine.backtesting.base import BacktestResult, BacktestTest
from engine.backtesting.registry import register_backtest

SIGNIFICANCE = 0.05


def unconditional_coverage_lr(x: int, n: int, alpha: float) -> float:
    log_l_null = xlogy(n - x, 1 - alpha) + xlogy(x, alpha)
    pi_hat = x / n
    log_l_alt = xlogy(n - x, 1 - pi_hat) + xlogy(x, pi_hat)
    return -2 * (log_l_null - log_l_alt)


@register_backtest("kupiec")
class KupiecTest(BacktestTest):
    def run(
        self, returns: pd.Series, var_series: pd.Series, alpha: float
    ) -> BacktestResult:
        violations = returns < -var_series
        n, x = len(violations), int(violations.sum())

        lr_uc = unconditional_coverage_lr(x, n, alpha)
        p_value = 1 - chi2.cdf(lr_uc, df=1)

        return BacktestResult(
            test_name=self.name,
            statistic=lr_uc,
            p_value=p_value,
            passed=bool(p_value > SIGNIFICANCE),
            details={
                "violations": x,
                "expected": n * alpha,
                "n_obs": n,
                "violation_rate": x / n,
            },
        )
