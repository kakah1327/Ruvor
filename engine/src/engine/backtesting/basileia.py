"""Zonas de Basileia (Basel Committee, 1996): classifica o numero de violacoes de VaR
em verde/amarela/vermelha via probabilidade binomial acumulada, sobre a janela de 250
dias uteis exigida pelo Acordo de Basileia II (periodo minimo regulatorio de backtesting).
"""
from __future__ import annotations

import pandas as pd
from scipy.stats import binom

from engine.backtesting.base import BacktestResult, BacktestTest
from engine.backtesting.registry import register_backtest

WINDOW_DAYS = 250


@register_backtest("basileia")
class BasileiaZonesTest(BacktestTest):
    def run(self, returns: pd.Series, var_series: pd.Series, alpha: float) -> BacktestResult:
        if len(returns) < WINDOW_DAYS:
            raise ValueError(
                f"Zonas de Basileia exigem janela minima de {WINDOW_DAYS} dias uteis de "
                f"teste (Basileia II) — {len(returns)} disponiveis"
            )

        window_returns = returns.iloc[-WINDOW_DAYS:]
        window_var = var_series.iloc[-WINDOW_DAYS:]
        violations = window_returns < -window_var
        x = int(violations.sum())

        cum_prob = binom.cdf(x, WINDOW_DAYS, alpha)
        if cum_prob < 0.95:
            zone = "verde"
        elif cum_prob < 0.9999:
            zone = "amarela"
        else:
            zone = "vermelha"

        return BacktestResult(
            test_name=self.name,
            statistic=float(x),
            p_value=1 - cum_prob,
            passed=zone in ("verde", "amarela"),
            details={
                "zone": zone,
                "violations": x,
                "expected": WINDOW_DAYS * alpha,
                "window_days": WINDOW_DAYS,
                "cum_prob": cum_prob,
            },
        )
