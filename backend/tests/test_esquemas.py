"""F4-01 e F4-02: os quatro esquemas existem, e as tabelas sao a lista fechada.

Sao treze tabelas. O F4 criou nove — as duas do `core`, as duas de juncao do usuario e
as cinco do Django no `public` —, e o M1.1 acrescentou as quatro do catalogo de ativos:
tres na `bronze` (`collection_run`, `b3_company_listing`, `b3_company_detail`) e uma na
`silver` (`asset`).

Usa `django_db_blocker` e nao a marca `django_db` pelo mesmo motivo do
`test_conexao_com_o_banco`: a marca conecta em `test_<nome>`, um banco que o proprio
pytest-django cria e migra, e por isso nao diz nada sobre o banco configurado — que e
onde os esquemas precisam existir de verdade. Inspeciona o banco da conexao corrente —
configurado quando isolado, `test_<nome>` na suite inteira, porque os testes de
`tests/assets/` vem antes e a marca deles renomeia a conexao ate o fim da sessao.

A comparacao e de conjunto INTEIRO, nunca de amostra: `assertIn` aprovaria com uma
tabela de dominio nascida no `public`, que e exatamente o que F4-02 proibe.

Esta lista e a fonte da lista fechada. Ela aparece na forma literal `esquema.tabela`
porque o criterio de aceite a extrai deste arquivo e a confronta com o banco.
"""

from django.db import connection
from pytest_django.plugin import DjangoDbBlocker

ESQUEMAS = {"core", "bronze", "silver", "gold"}

TABELAS = {
    "bronze.b3_company_detail",
    "bronze.b3_company_listing",
    "bronze.collection_run",
    "core.organization",
    "core.user",
    "core.user_groups",
    "core.user_user_permissions",
    "public.auth_group",
    "public.auth_group_permissions",
    "public.auth_permission",
    "public.django_content_type",
    "public.django_migrations",
    "silver.asset",
}


def test_os_quatro_esquemas_existem(django_db_blocker: DjangoDbBlocker) -> None:
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT schema_name FROM information_schema.schemata"
            " WHERE schema_name IN ('core', 'bronze', 'silver', 'gold')"
        )
        encontrados = {linha[0] for linha in cursor.fetchall()}

    assert encontrados == ESQUEMAS


def test_o_conjunto_de_tabelas_e_a_lista_fechada(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT schemaname || '.' || tablename FROM pg_tables"
            " WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
        )
        encontradas = {linha[0] for linha in cursor.fetchall()}

    assert encontradas == TABELAS
