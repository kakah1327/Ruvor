"""M2.1a, T12: as rotas de conta, `auth/*` (RF-04, RF-21, RF-27; V-02b, V-04, V-15, V-20).

O CSRF so e conferido com `APIClient(enforce_csrf_checks=True)`; os outros testes usam o
cliente sem checagem, para provar uma coisa de cada vez. O limite `auth` conta no cache, que a
fixture `cache_limpo` zera a cada teste.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from apps.accounts.lockout import MAX_FAILURES
from apps.accounts.models import AccessEvent, Organization, User
from apps.accounts.views import STATUS_BY_CODE, AuthRateThrottle
from tests.accounts.conftest import SENHA, organizacao, usuario

pytestmark = pytest.mark.django_db

ACCOUNTS = Path(__file__).resolve().parents[2] / "apps" / "accounts"
CADASTRO = {"email": "Ana@Acme.test", "name": "Ana Souza", "password": SENHA}


def _erro(resposta: Any, status: int, code: str) -> dict[str, Any]:
    """Confere status e o formato da D-86; devolve o `error`."""
    assert resposta.status_code == status, resposta.content
    corpo = resposta.json()
    assert set(corpo) == {"error"}
    erro: dict[str, Any] = corpo["error"]
    assert set(erro) == {"code", "message", "details"}
    assert erro["code"] == code
    assert erro["message"]
    return erro


def _csrf(cliente: APIClient) -> str:
    return str(cliente.cookies[settings.CSRF_COOKIE_NAME].value)


# --- o ciclo -------------------------------------------------------------------------


def test_o_ciclo_signup_me_logout_login_password() -> None:
    cliente = APIClient()

    cadastro = cliente.post("/api/v1/auth/signup", CADASTRO, format="json")
    assert cadastro.status_code == 201, cadastro.content
    me = cadastro.json()
    assert me["email"] == "ana@acme.test"
    assert me["role"] == "admin"
    assert me["organization"]["is_personal"] is True

    assert cliente.get("/api/v1/auth/me").json() == me
    assert cliente.post("/api/v1/auth/logout").status_code == 204

    saiu = cliente.get("/api/v1/auth/me")
    _erro(saiu, 401, "not_authenticated")
    # o cabecalho distingue o 401 da permissao do `not_authenticated` do servico
    assert saiu["WWW-Authenticate"] == "Session"

    entrada = cliente.post(
        "/api/v1/auth/login",
        {"email": "ana@acme.test", "password": SENHA},
        format="json",
    )
    assert entrada.status_code == 200, entrada.content
    assert entrada.json() == me

    troca = cliente.post(
        "/api/v1/auth/password",
        {"current_password": SENHA, "new_password": "outra-senha-longa-77"},
        format="json",
    )
    assert troca.status_code == 204, troca.content
    assert cliente.get("/api/v1/auth/me").json()["must_change_password"] is False


def test_senha_provisoria_entra_e_me_mostra_a_flag() -> None:
    usuario(organizacao(), "bia@acme.test", must_change_password=True)
    cliente = APIClient()
    entrada = cliente.post(
        "/api/v1/auth/login",
        {"email": "bia@acme.test", "password": SENHA},
        format="json",
    )
    assert entrada.status_code == 200
    assert cliente.get("/api/v1/auth/me").json()["must_change_password"] is True


# --- V-02b: os cookies ----------------------------------------------------------------


def test_v02b_cookies_da_sessao_e_do_csrf() -> None:
    usuario(organizacao(), "ana@acme.test")
    resposta = APIClient().post(
        "/api/v1/auth/login",
        {"email": "ana@acme.test", "password": SENHA},
        format="json",
    )
    assert resposta.status_code == 200
    sessao = resposta.cookies[settings.SESSION_COOKIE_NAME]
    assert sessao["httponly"] is True
    assert sessao["samesite"] == "Lax"
    csrf = resposta.cookies[settings.CSRF_COOKIE_NAME]
    assert not csrf["httponly"]


# --- V-04: o CSRF ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rota", "corpo"),
    [
        ("/api/v1/auth/signup", CADASTRO),
        ("/api/v1/auth/login", {"email": "ana@acme.test", "password": SENHA}),
    ],
    ids=["signup", "login"],
)
def test_v04_anonimo_sem_token_e_csrf_failed_e_nada_e_gravado(
    rota: str, corpo: dict[str, str], debug: bool
) -> None:
    if rota.endswith("login"):
        usuario(organizacao(), "ana@acme.test")
    usuarios, eventos = User.objects.count(), AccessEvent.objects.count()

    resposta = APIClient(enforce_csrf_checks=True).post(rota, corpo, format="json")

    _erro(resposta, 403, "csrf_failed")
    assert User.objects.count() == usuarios
    assert AccessEvent.objects.count() == eventos
    assert settings.SESSION_COOKIE_NAME not in resposta.cookies


def test_v04_com_o_token_do_csrf_passa_e_o_token_muda_no_login() -> None:
    cliente = APIClient(enforce_csrf_checks=True)
    pedido = cliente.get("/api/v1/auth/csrf")
    assert pedido.status_code == 204
    assert settings.CSRF_COOKIE_NAME in pedido.cookies
    antes = _csrf(cliente)

    cadastro = cliente.post(
        "/api/v1/auth/signup", CADASTRO, format="json", HTTP_X_CSRFTOKEN=antes
    )
    assert cadastro.status_code == 201, cadastro.content
    depois = _csrf(cliente)
    assert depois != antes  # o `login()` do Django troca o token

    velho = cliente.post("/api/v1/auth/logout", format="json", HTTP_X_CSRFTOKEN=antes)
    _erro(velho, 403, "csrf_failed")
    novo = cliente.post("/api/v1/auth/logout", format="json", HTTP_X_CSRFTOKEN=depois)
    assert novo.status_code == 204, novo.content


def test_v04_login_com_token_passa() -> None:
    usuario(organizacao(), "ana@acme.test")
    cliente = APIClient(enforce_csrf_checks=True)
    cliente.get("/api/v1/auth/csrf")
    resposta = cliente.post(
        "/api/v1/auth/login",
        {"email": "ana@acme.test", "password": SENHA},
        format="json",
        HTTP_X_CSRFTOKEN=_csrf(cliente),
    )
    assert resposta.status_code == 200, resposta.content


# --- V-15: o limite por IP --------------------------------------------------------------


@pytest.fixture
def tres_por_minuto(monkeypatch: pytest.MonkeyPatch) -> None:
    # a taxa e lida no import (`throttling.py:66`): mexer em `REST_FRAMEWORK` nao muda nada
    monkeypatch.setattr(AuthRateThrottle, "THROTTLE_RATES", {"auth": "3/min"})


def _pede(rota: str, cliente: APIClient, n: int) -> Any:
    if rota == "signup":
        corpo = {**CADASTRO, "email": f"p{n}@acme.test"}
        return cliente.post("/api/v1/auth/signup", corpo, format="json")
    if rota == "login":
        corpo = {"email": "ninguem@acme.test", "password": "errada-errada"}
        return cliente.post("/api/v1/auth/login", corpo, format="json")
    corpo = {"current_password": "errada-errada", "new_password": "x"}
    return cliente.post("/api/v1/auth/password", corpo, format="json")


@pytest.mark.usefixtures("tres_por_minuto")
@pytest.mark.parametrize("rota", ["signup", "login", "password"])
def test_v15_o_quarto_pedido_do_ip_e_429(rota: str) -> None:
    cliente = APIClient()
    if rota == "password":
        cliente.force_login(usuario(organizacao(), "ana@acme.test"))
    for n in range(3):
        assert _pede(rota, cliente, n).status_code != 429
    resposta = _pede(rota, cliente, 3)
    erro = _erro(resposta, 429, "too_many_requests")
    espera = erro["details"]["wait_seconds"]
    assert isinstance(espera, int) and espera > 0
    assert resposta["Retry-After"] == str(espera)


@pytest.mark.usefixtures("tres_por_minuto")
def test_v15_conta_por_ip_mesmo_com_login() -> None:
    org = organizacao()
    # `force_login`: entrar pela rota `login` tambem contaria no IP
    a, b = APIClient(), APIClient()
    a.force_login(usuario(org, "a@acme.test"))
    b.force_login(usuario(org, "b@acme.test"))
    pedidos = [_pede("password", c, 0) for c in (a, b, a)]
    assert all(p.status_code != 429 for p in pedidos)
    _erro(_pede("password", b, 0), 429, "too_many_requests")


# --- V-20: os codigos pela rota --------------------------------------------------------


def test_v20_campo_ausente_e_invalid_parameter_com_os_campos(debug: bool) -> None:
    resposta = APIClient().post(
        "/api/v1/auth/signup", {"email": "ana@acme.test"}, format="json"
    )
    erro = _erro(resposta, 400, "invalid_parameter")
    assert set(erro["details"]["fields"]) == {"name", "password"}


def test_v20_senha_fraca_e_invalid_parameter_com_a_mensagem(debug: bool) -> None:
    resposta = APIClient().post(
        "/api/v1/auth/signup", {**CADASTRO, "password": "123"}, format="json"
    )
    erro = _erro(resposta, 400, "invalid_parameter")
    assert erro["details"]["fields"]["password"]
    assert Organization.objects.filter(is_personal=True).count() == 0


def test_v20_email_taken(debug: bool) -> None:
    usuario(organizacao(), "ana@acme.test")
    resposta = APIClient().post("/api/v1/auth/signup", CADASTRO, format="json")
    _erro(resposta, 409, "email_taken")


def test_v20_invalid_credentials(debug: bool) -> None:
    usuario(organizacao(), "ana@acme.test")
    resposta = APIClient().post(
        "/api/v1/auth/login",
        {"email": "ana@acme.test", "password": "errada-errada"},
        format="json",
    )
    erro = _erro(resposta, 400, "invalid_credentials")
    assert erro["details"] == {}


def test_v20_not_authenticated(debug: bool) -> None:
    resposta = APIClient().post("/api/v1/auth/logout")
    _erro(resposta, 401, "not_authenticated")
    assert resposta["WWW-Authenticate"] == "Session"


def test_v20_o_bloqueio_por_email_e_ip_e_429_com_retry_after(debug: bool) -> None:
    usuario(organizacao(), "ana@acme.test")
    cliente = APIClient()
    for _ in range(MAX_FAILURES):
        errada = cliente.post(
            "/api/v1/auth/login",
            {"email": "ana@acme.test", "password": "errada-errada"},
            format="json",
        )
        assert errada.status_code == 400
    resposta = cliente.post(
        "/api/v1/auth/login",
        {"email": "ana@acme.test", "password": SENHA},
        format="json",
    )
    erro = _erro(resposta, 429, "too_many_requests")
    espera = erro["details"]["wait_seconds"]
    assert isinstance(espera, int) and espera > 0
    assert resposta["Retry-After"] == str(espera)
    assert settings.SESSION_COOKIE_NAME not in resposta.cookies


# --- a traducao ------------------------------------------------------------------------


def _codigos_levantados() -> set[str]:
    """O primeiro argumento de toda chamada `AccountError(...)` em `apps/accounts/`."""
    codigos: set[str] = set()
    for arquivo in ACCOUNTS.rglob("*.py"):
        if "migrations" in arquivo.parts:
            continue
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if not (
                isinstance(no, ast.Call)
                and isinstance(no.func, ast.Name)
                and no.func.id == "AccountError"
            ):
                continue
            primeiro = no.args[0] if no.args else None
            assert isinstance(primeiro, ast.Constant) and isinstance(
                primeiro.value, str
            ), f"{arquivo.name}:{no.lineno}: codigo de AccountError nao literal"
            codigos.add(primeiro.value)
    return codigos


def test_todo_codigo_levantado_tem_traducao_e_nenhuma_traducao_e_morta() -> None:
    # igualdade, e nao inclusao: com zero chamadas achadas, a inclusao passaria vazia
    assert _codigos_levantados() == set(STATUS_BY_CODE) | {"too_many_requests"}
