"""GARCH(1,1) (Bollerslev, 1986): a variancia condicional depende do choque e da propria
variancia do periodo anterior, capturando volatility clustering — VaR dinamico = z_alpha * sigma_t.
"""

from __future__ import annotations

from engine.models.base import ModelCategory
from engine.models.garch._conditional import ConditionalVolatilityVaR
from engine.models.registry import register_model


@register_model("garch_1_1")
class Garch11VaR(ConditionalVolatilityVaR):
    category = ModelCategory.GARCH

    def _arch_kwargs(self) -> dict:
        return {"vol": "GARCH", "p": 1, "q": 1}
