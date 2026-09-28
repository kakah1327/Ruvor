"""O banco dos testes `transaction=True`: a marca e a limpeza.

O `flush` do Django, que o pytest-django roda na saida de cada teste `transaction=True`, nao
serve neste repositorio (medido na T6 do M1.6a): a introspeccao so enxerga as quatro tabelas de
`auth` e `contenttypes` -- as com esquema no `db_table` ficam de fora --, e o `TRUNCATE` delas
sem `CASCADE` falha pela FK de `core.user_groups`. Por isso:

- **`TRANSACIONAL`** e a marca: com `available_apps`, o Django trunca `auth` e `contenttypes`
  com `CASCADE` e o `flush` passa; e reemite o `post_migrate` na entrada, que recria tipos de
  conteudo e permissoes.
- **`banco_limpo`**, de funcao, pede `transactional_db` -- por isso a desmontagem dela roda
  **antes** da do Django. Na desmontagem, `TRUNCATE` de **toda** tabela dos esquemas `core`,
  `bronze`, `silver` e `gold` (a lista sai de `pg_tables`), `RESTART IDENTITY CASCADE`, numa
  instrucao so; depois recria a organizacao `ruvor` e o `IBOV` pelas funcoes das migrations.
  O banco sai de cada teste como a migration o deixou.

**Todo teste `transaction=True` do repositorio usa as duas.** A forma do import:

    from tests.api.migracao import TRANSACIONAL, banco_limpo  # noqa: F401

e a fixture e pedida por `pytest.mark.usefixtures("banco_limpo")`, nunca como parametro
(seria F811).

As funcoes das migrations sao chamadas com o registro de apps corrente, pelo modulo que o
`importlib` devolve -- o precedente de `tests/risk/test_tasks.py`.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator

import pytest
from django.apps import apps as django_apps
from django.conf import settings
from django.db import connection

MIGRATION_ORGANIZACAO = "apps.accounts.migrations.0002_marco1_organization"
MIGRATION_IBOVESPA = "apps.assets.migrations.0002_ibovespa"
ESQUEMAS = ("core", "bronze", "silver", "gold")

TRANSACIONAL = pytest.mark.django_db(
    transaction=True, available_apps=list(settings.INSTALLED_APPS)
)


def _trunca_esquemas() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = ANY(%s)",
            [list(ESQUEMAS)],
        )
        tabelas = [f'"{esquema}"."{tabela}"' for esquema, tabela in cursor.fetchall()]
        cursor.execute(f"TRUNCATE {', '.join(tabelas)} RESTART IDENTITY CASCADE")


def _recria_dados_de_migration() -> None:
    importlib.import_module(MIGRATION_ORGANIZACAO).cria_organizacao_do_marco1(
        django_apps, None
    )
    importlib.import_module(MIGRATION_IBOVESPA).cria_ibovespa(django_apps, None)


@pytest.fixture
def banco_limpo(transactional_db: None) -> Iterator[None]:
    yield
    _trunca_esquemas()
    _recria_dados_de_migration()
