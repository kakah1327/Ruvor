"""M4.2, T2: a tabela `core.api_key` (RF-01; V-01)."""

from __future__ import annotations

import pytest
from django.db import IntegrityError, connection, transaction

from apps.accounts.models import AccessEvent, ApiKey
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db

COLUNAS = {
    "id": "bigint",
    "user_id": "bigint",
    "name": "character varying",
    "prefix": "character varying",
    "secret_hash": "character varying",
    "scopes": "jsonb",
    "created_at": "timestamp with time zone",
    "last_used_at": "timestamp with time zone",
    "revoked_at": "timestamp with time zone",
}


def _chave(user_email: str, prefix: str) -> ApiKey:
    user = usuario(organizacao(user_email.split("@")[0]), user_email)
    return ApiKey.unscoped.create(
        user=user, name="n", prefix=prefix, secret_hash="0" * 64, scopes=["read"]
    )


def test_v01_as_colunas_da_tabela() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns"
            " WHERE table_schema = 'core' AND table_name = 'api_key'"
        )
        linhas = cursor.fetchall()
    assert {nome: tipo for nome, tipo, _ in linhas} == COLUNAS
    nulas = {nome for nome, _, nula in linhas if nula == "YES"}
    assert nulas == {"last_used_at", "revoked_at"}


def test_v01_o_prefix_e_unico_no_banco_pela_restricao_nomeada() -> None:
    _chave("a@a.test", "abcd1234")
    with pytest.raises(IntegrityError) as erro, transaction.atomic():
        _chave("b@b.test", "abcd1234")
    # o nome que o `unique=True` gera: e por ele que a criacao reconhece a colisao (T3)
    diag = getattr(erro.value.__cause__, "diag", None)
    assert getattr(diag, "constraint_name", None) == "api_key_prefix_key"


def test_os_dois_kind_novos_da_auditoria() -> None:
    assert AccessEvent.Kind.API_KEY_CREATED.value == "api_key_created"
    assert AccessEvent.Kind.API_KEY_REVOKED.value == "api_key_revoked"
