"""Infraestrutura dos testes da carteira (M2.2a).

**Os limites.** O `compose` repassa o `.env` ao conteiner, e o teto e o prazo do pedido de risco
de carteira viriam dele: a fixture `limites` fixa os padroes da spec em todo teste daqui, o molde
de `prazo` em `tests/api/test_pedido.py`. O teste que precisa de outro valor o troca por cima.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from pytest_django import Settings


@pytest.fixture(autouse=True)
def limites(settings: Settings) -> None:
    settings.RUVOR_PORTFOLIO_TIMEOUT = timedelta(minutes=60)
    settings.RUVOR_PORTFOLIO_COMPUTE_MAX = 2
