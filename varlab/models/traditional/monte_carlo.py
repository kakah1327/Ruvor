"""VaR por simulacao de Monte Carlo: ajusta uma normal aos retornos de treino e simula
cenarios para estimar o quantil de perdas, em vez de usar a formula fechada do metodo
parametrico.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from varlab.models.base import ModelCategory, VaREstimate, VaRModel
from varlab.models.registry import register_model


@register_model("monte_carlo")
class MonteCarloVaR(VaRModel):
    category = ModelCategory.TRADITIONAL

    def __init__(self, n_simulations: int = 100_000, random_state: int = 42):
        self.n_simulations = n_simulations
        self.random_state = random_state

    def fit(self, returns: pd.Series) -> "MonteCarloVaR":
        self.mu_ = returns.mean()
        self.sigma_ = returns.std(ddof=1)
        return self

    def estimate_var(self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1) -> VaREstimate:
        rng = np.random.default_rng(self.random_state)
        mu_h = self.mu_ * horizon
        sigma_h = self.sigma_ * (horizon ** 0.5)

        simulated_returns = rng.normal(mu_h, sigma_h, size=self.n_simulations)
        var_value = -np.quantile(simulated_returns, alpha)

        var_series = pd.Series(var_value, index=returns.index)
        return VaREstimate(var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name)
