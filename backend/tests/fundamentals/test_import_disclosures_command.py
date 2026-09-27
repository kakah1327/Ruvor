"""`manage.py import_disclosures`: a casca repassa as opcoes, entrega o relatorio, converte a
falha e recusa `--full` com `--reconform` (RF-08, RF-09).

`run_import_disclosures` e `CvmClient` sao substituidos no ponto em que o comando os chama
(o nome global de `apps.fundamentals.management.commands.import_disclosures`); o `sem_rede`
do `conftest` garante que nada sai para a rede se o patch falhar. Tudo passa pela casca
(`call_command`): e o que prova que `--full` chega como `full=True`.
"""

from __future__ import annotations

import re
from io import StringIO
from typing import Any

import pytest
from django.core.management import CommandError, call_command

from apps.fundamentals.disclosures_importer import (
    DisclosuresImportFailed,
    DisclosuresReport,
    DisclosureYearResult,
)
from apps.fundamentals.importer import FileResult

MODULE = "apps.fundamentals.management.commands.import_disclosures"


class FakeClient:
    """Substituto de `CvmClient`: so marca que foi ele quem chegou a coleta."""


class FakeRun:
    """Substituto de `run_import_disclosures`: registra cada chamada e devolve `report`,
    ou levanta `DisclosuresImportFailed` com ele se `fail`."""

    def __init__(self, report: DisclosuresReport, *, fail: bool = False) -> None:
        self.report = report
        self.fail = fail
        self.sources: list[object] = []
        self.calls: list[dict[str, Any]] = []

    def __call__(self, source: object, **kwargs: Any) -> DisclosuresReport:
        self.sources.append(source)
        self.calls.append(kwargs)
        if self.fail:
            raise DisclosuresImportFailed(self.report)
        return self.report


def ok_report() -> DisclosuresReport:
    return DisclosuresReport(
        files=[FileResult(kind="ipe", year=2025, status="novo", size=10)],
        years=[
            DisclosureYearResult(
                label="ano", year=2025, companies=3, created=5, updated=1, removed=2
            )
        ],
        collected=True,
    )


def failed_report() -> DisclosuresReport:
    return DisclosuresReport(
        files=[
            FileResult(kind="ipe", year=2024, status="falhou", error="timeout"),
            FileResult(kind="ipe", year=2025, status="novo", size=10),
        ],
        years=[
            DisclosureYearResult(
                label="ano",
                year=2025,
                companies=2,
                created=4,
                failures=[("4170", "ValueError: quebrou")],
            ),
            DisclosureYearResult(label="novas", year=2023, error="BadZipFile: ruim"),
        ],
        collected=True,
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    fake = FakeClient()
    monkeypatch.setattr(f"{MODULE}.CvmClient", lambda: fake)
    return fake


def install(monkeypatch: pytest.MonkeyPatch, fake: FakeRun) -> FakeRun:
    monkeypatch.setattr(f"{MODULE}.run_import_disclosures", fake)
    return fake


def test_rf09_comando_escreve_o_relatorio_em_stdout(
    monkeypatch: pytest.MonkeyPatch, client: FakeClient
) -> None:
    fake = install(monkeypatch, FakeRun(ok_report()))
    stdout = StringIO()

    call_command("import_disclosures", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(r"^ipe 2025: baixado, 10 bytes, novo$", saida, re.MULTILINE)
    assert re.search(
        r"^ano 2025: 3 companhias, 5 criados, 1 atualizados, 2 removidos, 0 falhos$",
        saida,
        re.MULTILINE,
    )
    assert re.search(
        r"^coleta: 1 arquivos, 1 novos, 0 inalterados, 0 nao modificados, "
        r"0 ausentes, 0 falhos$",
        saida,
        re.MULTILINE,
    )
    assert fake.calls == [{"full": False, "reconform": None}]
    assert fake.sources == [client]


def test_rf09_falha_escreve_o_relatorio_e_vira_command_error(
    monkeypatch: pytest.MonkeyPatch, client: FakeClient
) -> None:
    install(monkeypatch, FakeRun(failed_report(), fail=True))
    stdout = StringIO()

    with pytest.raises(
        CommandError,
        match=r"^coleta com falhas: ipe 2024, ano 2025 4170, novas 2023$",
    ) as caught:
        call_command("import_disclosures", stdout=stdout)

    assert caught.value.returncode == 1
    saida = stdout.getvalue()
    assert re.search(r"^ipe 2024: FALHOU \(timeout\)$", saida, re.MULTILINE)
    assert re.search(
        r"^ano 2025: FALHOU 4170 \(ValueError: quebrou\)$", saida, re.MULTILINE
    )
    assert re.search(r"^novas 2023: FALHOU \(BadZipFile: ruim\)$", saida, re.MULTILINE)
    assert re.search(r"^coleta: 2 arquivos, .*, 1 falhos$", saida, re.MULTILINE)


def test_rf08_full_e_reconform_juntos_sao_recusados_sem_chamar_a_coleta(
    monkeypatch: pytest.MonkeyPatch, client: FakeClient
) -> None:
    fake = install(monkeypatch, FakeRun(ok_report()))

    with pytest.raises(CommandError, match=r"not allowed with argument"):
        call_command("import_disclosures", "--full", "--reconform", stdout=StringIO())

    assert fake.calls == []


def test_rf08_full_chama_com_full(
    monkeypatch: pytest.MonkeyPatch, client: FakeClient
) -> None:
    fake = install(monkeypatch, FakeRun(ok_report()))

    call_command("import_disclosures", "--full", stdout=StringIO())

    assert fake.calls == [{"full": True, "reconform": None}]


def test_rf08_reconform_sem_ano_chama_com_lista_vazia(
    monkeypatch: pytest.MonkeyPatch, client: FakeClient
) -> None:
    fake = install(monkeypatch, FakeRun(ok_report()))

    call_command("import_disclosures", "--reconform", stdout=StringIO())

    assert fake.calls == [{"full": False, "reconform": []}]


def test_rf08_reconform_com_dois_anos_chama_com_a_lista(
    monkeypatch: pytest.MonkeyPatch, client: FakeClient
) -> None:
    fake = install(monkeypatch, FakeRun(ok_report()))

    call_command("import_disclosures", "--reconform", "2024", "2025", stdout=StringIO())

    assert fake.calls == [{"full": False, "reconform": [2024, 2025]}]
