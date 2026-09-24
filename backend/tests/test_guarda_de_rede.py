"""RF-14: a guarda de rede existe e vale para a suite inteira.

A guarda e a fixture `autouse` `sem_rede`, em `tests/conftest.py`. Sem este arquivo,
apaga-la deixaria a suite **inteira verde** — medido na revisao final do M1.3 — e o
proximo app nasceria sem guarda sem que nada acusasse. Requisito sem verificacao
permanente e a categoria de defeito mais cara deste projeto.

Vive na raiz de `tests/`, e nao dentro de um app, de proposito: o que se prova aqui e
que a guarda alcanca todo o backend, nao um diretorio em particular.
"""

from __future__ import annotations

import urllib.request

import pytest


def test_a_guarda_de_rede_esta_armada() -> None:
    """Chamar `urlopen` num teste levanta, com a mensagem que o M1.3 congelou."""
    with pytest.raises(AssertionError, match="teste tentou sair para a rede"):
        # 127.0.0.1:1 nao atende: se a guarda cair, o erro sera de conexao, nao
        # AssertionError, e o teste reprova do mesmo jeito — sem sair da maquina.
        urllib.request.urlopen("http://127.0.0.1:1/")
