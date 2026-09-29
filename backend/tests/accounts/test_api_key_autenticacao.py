"""M4.2, T4: a autenticacao por chave e o contexto posto pela autenticacao (RF-06, RF-11,
RF-13; V-06, V-07, V-13 e V-17 pelo HTTP).

A chave le uma rota de leitura real do M1.6a, `GET /api/v1/assets`. O alcance -- o que a chave
nao pode -- e da T5.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

from apps.accounts import services
from apps.accounts.models import ApiKey, User
from apps.accounts.tenancy import current_organization_id, set_organization_id
from apps.api.errors import handle_exception
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db

LEITURA = "/api/v1/assets"
URLS_DE_TESTE = pytest.mark.urls("tests.accounts.urls_de_teste")


@pytest.fixture
def ana() -> User:
    return usuario(organizacao("acme"), "ana@acme.test")


@pytest.fixture
def segredo(ana: User) -> str:
    return services.create_api_key(ana, name="minha", ip=None)[1]


def _com(segredo: str, esquema: str = "Bearer") -> APIClient:
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"{esquema} {segredo}")
    return cliente


def _erro(resposta: Any, status: int, code: str) -> dict[str, Any]:
    assert resposta.status_code == status, resposta.content
    erro: dict[str, Any] = resposta.json()["error"]
    assert erro["code"] == code
    return erro


# --- V-06 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("esquema", ["Bearer", "bearer", "BEARER"])
def test_v06_a_chave_le_como_a_dona(segredo: str, esquema: str, debug: bool) -> None:
    resposta = _com(segredo, esquema).get(LEITURA)
    assert resposta.status_code == 200, resposta.content


def test_v06_sem_cabecalho_e_com_basic_segue_anonimo(segredo: str) -> None:
    assert APIClient().get(LEITURA).status_code == 200
    assert _com("dXNlcjpzZW5oYQ==", "Basic").get(LEITURA).status_code == 200


def _falhas(ana: User, segredo: str) -> dict[str, str]:
    """Os cinco casos de falha, cada um com o seu `Bearer`."""
    prefix = segredo.split("_")[1]
    revogada = services.create_api_key(ana, name="revogada", ip=None)
    services.revoke_api_key(ana, revogada[0].prefix, ip=None)
    bia = usuario(ana.organization, "bia@acme.test")
    da_inativa = services.create_api_key(bia, name="da bia", ip=None)[1]
    User.objects.filter(pk=bia.pk).update(is_active=False)
    return {
        "malformado": "rvr_nao-e-uma-chave",
        "prefix_inexistente": "rvr_00000000_" + "A" * 43,
        "hash_errado": f"rvr_{prefix}_" + "B" * 43,
        "revogada": revogada[1],
        "dona_inativa": da_inativa,
    }


def test_v06_as_cinco_falhas_dao_o_mesmo_401(ana: User, segredo: str) -> None:
    corpos = []
    for nome, token in _falhas(ana, segredo).items():
        resposta = _com(token).get(LEITURA)
        _erro(resposta, 401, "invalid_api_key")
        assert resposta["WWW-Authenticate"] == "Session", nome
        corpos.append(resposta.json())
    assert all(corpo == corpos[0] for corpo in corpos)


def test_v06_dona_com_senha_provisoria_e_403(ana: User, segredo: str) -> None:
    User.objects.filter(pk=ana.pk).update(must_change_password=True)
    _erro(_com(segredo).get(LEITURA), 403, "password_change_required")


# --- V-07 ---------------------------------------------------------------------------------


def _usado(segredo: str) -> Any:
    return ApiKey.unscoped.get(prefix=segredo.split("_")[1]).last_used_at


def test_v07_last_used_at_uma_escrita_por_minuto(
    segredo: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _usado(segredo) is None
    _com(segredo).get(LEITURA)
    primeiro = _usado(segredo)
    assert primeiro is not None
    _com(segredo).get(LEITURA)
    assert _usado(segredo) == primeiro

    depois = primeiro + timedelta(seconds=61)
    monkeypatch.setattr(timezone, "now", lambda: depois)
    _com(segredo).get(LEITURA)
    assert _usado(segredo) == depois


# --- V-13 ---------------------------------------------------------------------------------


def test_v13_o_tratador_da_401_com_o_cabecalho() -> None:
    excecao = AuthenticationFailed()
    # o que a `APIView` poe quando ha autenticador (atributo fora dos stubs)
    setattr(excecao, "auth_header", "Session")
    resposta = handle_exception(excecao, {})
    assert resposta.status_code == 401
    assert resposta.data["error"]["code"] == "invalid_api_key"
    assert resposta["WWW-Authenticate"] == "Session"


def test_v13_rebaixado_pela_apiview_e_permission_denied() -> None:
    excecao = AuthenticationFailed()
    excecao.status_code = 403
    resposta = handle_exception(excecao, {})
    assert resposta.status_code == 403
    assert resposta.data["error"]["code"] == "permission_denied"


# --- V-17 pelo HTTP -----------------------------------------------------------------------


@URLS_DE_TESTE
def test_v17_a_sessao_poe_a_organizacao_da_conta(ana: User) -> None:
    cliente = APIClient()
    cliente.force_login(ana)
    assert cliente.get("/test/organizacao").json() == {
        "organization_id": ana.organization_id
    }


@URLS_DE_TESTE
def test_v17_a_chave_poe_a_organizacao_da_dona(ana: User, segredo: str) -> None:
    assert _com(segredo).get("/test/organizacao").json() == {
        "organization_id": ana.organization_id
    }


@URLS_DE_TESTE
def test_v17_o_middleware_zera_no_comeco(ana: User) -> None:
    set_organization_id(ana.organization_id + 1000)
    assert APIClient().get("/test/organizacao").json() == {"organization_id": None}


@URLS_DE_TESTE
def test_v17_o_middleware_zera_no_fim(ana: User, segredo: str) -> None:
    # pedido autenticado: com anonimo nada poria o contexto, e a prova passaria vazia
    _com(segredo).get("/test/organizacao")
    assert current_organization_id() is None
