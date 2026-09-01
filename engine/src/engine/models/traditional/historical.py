"""VaR por simulacao historica: usa o quantil empirico dos retornos de treino, sem
supor nenhuma distribuicao parametrica.
"""
from __future__ import annotations

import pandas as pd

from engine.models.base import ModelCategory, VaREstimate, VaRModel
from engine.models.registry import register_model


@register_model("historical")
class HistoricalVaR(VaRModel):
    category = ModelCategory.TRADITIONAL

    def fit(self, returns: pd.Series) -> "HistoricalVaR":
        self.train_returns_ = returns
        return self

    def estimate_var(self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1) -> VaREstimate:
        var_1d = -self.train_returns_.quantile(alpha)
        var_value = var_1d * (horizon ** 0.5)

        var_series = pd.Series(var_value, index=returns.index)
        return VaREstimate(var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name)
