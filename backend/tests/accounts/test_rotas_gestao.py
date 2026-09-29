"""M2.1a, T13: as rotas de gestao, `organization/users*` (RF-14 a RF-18 pela rota; V-03,
V-20).

A regra ja e provada nos servicos (`test_gestao.py`); aqui, que cada rota chega ao servico
certo, com o status e o corpo da D-86. Os erros rodam com `DEBUG` ligado e desligado.
"""

from __future__ import annotations

from typing import Any

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Organization, User
from tests.accounts.conftest import SENHA, organizacao, usuario

pytestmark = pytest.mark.django_db

USERS = "/api/v1/organization/users"


def _erro(resposta: Any, status: int, code: str) -> dict[str, Any]:
    assert resposta.status_code == status, resposta.content
    corpo = resposta.json()
    assert set(corpo) == {"error"}
    erro: dict[str, Any] = corpo["error"]
    assert set(erro) == {"code", "message", "details"}
    assert erro["code"] == code
    return erro


def _logado(user: User) -> APIClient:
    cliente = APIClient()
    cliente.force_login(user)
    return cliente


@pytest.fixture
def org() -> Organization:
    return organizacao("acme")


@pytest.fixture
def admin(org: Organization) -> APIClient:
    return _logado(usuario(org, "adm@acme.test", role="admin"))


def test_o_ciclo_da_admin(admin: APIClient) -> None:
    criado = admin.post(
        USERS,
        {"email": "Bia@Acme.test", "name": "Bia", "role": "member"},
        format="json",
    )
    assert criado.status_code == 201, criado.content
    corpo = criado.json()
    senha = corpo["temporary_password"]
    assert isinstance(senha, str) and len(senha) == 16
    assert corpo["user"]["email"] == "bia@acme.test"
    assert corpo["user"]["must_change_password"] is True
    assert set(corpo["user"]) == {
        "email",
        "name",
        "role",
        "is_active",
        "must_change_password",
        "created_at",
        "last_login",
    }

    lista = admin.get(USERS).json()
    assert lista["count"] == 2
    assert (lista["limit"], lista["offset"]) == (50, 0)
    assert [u["email"] for u in lista["results"]] == ["adm@acme.test", "bia@acme.test"]

    desativada = admin.patch(
        f"{USERS}/bia@acme.test", {"is_active": False}, format="json"
    )
    assert desativada.status_code == 200, desativada.content
    assert desativada.json()["is_active"] is False

    redefinida = admin.post(f"{USERS}/bia@acme.test/temporary-password")
    assert redefinida.status_code == 200, redefinida.content
    assert redefinida.json()["temporary_password"] != senha


def test_o_criado_entra_com_a_provisoria_e_nao_gere(admin: APIClient) -> None:
    senha = admin.post(
        USERS,
        {"email": "bia@acme.test", "name": "Bia", "role": "admin"},
        format="json",
    ).json()["temporary_password"]
    bia = APIClient()
    entrada = bia.post(
        "/api/v1/auth/login",
        {"email": "bia@acme.test", "password": senha},
        format="json",
    )
    assert entrada.status_code == 200
    _erro(bia.get(USERS), 403, "password_change_required")


def test_o_email_da_rota_com_caixa_mista_e_arroba_codificada(
    admin: APIClient, org: Organization
) -> None:
    usuario(org, "bia@acme.test")
    resposta = admin.patch(f"{USERS}/BIA%40Acme.test", {"role": "admin"}, format="json")
    assert resposta.status_code == 200, resposta.content
    assert resposta.json()["role"] == "admin"


# --- V-03 e V-20 --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("get", USERS),
        ("post", USERS),
        ("patch", f"{USERS}/x@acme.test"),
        ("post", f"{USERS}/x@acme.test/temporary-password"),
    ],
)
def test_v03_anonimo_e_401_com_www_authenticate(
    metodo: str, rota: str, debug: bool
) -> None:
    resposta = getattr(APIClient(), metodo)(rota, {}, format="json")
    _erro(resposta, 401, "not_authenticated")
    assert resposta["WWW-Authenticate"] == "Session"


def test_v20_password_change_required(org: Organization, debug: bool) -> None:
    cliente = _logado(
        usuario(org, "adm@acme.test", role="admin", must_change_password=True)
    )
    _erro(cliente.get(USERS), 403, "password_change_required")


def test_v20_permission_denied(org: Organization, debug: bool) -> None:
    cliente = _logado(usuario(org, "bia@acme.test", role="member"))
    _erro(cliente.get(USERS), 403, "permission_denied")


def test_v20_personal_organization(debug: bool) -> None:
    pessoal = organizacao("pessoal-x", pessoal=True)
    cliente = _logado(usuario(pessoal, "eu@x.test", role="admin"))
    _erro(cliente.get(USERS), 409, "personal_organization")


def test_v20_user_not_found_igual_para_outra_organizacao_e_inexistente(
    admin: APIClient, debug: bool
) -> None:
    usuario(organizacao("outra"), "de-fora@outra.test")
    fora = _erro(
        admin.patch(f"{USERS}/de-fora@outra.test", {"role": "admin"}, format="json"),
        404,
        "user_not_found",
    )
    nenhum = _erro(
        admin.patch(f"{USERS}/ninguem@acme.test", {"role": "admin"}, format="json"),
        404,
        "user_not_found",
    )
    assert fora == nenhum
    assert User.objects.get(email="de-fora@outra.test").role == "member"


def test_v20_last_admin(admin: APIClient, debug: bool) -> None:
    _erro(
        admin.patch(f"{USERS}/adm@acme.test", {"role": "member"}, format="json"),
        409,
        "last_admin",
    )


def test_v20_use_password_route(admin: APIClient, debug: bool) -> None:
    _erro(
        admin.post(f"{USERS}/adm@acme.test/temporary-password"),
        409,
        "use_password_route",
    )


def test_v20_email_taken(admin: APIClient, debug: bool) -> None:
    usuario(organizacao("outra"), "bia@outra.test")
    _erro(
        admin.post(
            USERS,
            {"email": "bia@outra.test", "name": "Bia", "role": "member"},
            format="json",
        ),
        409,
        "email_taken",
    )


@pytest.mark.parametrize(
    ("consulta", "parametro"),
    [("limit=abc", "limit"), ("offset=1_0", "offset"), ("limit=101", "limit")],
)
def test_v20_invalid_parameter_na_consulta(
    admin: APIClient, consulta: str, parametro: str, debug: bool
) -> None:
    erro = _erro(admin.get(f"{USERS}?{consulta}"), 400, "invalid_parameter")
    assert erro["details"] == {"parameter": parametro}


def test_v20_invalid_parameter_no_corpo_do_patch(
    admin: APIClient, org: Organization, debug: bool
) -> None:
    usuario(org, "bia@acme.test")
    erro = _erro(
        admin.patch(f"{USERS}/bia@acme.test", {"name": "Outra"}, format="json"),
        400,
        "invalid_parameter",
    )
    assert erro["details"] == {"fields": {"name": ["campo desconhecido"]}}


def test_patch_com_corpo_que_nao_e_objeto_e_invalid_parameter(
    admin: APIClient, org: Organization
) -> None:
    usuario(org, "bia@acme.test")
    _erro(
        admin.patch(f"{USERS}/bia@acme.test", ["role"], format="json"),
        400,
        "invalid_parameter",
    )


def test_a_senha_de_quem_gere_continua_a_mesma(admin: APIClient) -> None:
    # a gestao nunca mexe na senha de quem pede: a administradora ainda entra com a dela
    admin.post(
        USERS,
        {"email": "bia@acme.test", "name": "Bia", "role": "member"},
        format="json",
    )
    assert User.objects.get(email="adm@acme.test").check_password(SENHA)
