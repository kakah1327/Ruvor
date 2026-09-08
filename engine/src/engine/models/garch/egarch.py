"""EGARCH (Nelson, 1991): extensao assimetrica do GARCH — a variancia condicional (em
log) reage de forma diferente a choques negativos e positivos (leverage effect), sem
exigir restricoes de nao-negatividade nos parametros.
"""

from __future__ import annotations

from engine.models.base import ModelCategory
from engine.models.garch._conditional import ConditionalVolatilityVaR
from engine.models.registry import register_model


@register_model("egarch")
class EgarchVaR(ConditionalVolatilityVaR):
    category = ModelCategory.GARCH

    def _arch_kwargs(self) -> dict:
        return {"vol": "EGARCH", "p": 1, "o": 1, "q": 1}
