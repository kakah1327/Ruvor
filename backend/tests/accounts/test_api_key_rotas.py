"""M4.2, T6: as rotas de chave, `api-keys*` (RF-03 a RF-05 pela rota; V-03, V-05, V-08).

A regra ja e provada nos servicos (`test_api_key_servicos.py`); aqui, que cada rota chega ao
servico certo, com o status e o corpo da D-86. Os erros rodam com `DEBUG` ligado e desligado.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.accounts import services
from apps.accounts.models import AccessEvent, ApiKey, User
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db

KEYS = "/api/v1/api-keys"
IP = "10.9.8.7"
SEGREDO = re.compile(r"rvr_[0-9a-f]{8}_[A-Za-z0-9_-]{43}")
CORPO = {"prefix", "name", "scopes", "created_at", "last_used_at"}


def _erro(resposta: Any, status: int, code: str) -> dict[str, Any]:
    assert resposta.status_code == status, resposta.content
    corpo = resposta.json()
    assert set(corpo) == {"error"}
    erro: dict[str, Any] = corpo["error"]
    assert set(erro) == {"code", "message", "details"}
    assert erro["code"] == code
    return erro


def _logado(user: User) -> APIClient:
    cliente = APIClient(REMOTE_ADDR=IP)
    cliente.force_login(user)
    return cliente


@pytest.fixture
def ana() -> User:
    return usuario(organizacao("acme"), "ana@acme.test", role="admin")


@pytest.fixture
def logada(ana: User) -> APIClient:
    return _logado(ana)


def test_o_ciclo_da_chave(ana: User, logada: APIClient) -> None:
    criada = logada.post(KEYS, {"name": "  minha chave  "}, format="json")
    assert criada.status_code == 201, criada.content
    corpo = criada.json()
    assert set(corpo) == {"api_key", "secret"}
    assert set(corpo["api_key"]) == CORPO
    assert corpo["api_key"]["name"] == "minha chave"
    assert corpo["api_key"]["scopes"] == ["read"]
    assert corpo["api_key"]["last_used_at"] is None
    segredo = corpo["secret"]
    assert SEGREDO.fullmatch(segredo)
    prefix = corpo["api_key"]["prefix"]
    assert segredo.startswith(f"rvr_{prefix}_")
    (evento,) = AccessEvent.objects.filter(kind="api_key_created")
    assert (evento.actor_id, evento.ip) == (ana.pk, IP)

    # a chave recem-criada le pela rota de leitura
    pela_chave = APIClient()
    pela_chave.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    assert pela_chave.get("/api/v1/assets").status_code == 200

    lista = logada.get(KEYS)
    assert lista.status_code == 200, lista.content
    assert set(lista.json()) == {"results"}
    (item,) = lista.json()["results"]
    assert set(item) == CORPO
    assert item["prefix"] == prefix
    assert item["last_used_at"] is not None  # a leitura acima contou como uso
    assert "secret" not in item

    revogada = logada.delete(f"{KEYS}/{prefix}")
    assert revogada.status_code == 204, revogada.content
    assert revogada.content == b""
    assert ApiKey.unscoped.get(prefix=prefix).revoked_at is not None
    (evento,) = AccessEvent.objects.filter(kind="api_key_revoked")
    assert evento.ip == IP
    assert evento.details == {"prefix": prefix, "via": "owner"}

    assert logada.get(KEYS).json() == {"results": []}
    _erro(pela_chave.get("/api/v1/assets"), 401, "invalid_api_key")


def test_a_lista_vem_da_mais_nova_para_a_mais_velha(
    ana: User, logada: APIClient
) -> None:
    velha = services.create_api_key(ana, name="velha", ip=None)[0]
    nova = services.create_api_key(ana, name="nova", ip=None)[0]
    lista = logada.get(KEYS).json()["results"]
    assert [k["prefix"] for k in lista] == [nova.prefix, velha.prefix]


# --- os erros, no formato da D-86 ----------------------------------------------------------


@pytest.mark.parametrize("nome", ["", "   ", "x" * 61])
def test_v03_nome_invalido(logada: APIClient, nome: str, debug: bool) -> None:
    erro = _erro(
        logada.post(KEYS, {"name": nome}, format="json"), 400, "invalid_parameter"
    )
    assert list(erro["details"]["fields"]) == ["name"]


def test_v03_sem_nome_no_corpo(logada: APIClient, debug: bool) -> None:
    erro = _erro(logada.post(KEYS, {}, format="json"), 400, "invalid_parameter")
    assert list(erro["details"]["fields"]) == ["name"]


def test_v03_a_decima_primeira_ativa(ana: User, logada: APIClient, debug: bool) -> None:
    for i in range(services.MAX_ACTIVE_KEYS):
        services.create_api_key(ana, name=f"k{i}", ip=None)
    erro = _erro(
        logada.post(KEYS, {"name": "mais"}, format="json"), 409, "api_key_limit"
    )
    assert erro["details"] == {"max": services.MAX_ACTIVE_KEYS}


def test_v05_de_outra_pessoa_revogada_ou_inexistente_e_o_mesmo_404(
    ana: User, logada: APIClient, debug: bool
) -> None:
    bia = usuario(ana.organization, "bia@acme.test")
    de_outra = services.create_api_key(bia, name="da bia", ip=None)[0]
    revogada = services.create_api_key(ana, name="velha", ip=None)[0]
    services.revoke_api_key(ana, revogada.prefix, ip=None)

    corpos = [
        _erro(logada.delete(f"{KEYS}/{p}"), 404, "api_key_not_found")
        for p in (de_outra.prefix, revogada.prefix, "deadbeef")
    ]
    assert corpos[0] == corpos[1] == corpos[2]
    assert ApiKey.unscoped.get(pk=de_outra.pk).revoked_at is None


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [("get", KEYS), ("post", KEYS), ("delete", f"{KEYS}/deadbeef")],
)
def test_sem_login_e_401(metodo: str, rota: str, debug: bool) -> None:
    _erro(getattr(APIClient(), metodo)(rota), 401, "not_authenticated")


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [("get", KEYS), ("post", KEYS), ("delete", f"{KEYS}/deadbeef")],
)
def test_com_senha_provisoria_e_403(
    ana: User, metodo: str, rota: str, debug: bool
) -> None:
    provisoria = usuario(ana.organization, "bia@acme.test", must_change_password=True)
    _erro(getattr(_logado(provisoria), metodo)(rota), 403, "password_change_required")


# --- V-08: a chave nao gere chave ----------------------------------------------------------


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [("get", KEYS), ("post", KEYS), ("delete", f"{KEYS}/deadbeef")],
)
def test_v08_a_chave_nao_alcanca_api_keys(
    ana: User, metodo: str, rota: str, debug: bool
) -> None:
    key, segredo = services.create_api_key(ana, name="minha", ip=None)
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    _erro(getattr(cliente, metodo)(rota), 403, "api_key_not_allowed")
    assert ApiKey.unscoped.get(pk=key.pk).revoked_at is None
    assert ApiKey.unscoped.filter(user=ana).count() == 1
