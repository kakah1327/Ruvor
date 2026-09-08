"""Dynamic Quantile test (Engle & Manganelli, 2004): regride o indicador de violacao
centrado (Hit_t) sobre suas defasagens e o VaR contemporaneo, e testa se os coeficientes
sao conjuntamente zero (teste de Wald) — captura tanto cobertura incondicional quanto
dependencia temporal nas violacoes, num unico teste.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2

from engine.backtesting.base import BacktestResult, BacktestTest
from engine.backtesting.registry import register_backtest

SIGNIFICANCE = 0.05
N_LAGS = 4


@register_backtest("dq")
class DynamicQuantileTest(BacktestTest):
    def run(
        self, returns: pd.Series, var_series: pd.Series, alpha: float
    ) -> BacktestResult:
        hit = (returns < -var_series).astype(float) - alpha
        n = len(hit)
        n_regressors = N_LAGS + 2  # constante + N_LAGS defasagens + VaR contemporaneo

        if n - N_LAGS < n_regressors + 5:
            raise ValueError(
                f"Serie curta demais para o teste DQ com {N_LAGS} defasagens "
                f"({n} observacoes, minimo recomendado {N_LAGS + n_regressors + 5})"
            )

        hit_vals = hit.to_numpy()
        var_vals = var_series.to_numpy()

        y = hit_vals[N_LAGS:]
        columns = [np.ones(n - N_LAGS)]
        for lag in range(1, N_LAGS + 1):
            columns.append(hit_vals[N_LAGS - lag : n - lag])
        columns.append(var_vals[N_LAGS:])
        x = np.column_stack(columns)

        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        dq_stat = float(beta @ (x.T @ x) @ beta) / (alpha * (1 - alpha))
        p_value = 1 - chi2.cdf(dq_stat, df=n_regressors)

        return BacktestResult(
            test_name=self.name,
            statistic=dq_stat,
            p_value=p_value,
            passed=bool(p_value > SIGNIFICANCE),
            details={"n_lags": N_LAGS, "beta": beta.tolist()},
        )
