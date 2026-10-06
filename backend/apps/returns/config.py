"""Constantes do retorno (M5.1), num modulo so.

O corte e o piso **nao** moram aqui: `TRAIN_WINDOW_DAYS` e `MIN_SESSIONS` sao os de
`apps/risk/config.py`, uma fonte so (RF-01).
"""

from __future__ import annotations

from decimal import Decimal

#: o nivel do veredito (RF-08, RF-09): comparado com o *p* do DM ja quantizado em `Q10`
SIGNIFICANCE = Decimal("0.05")

#: os dois modelos, literais (RF-11): um padrao que dissesse `list_return_models()`
#: compararia o registry consigo mesmo, e o registry incompleto nunca seria denunciado
#: literal, nunca list_return_models()
RETURN_MODELS: tuple[str, ...] = ("ar_1", "historical_mean")
