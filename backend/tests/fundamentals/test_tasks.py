"""As tarefas de fundamentos (RF-28), sem rede e sem Redis.

`call_command` e `_enqueue` sao substituidos pelo nome em `apps.fundamentals.tasks`, que e
onde as tarefas os chamam. A corrente e conferida pela assinatura serializada:
`chain(...)` devolve um `_chain`, que nao e instancia de `celery.chain` (aprendizados).
"""

from __future__ import annotations

from typing import Any, NoReturn

import pytest
from django.core.management.base import CommandError

from apps.fundamentals.tasks import (
    _calcular_fundamentos,
    _importar_fundamentos,
    _rotina_fundamentos,
)


def test_rf28_rotina_enfileira_uma_corrente_coleta_e_depois_calculo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.fundamentals.tasks._enqueue", recebidos.append)

    _rotina_fundamentos()

    assert len(recebidos) == 1
    corrente = recebidos[0]
    assert corrente["subtask_type"] == "chain"
    elos = corrente.tasks
    assert [elo.task for elo in elos] == [
        "apps.fundamentals.tasks.importar_fundamentos",
        "apps.fundamentals.tasks.calcular_fundamentos",
    ]
    # Imutavel: com `.s()`, o texto da coleta chegaria como argumento do calculo.
    assert elos[1].immutable is True


def test_rf28_importar_devolve_a_falha_do_comando_em_vez_de_levantar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falha(*args: object, **kwargs: object) -> NoReturn:
        raise CommandError("coleta com falhas: 009512")

    monkeypatch.setattr("apps.fundamentals.tasks.call_command", falha)

    assert _importar_fundamentos() == "FALHOU: coleta com falhas: 009512"


def test_rf28_importar_propaga_o_que_nao_e_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def quebra(*args: object, **kwargs: object) -> NoReturn:
        raise RuntimeError("a coleta nao chegou a rodar")

    monkeypatch.setattr("apps.fundamentals.tasks.call_command", quebra)

    with pytest.raises(RuntimeError, match="nao chegou a rodar"):
        _importar_fundamentos()


def _comando_que_escreve(chamadas: list[str]) -> Any:
    def comando(name: str, *args: object, **kwargs: Any) -> None:
        chamadas.append(name)
        kwargs["stdout"].write(f"saida de {name}\n")

    return comando


def test_rf28_importar_devolve_a_saida_do_comando(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas: list[str] = []
    monkeypatch.setattr(
        "apps.fundamentals.tasks.call_command", _comando_que_escreve(chamadas)
    )

    assert _importar_fundamentos() == "saida de import_fundamentals\n"
    assert chamadas == ["import_fundamentals"]


def test_rf28_calcular_devolve_a_saida_do_comando(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas: list[str] = []
    monkeypatch.setattr(
        "apps.fundamentals.tasks.call_command", _comando_que_escreve(chamadas)
    )

    assert _calcular_fundamentos() == "saida de compute_fundamentals\n"
    assert chamadas == ["compute_fundamentals"]
