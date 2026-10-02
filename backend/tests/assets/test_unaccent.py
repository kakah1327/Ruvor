"""V-01 do M1.7: a extensao `unaccent` existe no banco, pela `assets/0004` (RF-01).

O banco de teste nasce do `migrate` num banco vazio (o pytest-django roda as migrations), e
nele `pg_extension` tem `unaccent`. Voltar a `assets 0003` a remove; o `migrate` seguinte a
recria. Migrar dentro do teste pede `transaction=True` -- por isso a marca `TRANSACIONAL` e
a fixture `banco_limpo` (`tests/api/migracao.py`). O `finally` reaplica a migration e recria
a extensao se ela faltar: uma falha no meio nao deixa o banco de teste sem ela, o que
derrubaria a busca de todo teste seguinte.
"""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.db import connection

from tests.api.migracao import TRANSACIONAL, banco_limpo  # noqa: F401

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]


def _tem_unaccent() -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'unaccent'")
        return cursor.fetchone() is not None


def test_a_migration_cria_e_a_volta_remove_a_extensao() -> None:
    assert _tem_unaccent()
    try:
        call_command("migrate", "assets", "0003", verbosity=0)
        assert not _tem_unaccent()

        call_command("migrate", "assets", verbosity=0)
        assert _tem_unaccent()
    finally:
        call_command("migrate", "assets", verbosity=0)
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
