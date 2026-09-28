"""Infraestrutura dos testes da API.

`debug` parametriza o teste que a pede com `DEBUG` ligado e desligado (V-08): o formato de
erro da D-86 tem de valer nos dois, e e com `DEBUG` ligado que um tratador que devolvesse
`None` vazaria a pagina de depuracao. As T7 e T12 do M1.6a reusam esta fixture.
"""

from __future__ import annotations

import pytest
from pytest_django import Settings


@pytest.fixture(params=[True, False], ids=["debug_ligado", "debug_desligado"])
def debug(request: pytest.FixtureRequest, settings: Settings) -> bool:
    ligado: bool = request.param
    settings.DEBUG = ligado
    return ligado
