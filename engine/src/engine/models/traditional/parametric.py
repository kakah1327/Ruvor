"""VaR parametrico (variancia-covariancia): assume retornos ~ N(mu, sigma^2), com `mu` e
`sigma` reestimados em janela expansiva a cada `REFIT_FREQUENCY_DAYS` pregoes do teste
(M1.4b)."""

from __future__ import annotations

from typing import Any

import pandas as pd
from scipy.stats import norm

from engine.models.base import ModelCategory, VaREstimate, VaRModel
from engine.models.registry import register_model
from engine.models.traditional._expanding import (
    REFIT_FREQUENCY_DAYS,
    expanding_var_series,
)


@register_model("parametric")
class ParametricVaR(VaRModel):
    category = ModelCategory.TRADITIONAL

    @property
    def hyperparameters(self) -> dict[str, Any]:
        return {"refit_frequency_days": REFIT_FREQUENCY_DAYS}

    def fit(self, returns: pd.Series) -> ParametricVaR:
        self.train_returns_ = returns
        return self

    def estimate_var(
        self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1
    ) -> VaREstimate:
        z = norm.ppf(alpha)

        def var_of(known: pd.Series) -> float:
            mu_h = known.mean() * horizon
            sigma_h = known.std(ddof=1) * (horizon**0.5)
            return float(-(mu_h + z * sigma_h))

        var_series = expanding_var_series(self.train_returns_, returns, var_of)
        return VaREstimate(
            var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name
        )
