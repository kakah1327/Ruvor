"""VaR parametrico (variancia-covariancia): assume retornos ~ N(mu, sigma^2)."""
from __future__ import annotations

import pandas as pd
from scipy.stats import norm

from engine.models.base import ModelCategory, VaREstimate, VaRModel
from engine.models.registry import register_model


@register_model("parametric")
class ParametricVaR(VaRModel):
    category = ModelCategory.TRADITIONAL

    def fit(self, returns: pd.Series) -> "ParametricVaR":
        self.mu_ = returns.mean()
        self.sigma_ = returns.std(ddof=1)
        return self

    def estimate_var(self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1) -> VaREstimate:
        z = norm.ppf(alpha)
        mu_h = self.mu_ * horizon
        sigma_h = self.sigma_ * (horizon ** 0.5)
        var_value = -(mu_h + z * sigma_h)

        var_series = pd.Series(var_value, index=returns.index)
        return VaREstimate(var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name)
