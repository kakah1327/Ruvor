"""VaR por simulacao historica: usa o quantil empirico dos retornos conhecidos, sem supor
nenhuma distribuicao parametrica, reestimado em janela expansiva a cada
`REFIT_FREQUENCY_DAYS` pregoes do teste (M1.4b).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from engine.models.base import ModelCategory, VaREstimate, VaRModel
from engine.models.registry import register_model
from engine.models.traditional._expanding import (
    REFIT_FREQUENCY_DAYS,
    expanding_var_series,
)


@register_model("historical")
class HistoricalVaR(VaRModel):
    category = ModelCategory.TRADITIONAL

    @property
    def hyperparameters(self) -> dict[str, Any]:
        return {"refit_frequency_days": REFIT_FREQUENCY_DAYS}

    def fit(self, returns: pd.Series) -> HistoricalVaR:
        self.train_returns_ = returns
        return self

    def estimate_var(
        self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1
    ) -> VaREstimate:
        def var_of(known: pd.Series) -> float:
            var_1d = -known.quantile(alpha)
            return float(var_1d * (horizon**0.5))

        var_series = expanding_var_series(self.train_returns_, returns, var_of)
        return VaREstimate(
            var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name
        )
