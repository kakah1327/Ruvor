"""Teste de independencia de Christoffersen (1998): verifica se as violacoes de VaR sao
independentes ao longo do tempo (nao-clusterizadas), via cadeia de Markov de 1a ordem
sobre o indicador de violacao. Complementa o Kupiec, que so testa a taxa incondicional.
"""
from __future__ import annotations

import pandas as pd
from scipy.special import xlogy
from scipy.stats import chi2

from varlab.backtesting.base import BacktestResult, BacktestTest
from varlab.backtesting.kupiec import unconditional_coverage_lr
from varlab.backtesting.registry import register_backtest

SIGNIFICANCE = 0.05


@register_backtest("christoffersen")
class ChristoffersenTest(BacktestTest):
    def run(self, returns: pd.Series, var_series: pd.Series, alpha: float) -> BacktestResult:
        indicator = (returns < -var_series).astype(int)
        prev, curr = indicator.iloc[:-1].to_numpy(), indicator.iloc[1:].to_numpy()

        n00 = int(((prev == 0) & (curr == 0)).sum())
        n01 = int(((prev == 0) & (curr == 1)).sum())
        n10 = int(((prev == 1) & (curr == 0)).sum())
        n11 = int(((prev == 1) & (curr == 1)).sum())

        pi_01 = n01 / (n00 + n01) if (n00 + n01) else 0.0
        pi_11 = n11 / (n10 + n11) if (n10 + n11) else 0.0
        pi = (n01 + n11) / (n00 + n01 + n10 + n11)

        log_l_null = xlogy(n00 + n10, 1 - pi) + xlogy(n01 + n11, pi)
        log_l_alt = (
            xlogy(n00, 1 - pi_01) + xlogy(n01, pi_01) + xlogy(n10, 1 - pi_11) + xlogy(n11, pi_11)
        )
        lr_ind = -2 * (log_l_null - log_l_alt)
        p_value = 1 - chi2.cdf(lr_ind, df=1)

        lr_uc = unconditional_coverage_lr(int(indicator.sum()), len(indicator), alpha)
        lr_cc = lr_uc + lr_ind

        return BacktestResult(
            test_name=self.name,
            statistic=lr_ind,
            p_value=p_value,
            passed=bool(p_value > SIGNIFICANCE),
            details={
                "n00": n00,
                "n01": n01,
                "n10": n10,
                "n11": n11,
                "lr_conditional_coverage": lr_cc,
                "p_value_conditional_coverage": 1 - chi2.cdf(lr_cc, df=2),
            },
        )
