"""VaR por simulacao de Monte Carlo: ajusta uma normal aos retornos conhecidos e simula
cenarios para estimar o quantil de perdas, em vez de usar a formula fechada do metodo
parametrico. A normal e reestimada em janela expansiva a cada `REFIT_FREQUENCY_DAYS`
pregoes do teste (M1.4b), e as simulacoes de cada trecho saem em sequencia de um gerador
so por chamada de `estimate_var`.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from engine.models.base import ModelCategory, VaREstimate, VaRModel
from engine.models.registry import register_model
from engine.models.traditional._expanding import (
    REFIT_FREQUENCY_DAYS,
    expanding_var_series,
)


@register_model("monte_carlo")
class MonteCarloVaR(VaRModel):
    category = ModelCategory.TRADITIONAL

    def __init__(self, n_simulations: int = 100_000, random_state: int = 42):
        self.n_simulations = n_simulations
        self.random_state = random_state

    @property
    def hyperparameters(self) -> dict[str, Any]:
        return {
            "n_simulations": self.n_simulations,
            "random_state": self.random_state,
            "refit_frequency_days": REFIT_FREQUENCY_DAYS,
        }

    def fit(self, returns: pd.Series) -> MonteCarloVaR:
        self.train_returns_ = returns
        return self

    def estimate_var(
        self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1
    ) -> VaREstimate:
        # um gerador por chamada: o trecho k tira as suas simulacoes depois das dos k
        # trechos anteriores (o trecho 0 sai igual ao numero de antes da correcao)
        rng = np.random.default_rng(self.random_state)

        def var_of(known: pd.Series) -> float:
            mu_h = known.mean() * horizon
            sigma_h = known.std(ddof=1) * (horizon**0.5)
            simulated_returns = rng.normal(mu_h, sigma_h, size=self.n_simulations)
            return float(-np.quantile(simulated_returns, alpha))

        var_series = expanding_var_series(self.train_returns_, returns, var_of)
        return VaREstimate(
            var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name
        )
