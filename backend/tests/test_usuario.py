"""F4-04: o usuario e o do projeto, e a organizacao e obrigatoria nas duas camadas.

As duas camadas sao testes separados de proposito. O gerente recusando `create_user` sem
organizacao nao diz nada sobre a coluna, e um `NOT NULL` no banco nao impede o gerente de
aceitar a chamada: uma verificacao so deixaria metade do requisito sem quem a reprove.

Onde ha banco, o acesso e por `django_db_blocker`, e nao pela marca `django_db` — a marca
conecta em `test_<nome>` e nao diz nada sobre o banco configurado.
"""

import pytest
from django.conf import settings
from django.db import connection, migrations
from django.db.migrations.loader import MigrationLoader
from pytest_django.plugin import DjangoDbBlocker

from apps.accounts.models import User

MIGRATION_INICIAL = ("accounts", "0001_esquemas_organization_user")


def test_auth_user_model_aponta_para_o_usuario_do_projeto() -> None:
    assert settings.AUTH_USER_MODEL == "accounts.User"


def test_a_0001_cria_o_usuario() -> None:
    """A criacao do usuario mora na primeira migration, e nao numa posterior.

    Trocar o `AUTH_USER_MODEL` depois de a tabela existir e a migracao cara que este
    bloco existe para evitar (D-39); uma `0003` que criasse o usuario deixaria qualquer
    banco ja migrado com o `auth.User` no lugar.
    """
    loader = MigrationLoader(None, ignore_no_migrations=True)

    assert MIGRATION_INICIAL in loader.disk_migrations
    criados = [
        operacao.name
        for operacao in loader.disk_migrations[MIGRATION_INICIAL].operations
        if isinstance(operacao, migrations.CreateModel)
    ]
    assert "User" in criados


def test_create_user_sem_organizacao_e_recusado_pelo_gerente() -> None:
    """Primeira camada: o gerente levanta antes de chegar ao banco."""
    with pytest.raises(ValueError):
        User.objects.create_user(email="sem-org@ruvor.test", name="Sem Organizacao")


def test_a_coluna_organization_id_e_not_null(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    """Segunda camada: o banco recusa, mesmo por caminho que nao passe pelo gerente."""
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT is_nullable FROM information_schema.columns"
            " WHERE table_schema = 'core' AND table_name = 'user'"
            " AND column_name = 'organization_id'"
        )
        linha = cursor.fetchone()

    assert linha is not None
    assert linha[0] == "NO"
