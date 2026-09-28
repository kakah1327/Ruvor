"""M2.1a, T5: os servicos de gestao de usuarios da organizacao (RF-14 a RF-18, RF-24;
V-07, V-09 a V-12 e V-18 da gestao).

A concorrencia do `last_admin` mora em `test_gestao_concorrente.py`, que precisa de
`transaction=True`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from apps.accounts import services
from apps.accounts.audit import record as record_real
from apps.accounts.errors import AccountError
from apps.accounts.models import AccessEvent, Organization, User
from tests.accounts.conftest import (
    SENHA,
    autenticado,
    chave,
    organizacao,
    requisicao,
    usuario,
)

pytestmark = pytest.mark.django_db

IP = "10.1.2.3"


class Falhou(Exception):
    pass


def _grava_e_falha(*args: Any, **kwargs: Any) -> AccessEvent:
    record_real(*args, **kwargs)
    raise Falhou


def _erro(chamada: Callable[[], object]) -> AccountError:
    with pytest.raises(AccountError) as info:
        chamada()
    return info.value


def _admin(org: Organization | None = None, email: str = "adm@acme.test") -> User:
    return usuario(org or organizacao(), email, role="admin")


def _entra(email: str, senha: str) -> str:
    request = requisicao()
    services.login(request, email=email, password=senha)
    return chave(request)


_SERVICOS: dict[str, Callable[[User], object]] = {
    "listar": lambda ator: services.list_users(ator),
    "criar": lambda ator: services.create_user(
        ator, email="novo@acme.test", name="Novo", role="member", ip=IP
    ),
    "alterar": lambda ator: services.update_user(
        ator, "alvo@acme.test", changes={"role": "admin"}, ip=IP
    ),
    "redefinir": lambda ator: services.reset_temporary_password(
        ator, "alvo@acme.test", ip=IP
    ),
}


# --- V-07 e V-09, quem pode gerir ------------------------------------------------------


@pytest.mark.parametrize("servico", sorted(_SERVICOS))
def test_v07_senha_provisoria_barra_a_gestao(servico: str) -> None:
    org = organizacao()
    usuario(org, "alvo@acme.test")
    ator = usuario(org, "adm@acme.test", role="admin", must_change_password=True)
    assert _erro(lambda: _SERVICOS[servico](ator)).code == "password_change_required"


def test_v07_depois_da_troca_a_gestao_responde() -> None:
    org = organizacao()
    ator = usuario(org, "adm@acme.test", role="admin", must_change_password=True)
    request = requisicao(session_key=_entra("adm@acme.test", SENHA))
    services.change_password(
        request, current_password=SENHA, new_password="nova-senha-longa-9"
    )
    assert services.list_users(ator)[0] == 1


@pytest.mark.parametrize(
    ("papel", "flag", "pessoal", "codigo"),
    [
        ("member", True, False, "password_change_required"),
        ("member", False, False, "permission_denied"),
        ("admin", False, True, "personal_organization"),
    ],
)
def test_v09_a_ordem_das_checagens(
    papel: str, flag: bool, pessoal: bool, codigo: str
) -> None:
    ator = usuario(
        organizacao(pessoal=pessoal),
        "ator@acme.test",
        role=papel,
        must_change_password=flag,
    )
    assert _erro(lambda: services.list_users(ator)).code == codigo


@pytest.mark.parametrize("servico", sorted(_SERVICOS))
def test_v09_member_nao_gere(servico: str) -> None:
    org = organizacao()
    usuario(org, "alvo@acme.test")
    ator = usuario(org, "membro@acme.test")
    assert _erro(lambda: _SERVICOS[servico](ator)).code == "permission_denied"


# --- V-10, isolamento ------------------------------------------------------------------


def test_v10_a_admin_so_ve_a_propria_organizacao() -> None:
    acme, outra = organizacao("acme"), organizacao("outra")
    ator = _admin(acme)
    usuario(acme, "b@acme.test")
    usuario(outra, "c@outra.test")

    total, usuarios = services.list_users(ator)

    assert total == 2
    assert [u.email for u in usuarios] == ["adm@acme.test", "b@acme.test"]


@pytest.mark.parametrize("servico", ["alterar", "redefinir"])
def test_v10_email_de_outra_organizacao_e_igual_a_inexistente(servico: str) -> None:
    acme, outra = organizacao("acme"), organizacao("outra")
    ator = _admin(acme)
    usuario(outra, "de-fora@outra.test")

    def chama(email: str) -> AccountError:
        if servico == "alterar":
            return _erro(
                lambda: services.update_user(
                    ator, email, changes={"role": "admin"}, ip=IP
                )
            )
        return _erro(lambda: services.reset_temporary_password(ator, email, ip=IP))

    de_fora, inexistente = chama("de-fora@outra.test"), chama("nao@existe.test")

    assert (de_fora.code, de_fora.message, de_fora.details) == (
        inexistente.code,
        inexistente.message,
        inexistente.details,
    )
    assert de_fora.code == "user_not_found"
    assert User.objects.get(email="de-fora@outra.test").role == "member"


# --- V-11, gestao ----------------------------------------------------------------------


def _todo_texto_dos_eventos() -> str:
    linhas = AccessEvent.objects.values_list(
        "kind", "email", "ip", "details", "actor_id", "target_id", "organization_id"
    )
    return json.dumps([list(linha) for linha in linhas], default=str)


def test_v11_criar_da_senha_provisoria_que_entra_e_exige_troca() -> None:
    ator = _admin()
    user, senha = services.create_user(
        ator, email=" Novo@Acme.Test", name="Novo", role="member", ip=IP
    )

    assert user.email == "novo@acme.test"
    assert user.organization == ator.organization
    assert user.must_change_password is True
    assert services.user_body(user)["must_change_password"] is True
    services.login(requisicao(), email="novo@acme.test", password=senha)
    assert senha not in _todo_texto_dos_eventos()

    (evento,) = AccessEvent.objects.filter(kind="user_created")
    assert (evento.actor, evento.target, evento.organization) == (
        ator,
        user,
        ator.organization,
    )
    assert (evento.email, evento.ip, evento.details) == (
        "novo@acme.test",
        IP,
        {"role": "member"},
    )


def test_v11_criar_email_de_qualquer_organizacao_e_email_taken() -> None:
    usuario(organizacao("outra"), "ja@existe.test")
    ator = _admin()
    erro = _erro(
        lambda: services.create_user(
            ator, email="JA@existe.test", name="X", role="member", ip=IP
        )
    )
    assert erro.code == "email_taken"


def test_v11_criar_com_papel_invalido() -> None:
    erro = _erro(
        lambda: services.create_user(
            _admin(), email="n@acme.test", name="N", role="dono", ip=IP
        )
    )
    assert erro.code == "invalid_parameter"
    assert list(erro.details["fields"]) == ["role"]


def test_v11_alterar_papel_grava_antes_e_depois() -> None:
    ator = _admin()
    alvo = usuario(ator.organization, "alvo@acme.test")

    user = services.update_user(
        ator, "ALVO@acme.test", changes={"role": "admin"}, ip=IP
    )

    assert user.role == "admin"
    (evento,) = AccessEvent.objects.filter(kind="user_updated")
    assert (evento.actor, evento.target, evento.organization, evento.email) == (
        ator,
        alvo,
        ator.organization,
        "alvo@acme.test",
    )
    assert evento.details == {"role": {"before": "member", "after": "admin"}}


def test_v11_alterar_sem_mudanca_nao_grava_evento() -> None:
    ator = _admin()
    usuario(ator.organization, "alvo@acme.test")
    services.update_user(ator, "alvo@acme.test", changes={"role": "member"}, ip=IP)
    assert not AccessEvent.objects.filter(kind="user_updated").exists()


@pytest.mark.parametrize(
    ("changes", "campo"),
    [
        ({"email": "x@y.test"}, "email"),
        ({"role": "dono"}, "role"),
        ({"is_active": "sim"}, "is_active"),
    ],
)
def test_v11_alterar_campo_invalido(changes: dict[str, object], campo: str) -> None:
    ator = _admin()
    usuario(ator.organization, "alvo@acme.test")
    erro = _erro(
        lambda: services.update_user(ator, "alvo@acme.test", changes=changes, ip=IP)
    )
    assert erro.code == "invalid_parameter"
    assert list(erro.details["fields"]) == [campo]


def test_v11_desativar_e_reativar_nao_ressuscita_a_sessao() -> None:
    ator = _admin()
    usuario(ator.organization, "alvo@acme.test")
    sessao = _entra("alvo@acme.test", SENHA)
    assert autenticado(sessao)

    services.update_user(ator, "alvo@acme.test", changes={"is_active": False}, ip=IP)
    assert not autenticado(sessao)
    services.update_user(ator, "alvo@acme.test", changes={"is_active": True}, ip=IP)

    assert not autenticado(sessao)
    eventos = AccessEvent.objects.filter(kind="user_updated").order_by("id")
    assert [e.details for e in eventos] == [
        {"is_active": {"before": True, "after": False}},
        {"is_active": {"before": False, "after": True}},
    ]


@pytest.mark.parametrize(
    "changes", [{"role": "member"}, {"is_active": False}], ids=["rebaixar", "desativar"]
)
def test_v11_last_admin_sobre_a_unica(changes: dict[str, object]) -> None:
    ator = _admin()
    outra = _admin(ator.organization, "outra@acme.test")
    User.objects.filter(pk=outra.pk).update(is_active=False)

    erro = _erro(
        lambda: services.update_user(ator, "adm@acme.test", changes=changes, ip=IP)
    )

    assert erro.code == "last_admin"
    ator.refresh_from_db()
    assert (ator.role, ator.is_active) == ("admin", True)


def test_v11_last_admin_nao_barra_quando_ha_outra() -> None:
    ator = _admin()
    _admin(ator.organization, "outra@acme.test")
    services.update_user(ator, "outra@acme.test", changes={"role": "member"}, ip=IP)
    assert User.objects.get(email="outra@acme.test").role == "member"


def test_v11_redefinir_a_propria_senha_e_use_password_route() -> None:
    ator = _admin()
    erro = _erro(
        lambda: services.reset_temporary_password(ator, "adm@acme.test", ip=IP)
    )
    assert erro.code == "use_password_route"


def test_v11_redefinir_da_senha_nova_derruba_sessoes_e_grava() -> None:
    ator = _admin()
    alvo = usuario(ator.organization, "alvo@acme.test")
    sessao = _entra("alvo@acme.test", SENHA)

    user, senha = services.reset_temporary_password(ator, "alvo@acme.test", ip=IP)

    assert user.must_change_password is True
    assert not autenticado(sessao)
    services.login(requisicao(), email="alvo@acme.test", password=senha)
    assert senha not in _todo_texto_dos_eventos()
    (evento,) = AccessEvent.objects.filter(kind="temporary_password_reset")
    assert (evento.actor, evento.target, evento.organization, evento.details) == (
        ator,
        alvo,
        ator.organization,
        {},
    )


def test_v18_redefinir_evento_e_mudanca_na_mesma_transacao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ator = _admin()
    alvo = usuario(ator.organization, "alvo@acme.test")
    sessao = _entra("alvo@acme.test", SENHA)
    antes = AccessEvent.objects.count()
    monkeypatch.setattr(services, "record", _grava_e_falha)

    with pytest.raises(Falhou):
        services.reset_temporary_password(ator, "alvo@acme.test", ip=IP)

    alvo.refresh_from_db()
    assert alvo.check_password(SENHA)
    assert alvo.must_change_password is False
    assert autenticado(sessao)
    assert AccessEvent.objects.count() == antes


# --- V-12, paginacao -------------------------------------------------------------------


def test_v12_paginacao() -> None:
    ator = _admin()
    for n in range(4):
        usuario(ator.organization, f"u{n}@acme.test")

    total, pagina = services.list_users(ator, limit=2, offset=1)

    assert total == 5
    assert [u.email for u in pagina] == ["u0@acme.test", "u1@acme.test"]


@pytest.mark.parametrize(
    ("limit", "offset", "parametro"),
    [(0, 0, "limit"), (101, 0, "limit"), (10, -1, "offset")],
)
def test_v12_parametros_fora_da_faixa(limit: int, offset: int, parametro: str) -> None:
    erro = _erro(lambda: services.list_users(_admin(), limit=limit, offset=offset))
    assert erro.code == "invalid_parameter"
    assert erro.details == {"parameter": parametro}


def test_v18_criar_evento_e_mudanca_na_mesma_transacao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ator = _admin()
    monkeypatch.setattr(services, "record", _grava_e_falha)

    with pytest.raises(Falhou):
        services.create_user(
            ator, email="novo@acme.test", name="Novo", role="member", ip=IP
        )

    assert not User.objects.filter(email="novo@acme.test").exists()
    assert not AccessEvent.objects.exists()


def test_v18_alterar_evento_e_mudanca_na_mesma_transacao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ator = _admin()
    alvo = usuario(ator.organization, "alvo@acme.test")
    monkeypatch.setattr(services, "record", _grava_e_falha)

    with pytest.raises(Falhou):
        services.update_user(ator, "alvo@acme.test", changes={"role": "admin"}, ip=IP)

    alvo.refresh_from_db()
    assert alvo.role == "member"
    assert not AccessEvent.objects.exists()


def test_v09_member_com_corpo_invalido_recebe_permission_denied() -> None:
    org = organizacao()
    usuario(org, "alvo@acme.test")
    ator = usuario(org, "membro@acme.test")
    erro = _erro(
        lambda: services.update_user(
            ator, "alvo@acme.test", changes={"email": "x@y.test"}, ip=IP
        )
    )
    assert erro.code == "permission_denied"
