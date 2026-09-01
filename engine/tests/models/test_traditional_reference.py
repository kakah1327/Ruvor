"""Valida os 3 metodos tradicionais de VaR (Etapa 1) contra calculos de referencia
independentes -- nao so a interface (ja coberta por test_all_models.py). Fecha o gap
identificado na Matriz de Validacao: "Resultados validados contra calculos de referencia."
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from engine.models.traditional.historical import HistoricalVaR
from engine.models.traditional.monte_carlo import MonteCarloVaR
from engine.models.traditional.parametric import ParametricVaR


@pytest.fixture
def train_test_returns():
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2020-01-01", periods=500)
    returns = pd.Series(rng.normal(0.0005, 0.02, size=len(dates)), index=dates)
    return returns.iloc[:300], returns.iloc[300:]


def test_parametric_matches_closed_form_reference(train_test_returns):
    train, test = train_test_returns
    alpha = 0.05

    mu, sigma = train.mean(), train.std(ddof=1)
    expected = -(mu + norm.ppf(alpha) * sigma)

    model = ParametricVaR().fit(train)
    estimate = model.estimate_var(test, alpha=alpha, horizon=1)

    assert estimate.var_series.iloc[0] == pytest.approx(expected)
    assert (estimate.var_series == estimate.var_series.iloc[0]).all()  # estatico: 1 valor p/ toda a serie


def test_historical_matches_independent_empirical_quantile(train_test_returns):
    train, test = train_test_returns
    alpha = 0.05

    expected = -np.quantile(train.to_numpy(), alpha)

    model = HistoricalVaR().fit(train)
    estimate = model.estimate_var(test, alpha=alpha, horizon=1)

    assert estimate.var_series.iloc[0] == pytest.approx(expected)


def test_monte_carlo_converges_to_parametric_reference(train_test_returns):
    """Monte Carlo simula da MESMA normal(mu, sigma) do metodo parametrico -- com
    simulacoes suficientes, deve convergir para o mesmo VaR fechado (tolerancia
    estatistica, nao igualdade exata)."""
    train, test = train_test_returns
    alpha = 0.05

    mu, sigma = train.mean(), train.std(ddof=1)
    parametric_reference = -(mu + norm.ppf(alpha) * sigma)

    model = MonteCarloVaR(n_simulations=200_000, random_state=1).fit(train)
    estimate = model.estimate_var(test, alpha=alpha, horizon=1)

    assert estimate.var_series.iloc[0] == pytest.approx(parametric_reference, abs=0.001)
