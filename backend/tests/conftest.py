"""Infraestrutura comum da suite inteira: a guarda de rede.

O `conftest.py` do pytest so alcanca o diretorio em que esta. Aqui, na raiz de
`tests/`, a fixture vale para todos os testes do backend — inclusive os de
diretorios que ainda nao existem.
"""

from __future__ import annotations

from typing import NoReturn

import pytest


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    def recusa(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("teste tentou sair para a rede")

    monkeypatch.setattr("urllib.request.urlopen", recusa)
