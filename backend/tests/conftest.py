"""Infraestrutura comum da suite inteira: a guarda de rede, o cache e a organizacao.

O `conftest.py` do pytest so alcanca o diretorio em que esta. Aqui, na raiz de
`tests/`, a fixture vale para todos os testes do backend — inclusive os de
diretorios que ainda nao existem.

**O cache e a organizacao do contexto (M4.2, RF-08 e RF-13).** A suite usa o `LocMemCache`,
que dura a rodada inteira: sem limpar, os pedidos anonimos de todos os testes somariam na
mesma taxa, e a suite quebraria no meio por um motivo que nao e dela. E o contexto da
organizacao, que a autenticacao poe, vazaria de um teste para o seguinte na mesma thread quando
algum teste chamar uma autenticacao direto, sem o middleware que o zera.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import NoReturn

import pytest
from django.core.cache import cache

from apps.accounts.tenancy import set_organization_id


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    def recusa(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("teste tentou sair para a rede")

    monkeypatch.setattr("urllib.request.urlopen", recusa)


@pytest.fixture(autouse=True)
def cache_e_organizacao_limpos() -> Iterator[None]:
    cache.clear()
    set_organization_id(None)
    yield
    set_organization_id(None)
