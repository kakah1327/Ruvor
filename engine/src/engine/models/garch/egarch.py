"""EGARCH (Nelson, 1991): extensao assimetrica do GARCH — a variancia condicional (em
log) reage de forma diferente a choques negativos e positivos (leverage effect), sem
exigir restricoes de nao-negatividade nos parametros.
"""

from __future__ import annotations

import math

from engine.models.base import ModelCategory
from engine.models.garch._conditional import ConditionalVolatilityVaR
from engine.models.registry import register_model


@register_model("egarch")
class EgarchVaR(ConditionalVolatilityVaR):
    category = ModelCategory.GARCH

    def _arch_kwargs(self) -> dict:
        return {"vol": "EGARCH", "p": 1, "o": 1, "q": 1}

    def _fallback_starting_values(self, variance: float) -> list[list[float]]:
        # [omega, alpha, gamma, beta]; omega = log(variancia incondicional) * (1 - beta)
        log_variance = math.log(variance)
        return [
            [0.05 * log_variance, 0.05, 0.0, 0.95],
            [0.10 * log_variance, 0.10, 0.0, 0.90],
        ]
