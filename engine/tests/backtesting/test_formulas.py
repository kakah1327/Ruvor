"""Valida a CORRECAO matematica de cada teste de backtesting (nao so a interface, que
ja e coberta por test_all_backtests.py), com series construidas para ter um numero de
violacoes conhecido de antemao.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from engine.backtesting.basileia import BasileiaZonesTest
from engine.backtesting.christoffersen import ChristoffersenTest
from engine.backtesting.dq import DynamicQuantileTest
from engine.backtesting.kupiec import KupiecTest, unconditional_coverage_lr


def _reference_lr_uc(x: int, n: int, alpha: float) -> float:
    pi_hat = x / n

    def term(count: int, p: float) -> float:
        return count * math.log(p) if p > 0 else 0.0

    log_l_null = term(n - x, 1 - alpha) + term(x, alpha)
    log_l_alt = term(n - x, 1 - pi_hat) + term(x, pi_hat)
    return -2 * (log_l_null - log_l_alt)


def _constant_var_series(n: int, value: float = 1.0) -> pd.Series:
    return pd.Series(value, index=pd.RangeIndex(n))


def _returns_with_violations_at(n: int, violation_idx, var_value: float = 1.0) -> pd.Series:
    returns = pd.Series(0.0, index=pd.RangeIndex(n))
    returns.iloc[list(violation_idx)] = -2 * var_value
    return returns


# --- Kupiec ---------------------------------------------------------------


def test_kupiec_matches_independent_reference_formula():
    x, n, alpha = 10, 100, 0.05
    assert unconditional_coverage_lr(x, n, alpha) == pytest.approx(_reference_lr_uc(x, n, alpha))


def test_kupiec_rejects_excess_violations():
    n, alpha = 100, 0.05
    var_series = _constant_var_series(n)
    returns = _returns_with_violations_at(n, range(20), var_series.iloc[0])  # 20% vs 5% esperado

    result = KupiecTest().run(returns, var_series, alpha)

    assert result.details["violations"] == 20
    assert result.p_value < 0.05
    assert result.passed is False


def test_kupiec_accepts_expected_violation_rate():
    n, alpha = 200, 0.05
    var_series = _constant_var_series(n)
    returns = _returns_with_violations_at(n, range(10), var_series.iloc[0])  # exatos 5% de 200

    result = KupiecTest().run(returns, var_series, alpha)

    assert result.p_value > 0.05
    assert result.passed is True


# --- Christoffersen ---------------------------------------------------------


def test_christoffersen_rejects_clustered_violations():
    n, alpha = 200, 0.05
    var_series = _constant_var_series(n)
    clustered = list(range(0, 10)) + list(range(100, 110))  # 2 blocos de 10 consecutivas
    returns = _returns_with_violations_at(n, clustered, var_series.iloc[0])

    result = ChristoffersenTest().run(returns, var_series, alpha)

    assert result.p_value < 0.05
    assert result.passed is False


def test_christoffersen_accepts_random_violations():
    n, alpha = 200, 0.05
    var_series = _constant_var_series(n)
    rng = np.random.default_rng(0)
    random_idx = rng.choice(n, size=20, replace=False)
    returns = _returns_with_violations_at(n, random_idx, var_series.iloc[0])

    result = ChristoffersenTest().run(returns, var_series, alpha)

    assert result.p_value > 0.05
    assert result.passed is True


# --- Dynamic Quantile --------------------------------------------------------


def test_dq_runs_and_returns_finite_values(synthetic_returns):
    alpha = 0.05
    threshold = -synthetic_returns.quantile(alpha)
    var_series = synthetic_returns.apply(lambda _: threshold)

    result = DynamicQuantileTest().run(synthetic_returns, var_series, alpha)

    assert np.isfinite(result.statistic)
    assert np.isfinite(result.p_value)
    assert result.details["n_lags"] == 4
    assert len(result.details["beta"]) == 6


def test_dq_raises_on_short_series():
    n, alpha = 5, 0.05
    var_series = _constant_var_series(n)
    returns = pd.Series(0.0, index=var_series.index)

    with pytest.raises(ValueError):
        DynamicQuantileTest().run(returns, var_series, alpha)


# --- Basileia -----------------------------------------------------------------


def test_basileia_matches_classic_zones_at_n250_alpha1pct():
    n, alpha = 250, 0.01
    var_series = _constant_var_series(n)

    def zone_for(x: int) -> str:
        returns = _returns_with_violations_at(n, range(x), var_series.iloc[0])
        return BasileiaZonesTest().run(returns, var_series, alpha).details["zone"]

    assert zone_for(2) == "verde"
    assert zone_for(6) == "amarela"
    assert zone_for(12) == "vermelha"


def test_basileia_yellow_passes_red_fails():
    n, alpha = 250, 0.01
    var_series = _constant_var_series(n)

    yellow = BasileiaZonesTest().run(
        _returns_with_violations_at(n, range(6), var_series.iloc[0]), var_series, alpha
    )
    red = BasileiaZonesTest().run(
        _returns_with_violations_at(n, range(12), var_series.iloc[0]), var_series, alpha
    )

    assert yellow.passed is True
    assert red.passed is False
