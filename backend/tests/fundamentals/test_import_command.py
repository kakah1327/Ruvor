"""`manage.py import_fundamentals`: a casca entrega o relatorio, converte a falha e recusa
`--full` com `--reconform` (RF-27).

`run_import_fundamentals` e substituido no ponto em que o comando o chama
(`apps.fundamentals.management.commands.import_fundamentals.run_import_fundamentals`) por
um substituto que registra os argumentos; o `sem_rede` do `conftest` garante que nada sai
para a rede se o patch falhar. O grupo mutuamente exclusivo se prova so aqui: rodar o
comando de verdade com argumentos errados poderia sair para a rede se o grupo estivesse
errado.
"""

from __future__ import annotations

import re
from io import StringIO
from typing import Any

import pytest
from django.core.management import CommandError, call_command

from apps.fundamentals.importer import (
    FileResult,
    FundamentalsImportFailed,
    ImportReport,
)

PATCH_POINT = (
    "apps.fundamentals.management.commands.import_fundamentals.run_import_fundamentals"
)


class FakeRun:
    """Substituto de `run_import_fundamentals`: registra cada chamada e devolve `report`,
    ou levanta `FundamentalsImportFailed` com ele se `fail`."""

    def __init__(self, report: ImportReport, *, fail: bool = False) -> None:
        self.report = report
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def __call__(self, source: object, **kwargs: Any) -> ImportReport:
        self.calls.append(kwargs)
        if self.fail:
            raise FundamentalsImportFailed(self.report)
        return self.report


def ok_report() -> ImportReport:
    return ImportReport(
        files=[FileResult(kind="dfp", year=2024, status="novo", size=10)],
        years=[],
        collected=True,
    )


def failed_report() -> ImportReport:
    return ImportReport(
        files=[FileResult(kind="dfp", year=2024, status="falhou", error="timeout")],
        years=[],
        collected=True,
    )


def test_rf27_comando_escreve_o_relatorio_em_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRun(ok_report())
    monkeypatch.setattr(PATCH_POINT, fake)
    stdout = StringIO()

    call_command("import_fundamentals", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(r"^dfp 2024: baixado, 10 bytes, novo$", saida, re.MULTILINE)
    assert re.search(r"^coleta: ", saida, re.MULTILINE)
    assert fake.calls == [{"full": False, "reconform": None}]


def test_rf27_falha_escreve_o_relatorio_e_vira_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRun(failed_report(), fail=True)
    monkeypatch.setattr(PATCH_POINT, fake)
    stdout = StringIO()

    with pytest.raises(CommandError, match=r"^coleta com falhas: dfp 2024$"):
        call_command("import_fundamentals", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(r"^dfp 2024: FALHOU \(timeout\)$", saida, re.MULTILINE)
    assert re.search(r"^coleta: 1 arquivos, .*, 1 falhos$", saida, re.MULTILINE)


def test_full_e_reconform_juntos_sao_recusados_sem_chamar_a_coleta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRun(ok_report())
    monkeypatch.setattr(PATCH_POINT, fake)

    with pytest.raises(CommandError, match=r"not allowed with argument"):
        call_command("import_fundamentals", "--full", "--reconform", stdout=StringIO())

    assert fake.calls == []


def test_full_chama_com_full(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeRun(ok_report())
    monkeypatch.setattr(PATCH_POINT, fake)

    call_command("import_fundamentals", "--full", stdout=StringIO())

    assert fake.calls == [{"full": True, "reconform": None}]


def test_reconform_com_ano_chama_com_a_lista_do_ano(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRun(ok_report())
    monkeypatch.setattr(PATCH_POINT, fake)

    call_command("import_fundamentals", "--reconform", "2024", stdout=StringIO())

    assert fake.calls == [{"full": False, "reconform": [2024]}]


def test_reconform_sem_ano_chama_com_lista_vazia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRun(ok_report())
    monkeypatch.setattr(PATCH_POINT, fake)

    call_command("import_fundamentals", "--reconform", stdout=StringIO())

    assert fake.calls == [{"full": False, "reconform": []}]
