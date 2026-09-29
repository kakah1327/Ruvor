"""M4.2, T3: os servicos de chave e a revogacao da conta mudada (RF-02 a RF-05, RF-09, RF-10;
V-02 a V-05 e V-12).

Todo servico e chamado **sem contexto de organizacao**: eles se escopam sozinhos (RF-13).
A concorrencia do teto mora em `test_api_key_concorrente.py`.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import pytest
from django.db import IntegrityError

from apps.accounts import services
from apps.accounts.audit import record as record_real
from apps.accounts.errors import AccountError
from apps.accounts.models import AccessEvent, ApiKey, User
from tests.accounts.conftest import SENHA, chave, organizacao, requisicao, usuario

pytestmark = pytest.mark.django_db

IP = "10.9.8.7"
SEGREDO = re.compile(r"rvr_[0-9a-f]{8}_[A-Za-z0-9_-]{43}")


class Falhou(Exception):
    pass


def _grava_e_falha(*args: Any, **kwargs: Any) -> AccessEvent:
    record_real(*args, **kwargs)
    raise Falhou


@pytest.fixture
def ana() -> User:
    return usuario(organizacao("acme", pessoal=False), "ana@acme.test", role="admin")


def _ativas(user: User) -> list[str]:
    return sorted(
        ApiKey.unscoped.filter(user=user, revoked_at__isnull=True).values_list(
            "prefix", flat=True
        )
    )


def _eventos(kind: str) -> list[AccessEvent]:
    return list(AccessEvent.objects.filter(kind=kind).order_by("id"))


# --- V-02, V-03: criar --------------------------------------------------------------------


def test_v02_o_segredo_tem_o_formato_e_o_banco_guarda_so_o_hash(ana: User) -> None:
    key, segredo = services.create_api_key(ana, name="minha", ip=IP)
    assert SEGREDO.fullmatch(segredo)
    assert segredo.startswith(f"rvr_{key.prefix}_")
    linha = ApiKey.unscoped.get(pk=key.pk)
    assert linha.secret_hash == hashlib.sha256(segredo.encode()).hexdigest()
    assert linha.scopes == ["read"]

    # o segredo nao aparece em coluna nenhuma da chave nem da auditoria
    colunas = [
        str(v) for v in ApiKey.unscoped.filter(pk=key.pk).values().get().values()
    ]
    eventos = [
        json.dumps(e, default=str)
        for e in AccessEvent.objects.values(
            "kind", "email", "details", "ip", "actor_id", "target_id"
        )
    ]
    assert not any(segredo in texto for texto in colunas + eventos)


def test_v03_criar_grava_o_evento_coluna_a_coluna(ana: User) -> None:
    key, _ = services.create_api_key(ana, name="  minha chave  ", ip=IP)
    assert key.name == "minha chave"
    (evento,) = _eventos("api_key_created")
    assert evento.actor_id == ana.pk
    assert evento.target_id is None
    assert evento.organization_id == ana.organization_id
    assert evento.email == ana.email
    assert evento.ip == IP
    assert evento.details == {"prefix": key.prefix, "name": "minha chave"}


@pytest.mark.parametrize("nome", ["", "   ", "x" * 61, "  " + "x" * 61 + "  "])
def test_v03_nome_invalido_e_invalid_parameter(ana: User, nome: str) -> None:
    with pytest.raises(AccountError) as erro:
        services.create_api_key(ana, name=nome, ip=IP)
    assert erro.value.code == "invalid_parameter"
    assert list(erro.value.details["fields"]) == ["name"]
    assert _ativas(ana) == []


def test_v03_nome_de_60_depois_de_aparado_passa(ana: User) -> None:
    key, _ = services.create_api_key(ana, name="  " + "x" * 60 + "  ", ip=IP)
    assert key.name == "x" * 60


def test_v03_a_decima_primeira_ativa_e_api_key_limit(ana: User) -> None:
    for n in range(services.MAX_ACTIVE_KEYS):
        services.create_api_key(ana, name=f"k{n}", ip=IP)
    with pytest.raises(AccountError) as erro:
        services.create_api_key(ana, name="demais", ip=IP)
    assert erro.value.code == "api_key_limit"
    assert len(_ativas(ana)) == services.MAX_ACTIVE_KEYS


def test_v03_revogada_libera_vaga(ana: User) -> None:
    keys = [services.create_api_key(ana, name=f"k{n}", ip=IP)[0] for n in range(10)]
    services.revoke_api_key(ana, keys[0].prefix, ip=IP)
    services.create_api_key(ana, name="nova", ip=IP)
    assert len(_ativas(ana)) == 10


def test_v03_o_prefix_que_colide_e_gerado_de_novo(
    ana: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    existente, _ = services.create_api_key(ana, name="velha", ip=IP)
    prefixos = iter([existente.prefix, "0badcafe"])
    monkeypatch.setattr("secrets.token_hex", lambda n: next(prefixos))
    key, segredo = services.create_api_key(ana, name="nova", ip=IP)
    assert key.prefix == "0badcafe"
    assert segredo.startswith("rvr_0badcafe_")
    assert len(_eventos("api_key_created")) == 2


def test_v03_cinco_colisoes_sobem_o_integrity_error(
    ana: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    existente, _ = services.create_api_key(ana, name="velha", ip=IP)
    monkeypatch.setattr("secrets.token_hex", lambda n: existente.prefix)
    with pytest.raises(IntegrityError):
        services.create_api_key(ana, name="nova", ip=IP)
    assert _ativas(ana) == [existente.prefix]


def test_v03_criar_e_transacional(ana: User, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(services, "record", _grava_e_falha)
    with pytest.raises(Falhou):
        services.create_api_key(ana, name="minha", ip=IP)
    assert _ativas(ana) == []
    assert _eventos("api_key_created") == []


# --- V-04: listar e isolar ----------------------------------------------------------------


def test_v04_lista_so_as_ativas_de_quem_pede_da_mais_nova(ana: User) -> None:
    bia = usuario(ana.organization, "bia@acme.test")
    k1, _ = services.create_api_key(ana, name="1", ip=IP)
    k2, _ = services.create_api_key(ana, name="2", ip=IP)
    k3, _ = services.create_api_key(ana, name="3", ip=IP)
    services.create_api_key(bia, name="da bia", ip=IP)
    services.revoke_api_key(ana, k2.prefix, ip=IP)
    assert [k.prefix for k in services.list_api_keys(ana)] == [k3.prefix, k1.prefix]
    assert services.api_key_body(k1) == {
        "prefix": k1.prefix,
        "name": "1",
        "scopes": ["read"],
        "created_at": k1.created_at,
        "last_used_at": None,
    }


# --- V-05: revogar ------------------------------------------------------------------------


def test_v05_revogar_grava_revoked_at_e_o_evento(ana: User) -> None:
    key, _ = services.create_api_key(ana, name="minha", ip=IP)
    services.revoke_api_key(ana, key.prefix, ip=IP)
    assert ApiKey.unscoped.get(pk=key.pk).revoked_at is not None
    (evento,) = _eventos("api_key_revoked")
    assert evento.actor_id == ana.pk
    assert evento.target_id is None
    assert evento.ip == IP
    assert evento.details == {"prefix": key.prefix, "via": "owner"}


def test_v05_de_outra_pessoa_revogada_ou_inexistente_e_o_mesmo_not_found(
    ana: User,
) -> None:
    bia = usuario(ana.organization, "bia@acme.test")
    de_outra, _ = services.create_api_key(bia, name="da bia", ip=IP)
    revogada, _ = services.create_api_key(ana, name="velha", ip=IP)
    services.revoke_api_key(ana, revogada.prefix, ip=IP)

    corpos = []
    for prefix in (de_outra.prefix, revogada.prefix, "deadbeef"):
        with pytest.raises(AccountError) as erro:
            services.revoke_api_key(ana, prefix, ip=IP)
        corpos.append((erro.value.code, erro.value.message, erro.value.details))
    assert corpos[0] == corpos[1] == corpos[2]
    assert corpos[0][0] == "api_key_not_found"
    assert _ativas(bia) == [de_outra.prefix]


# --- V-12: a conta mudada revoga as chaves ------------------------------------------------


@pytest.fixture
def alvo(ana: User) -> User:
    return usuario(ana.organization, "alvo@acme.test")


def test_v12_desativar_revoga_e_reativar_nao_devolve(ana: User, alvo: User) -> None:
    k1, _ = services.create_api_key(alvo, name="1", ip=IP)
    k2, _ = services.create_api_key(alvo, name="2", ip=IP)
    services.update_user(ana, alvo.email, changes={"is_active": False}, ip=IP)
    assert _ativas(alvo) == []
    services.update_user(ana, alvo.email, changes={"is_active": True}, ip=IP)
    assert _ativas(alvo) == []

    eventos = _eventos("api_key_revoked")
    assert [e.details for e in eventos] == [
        {"prefix": k1.prefix, "via": "deactivation"},
        {"prefix": k2.prefix, "via": "deactivation"},
    ]
    assert {(e.actor_id, e.target_id, e.email, e.ip) for e in eventos} == {
        (ana.pk, alvo.pk, alvo.email, IP)
    }


def test_v12_redefinir_a_senha_provisoria_revoga(ana: User, alvo: User) -> None:
    key, _ = services.create_api_key(alvo, name="1", ip=IP)
    services.reset_temporary_password(ana, alvo.email, ip=IP)
    assert _ativas(alvo) == []
    (evento,) = _eventos("api_key_revoked")
    assert evento.details == {"prefix": key.prefix, "via": "temporary_password_reset"}


def test_v12_mudar_so_o_papel_nao_revoga(ana: User, alvo: User) -> None:
    key, _ = services.create_api_key(alvo, name="1", ip=IP)
    services.update_user(ana, alvo.email, changes={"role": "admin"}, ip=IP)
    assert _ativas(alvo) == [key.prefix]


def test_v12_trocar_a_propria_senha_nao_revoga(alvo: User) -> None:
    key, _ = services.create_api_key(alvo, name="1", ip=IP)
    request = requisicao()
    services.login(request, email=alvo.email, password=SENHA)
    chave(request)
    services.change_password(
        request, current_password=SENHA, new_password="outra-senha-bem-longa-5"
    )
    assert _ativas(alvo) == [key.prefix]


def test_v12_desativar_e_transacional(
    ana: User, alvo: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    key, _ = services.create_api_key(alvo, name="1", ip=IP)
    monkeypatch.setattr(services, "record", _grava_e_falha)
    with pytest.raises(Falhou):
        services.update_user(ana, alvo.email, changes={"is_active": False}, ip=IP)
    alvo.refresh_from_db()
    assert alvo.is_active is True
    assert _ativas(alvo) == [key.prefix]
    assert _eventos("api_key_revoked") == []
