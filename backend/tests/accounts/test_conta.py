"""M2.1a, T4: os servicos da conta -- cadastro, entrada, saida, troca de senha e o bloqueio
por (e-mail, IP) (RF-08 a RF-13, RF-22b, RF-24, RF-28; V-05, V-06, V-08, V-16 e V-18 dos
eventos da conta).

Os servicos recebem um `HttpRequest` com sessao real (`requisicao()` do `conftest`). Os
casos transacionais substituem `services.record` -- o nome global que os servicos chamam --
por um duplo que grava o evento e **depois** levanta: sem o `atomic`, o evento ou a mudanca
ficariam gravados.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from django.contrib.auth.password_validation import UserAttributeSimilarityValidator
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.db import IntegrityError

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


class Falhou(Exception):
    pass


def _grava_e_falha(*args: Any, **kwargs: Any) -> AccessEvent:
    record_real(*args, **kwargs)
    raise Falhou


def _erro(chamada: Callable[[], object]) -> AccountError:
    with pytest.raises(AccountError) as info:
        chamada()
    return info.value


def _cadastra(email: str = "Nova@Pessoa.Test", **extra: str) -> tuple[User, str]:
    request = requisicao()
    user = services.signup(
        request,
        email=email,
        name=extra.get("name", "Nova Pessoa"),
        password=extra.get("password", SENHA),
    )
    return user, chave(request)


def _eventos(kind: str) -> list[AccessEvent]:
    return list(AccessEvent.objects.filter(kind=kind).order_by("id"))


# --- V-05, cadastro --------------------------------------------------------------------


def test_v05_cadastro_cria_organizacao_pessoal_admin_e_sessao() -> None:
    user, key = _cadastra()

    assert user.email == "nova@pessoa.test"
    assert user.role == "admin"
    org = user.organization
    assert org.is_personal is True
    assert org.name == "Nova Pessoa"
    assert org.slug.startswith("pessoal-")
    assert list(org.users.all()) == [user]
    assert autenticado(key)
    assert services.me_body(user) == {
        "email": "nova@pessoa.test",
        "name": "Nova Pessoa",
        "role": "admin",
        "must_change_password": False,
        "is_staff": False,
        "organization": {"name": "Nova Pessoa", "slug": org.slug, "is_personal": True},
    }


def test_v05_cadastro_grava_signup() -> None:
    user, _ = _cadastra()
    (evento,) = _eventos("signup")
    assert evento.actor == user
    assert evento.target is None
    assert evento.organization == user.organization
    assert evento.email == "nova@pessoa.test"
    assert evento.ip == "127.0.0.1"
    assert evento.details == {}


def test_v05_email_repetido_em_outra_caixa_e_email_taken() -> None:
    _cadastra("ana@x.test")
    organizacoes = Organization.objects.count()

    erro = _erro(lambda: _cadastra("  ANA@X.test"))

    assert erro.code == "email_taken"
    assert erro.details == {}
    assert Organization.objects.count() == organizacoes


def test_v05_integrity_error_de_outra_restricao_sobe_sem_traducao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "_personal_slug", lambda: "ruvor")
    with pytest.raises(IntegrityError):
        _cadastra()


def test_v05_dados_invalidos_juntam_os_campos() -> None:
    erro = _erro(
        lambda: services.signup(
            requisicao(), email="nao-e-email", name="   ", password="123"
        )
    )
    assert erro.code == "invalid_parameter"
    assert set(erro.details["fields"]) == {"email", "name", "password"}
    assert User.objects.filter(email="nao-e-email").count() == 0


def test_v05_senha_parecida_com_o_nome_reprova_so_pela_semelhanca() -> None:
    nome, senha = "Rafaela Monteverde", "RafaelaMonteverde"
    esperado: list[str] = []
    try:
        UserAttributeSimilarityValidator(user_attributes=("email", "name")).validate(
            senha, User(email="rm@x.test", name=nome)
        )
    except ValidationError as exc:
        esperado = list(exc.messages)
    assert esperado, "o validador de semelhanca deveria reprovar esta senha"

    erro = _erro(
        lambda: services.signup(
            requisicao(), email="rm@x.test", name=nome, password=senha
        )
    )

    assert erro.details["fields"] == {"password": esperado}


def test_v05_falha_depois_de_criar_nao_deixa_organizacao_nem_usuario(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    organizacoes = Organization.objects.count()
    monkeypatch.setattr(services, "record", _grava_e_falha)

    with pytest.raises(Falhou):
        _cadastra()

    assert Organization.objects.count() == organizacoes
    assert not User.objects.filter(email="nova@pessoa.test").exists()
    assert not AccessEvent.objects.exists()


# --- V-06, entrada e saida -------------------------------------------------------------


def test_v06_entrada_troca_a_chave_da_sessao_e_grava_login() -> None:
    user = usuario(organizacao(), "ana@x.test")
    request = requisicao()
    antes = chave(request)

    entrou = services.login(request, email=" ANA@x.test", password=SENHA)
    depois = chave(request)

    assert entrou == user
    assert depois != antes
    assert autenticado(depois)
    (evento,) = _eventos("login")
    assert (evento.actor, evento.target, evento.organization) == (
        user,
        None,
        user.organization,
    )
    assert evento.email == "ana@x.test"
    assert evento.ip == "127.0.0.1"


def test_v06_os_tres_erros_de_entrada_sao_identicos() -> None:
    org = organizacao()
    usuario(org, "ana@x.test")
    usuario(org, "inativa@x.test", is_active=False)

    erros = [
        _erro(
            lambda: services.login(
                requisicao(), email="nao@existe.test", password=SENHA
            )
        ),
        _erro(
            lambda: services.login(
                requisicao(), email="ana@x.test", password="errada-123456"
            )
        ),
        _erro(
            lambda: services.login(requisicao(), email="inativa@x.test", password=SENHA)
        ),
    ]

    assert {(e.code, e.message, str(e.details)) for e in erros} == {
        ("invalid_credentials", services.INVALID_CREDENTIALS_MESSAGE, "{}")
    }


def test_v18_login_failed_com_e_sem_usuario_do_email() -> None:
    user = usuario(organizacao(), "ana@x.test")
    _erro(
        lambda: services.login(
            requisicao(), email="ana@x.test", password="errada-123456"
        )
    )
    _erro(lambda: services.login(requisicao(), email="ninguem@x.test", password=SENHA))

    com, sem = _eventos("login_failed")
    assert (com.actor, com.target, com.organization) == (None, user, user.organization)
    assert (sem.actor, sem.target, sem.organization) == (None, None, None)
    assert com.email == "ana@x.test"
    assert sem.email == "ninguem@x.test"
    assert com.details == sem.details == {"reason": "invalid_credentials"}


def test_v06_saida_apaga_a_sessao_e_grava_logout() -> None:
    user = usuario(organizacao(), "ana@x.test")
    request = requisicao()
    services.login(request, email="ana@x.test", password=SENHA)
    key = chave(request)

    reaberta = requisicao(session_key=key)
    services.logout(reaberta)

    assert not Session.objects.filter(session_key=key).exists()
    assert not autenticado(key)
    (evento,) = _eventos("logout")
    assert (evento.actor, evento.target, evento.organization) == (
        user,
        None,
        user.organization,
    )


def test_saida_sem_sessao_e_not_authenticated() -> None:
    assert _erro(lambda: services.logout(requisicao())).code == "not_authenticated"


def test_me_devolve_o_corpo_mesmo_com_senha_provisoria() -> None:
    user = usuario(organizacao(), "ana@x.test", must_change_password=True)
    request = requisicao()
    services.login(request, email="ana@x.test", password=SENHA)
    assert services.me(requisicao(session_key=chave(request))) == services.me_body(user)


# --- V-08, troca de senha --------------------------------------------------------------


def _entra(email: str, senha: str = SENHA) -> str:
    request = requisicao()
    services.login(request, email=email, password=senha)
    return chave(request)


def test_v08_senha_atual_errada() -> None:
    usuario(organizacao(), "ana@x.test")
    request = requisicao(session_key=_entra("ana@x.test"))
    erro = _erro(
        lambda: services.change_password(
            request, current_password="errada-123456", new_password="nova-senha-longa-9"
        )
    )
    assert erro.code == "invalid_credentials"


def test_v08_nova_igual_a_atual() -> None:
    usuario(organizacao(), "ana@x.test")
    request = requisicao(session_key=_entra("ana@x.test"))
    erro = _erro(
        lambda: services.change_password(
            request, current_password=SENHA, new_password=SENHA
        )
    )
    assert erro.code == "invalid_parameter"
    assert list(erro.details["fields"]) == ["new_password"]


def test_v08_troca_mantem_esta_sessao_derruba_a_outra_e_tira_a_flag() -> None:
    user = usuario(organizacao(), "ana@x.test", must_change_password=True)
    primeira = _entra("ana@x.test")
    segunda = _entra("ana@x.test")
    assert autenticado(primeira) and autenticado(segunda)

    request = requisicao(session_key=primeira)
    services.change_password(
        request, current_password=SENHA, new_password="nova-senha-longa-9"
    )
    primeira_depois = chave(request)

    assert autenticado(primeira_depois)
    assert not autenticado(segunda)
    user.refresh_from_db()
    assert user.must_change_password is False
    assert user.check_password("nova-senha-longa-9")
    (evento,) = _eventos("password_changed")
    assert (evento.actor, evento.target, evento.organization) == (
        user,
        None,
        user.organization,
    )


# --- V-16, bloqueio por (e-mail, IP) ---------------------------------------------------


def _falha(email: str = "ana@x.test", ip: str = "127.0.0.1") -> AccountError:
    return _erro(
        lambda: services.login(requisicao(ip=ip), email=email, password="errada-123456")
    )


def test_v16_quinta_falha_bloqueia_ate_a_senha_certa() -> None:
    user = usuario(organizacao(), "ana@x.test")
    for _ in range(5):
        assert _falha().code == "invalid_credentials"

    request = requisicao()
    erro = _erro(lambda: services.login(request, email="ana@x.test", password=SENHA))

    assert erro.code == "too_many_requests"
    assert 0 < erro.details["wait_seconds"] <= 900
    assert not request.user.is_authenticated
    user.refresh_from_db()
    assert user.last_login is None
    (evento,) = _eventos("login_throttled")
    assert (evento.actor, evento.target, evento.organization) == (
        None,
        user,
        user.organization,
    )
    assert evento.details == {"wait_seconds": erro.details["wait_seconds"]}


def test_v16_o_mesmo_email_de_outro_ip_entra() -> None:
    usuario(organizacao(), "ana@x.test")
    for _ in range(5):
        _falha()
    services.login(requisicao(ip="10.0.0.2"), email="ana@x.test", password=SENHA)


def test_v16_entrada_certa_zera_a_contagem() -> None:
    usuario(organizacao(), "ana@x.test")
    for _ in range(4):
        _falha()
    services.login(requisicao(), email="ana@x.test", password=SENHA)
    for _ in range(4):
        assert _falha().code == "invalid_credentials"
    services.login(requisicao(), email="ana@x.test", password=SENHA)


# --- V-18, transacao -------------------------------------------------------------------


def test_v18_login_evento_e_mudanca_na_mesma_transacao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = usuario(organizacao(), "ana@x.test")
    monkeypatch.setattr(services, "record", _grava_e_falha)

    with pytest.raises(Falhou):
        services.login(requisicao(), email="ana@x.test", password=SENHA)

    user.refresh_from_db()
    assert user.last_login is None
    assert not AccessEvent.objects.exists()


def test_v18_logout_evento_e_mudanca_na_mesma_transacao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    usuario(organizacao(), "ana@x.test")
    key = _entra("ana@x.test")
    antes = AccessEvent.objects.count()
    monkeypatch.setattr(services, "record", _grava_e_falha)

    with pytest.raises(Falhou):
        services.logout(requisicao(session_key=key))

    assert AccessEvent.objects.count() == antes
    assert Session.objects.filter(session_key=key).exists()
    assert autenticado(key)


def test_v18_troca_de_senha_evento_e_mudanca_na_mesma_transacao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = usuario(organizacao(), "ana@x.test")
    request = requisicao(session_key=_entra("ana@x.test"))
    antes = AccessEvent.objects.count()
    monkeypatch.setattr(services, "record", _grava_e_falha)

    with pytest.raises(Falhou):
        services.change_password(
            request, current_password=SENHA, new_password="nova-senha-longa-9"
        )

    user.refresh_from_db()
    assert user.check_password(SENHA)
    assert AccessEvent.objects.count() == antes


def test_v08_nova_senha_fraca_reprova_e_a_antiga_continua() -> None:
    user = usuario(organizacao(), "ana@x.test")
    request = requisicao(session_key=_entra("ana@x.test"))

    erro = _erro(
        lambda: services.change_password(
            request, current_password=SENHA, new_password="12345678901"
        )
    )

    assert erro.code == "invalid_parameter"
    assert list(erro.details["fields"]) == ["new_password"]
    assert erro.details["fields"]["new_password"]
    user.refresh_from_db()
    assert user.check_password(SENHA)
