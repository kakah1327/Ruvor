"""`manage.py import_assets`: a casca entrega o relatorio e converte a falha (RF-13).

O `B3Client` e substituido no ponto em que o comando o importa
(`apps.assets.management.commands.import_assets.B3Client`) por uma `FakeSource`; o
`sem_rede` do `conftest` garante que nada sai para a rede se o patch falhar.
"""

from __future__ import annotations

import re
from io import StringIO
from typing import Any

import pytest
from django.core.management import CommandError, call_command

from tests.assets.conftest import FakeSource, fixture_json

pytestmark = pytest.mark.django_db

PATCH_POINT = "apps.assets.management.commands.import_assets.B3Client"


def fake_source_factory(source: FakeSource) -> Any:
    def factory(*args: object, **kwargs: object) -> FakeSource:
        return source

    return factory


def test_rf13_comando_escreve_o_relatorio_em_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = FakeSource(
        pages=[[fixture_json("listing_item_PETR")]],
        details={"9512": fixture_json("detail_PETR")},
    )
    monkeypatch.setattr(PATCH_POINT, fake_source_factory(source))
    stdout = StringIO()

    call_command("import_assets", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(r"^listagem: 1 companhias em 1 paginas$", saida, re.MULTILINE)
    assert re.search(r"^acoes conformadas: 2 \(criadas 2, ", saida, re.MULTILINE)


def test_rf13_falha_da_coleta_vira_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = FakeSource(
        pages=[[fixture_json("listing_item_PETR")]],
        details={},
        fail_on="9512",
    )
    monkeypatch.setattr(PATCH_POINT, fake_source_factory(source))

    with pytest.raises(CommandError, match=r"^B3ClientError: fonte falsa"):
        call_command("import_assets", stdout=StringIO())
