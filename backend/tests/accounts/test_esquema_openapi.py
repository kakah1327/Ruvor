"""M4.2, T8: o esquema OpenAPI (RF-12; V-08 do esquema, V-14).

O esquema e conferido contra o resolvedor, nos dois sentidos: toda rota e metodo de `/api/v1/`
esta nele -- menos `HEAD`, `OPTIONS` e `TRACE`, que o drf-spectacular omite, e menos a
`ApiNotFound`, que nao e rota --, e nenhum caminho dele fica sem rota.
"""

from __future__ import annotations

import re
from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from django.urls import URLPattern, get_resolver
from drf_spectacular.drainage import GENERATOR_STATS
from rest_framework.test import APIClient

from apps.accounts import services
from apps.api.views import ApiNotFound
from tests.accounts.conftest import organizacao, usuario
from tests.accounts.test_api_key_alcance import _rotas

pytestmark = pytest.mark.django_db

SCHEMA = "/api/v1/schema"
FORA = {"head", "options", "trace"}
ERRO = "#/components/schemas/ApiError"
# as respostas de sucesso sem corpo de esquema proprio: as 204 nao tem corpo, e o da `/schema`
# e o proprio esquema, objeto generico herdado do `SpectacularJSONAPIView`
SEM_CORPO = {
    ("get", "/api/v1/auth/csrf"),
    ("post", "/api/v1/auth/logout"),
    ("post", "/api/v1/auth/password"),
    ("delete", "/api/v1/api-keys/{prefix}"),
    ("get", SCHEMA),
}


@pytest.fixture(scope="module")
def esquema(django_db_blocker: Any) -> dict[str, Any]:
    with django_db_blocker.unblock():
        resposta = APIClient().get(SCHEMA)
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    return corpo


def _caminho(rota: str) -> str:
    return "/" + re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rota)


def _rotas_da_api() -> dict[tuple[str, str], type]:
    """(metodo, caminho) -> classe, de toda view sob `/api/v1/`, pelo resolvedor."""
    achadas: dict[tuple[str, str], type] = {}
    for rota, padrao in _rotas(get_resolver("config.urls").url_patterns):
        assert isinstance(padrao, URLPattern)
        classe = getattr(padrao.callback, "view_class", None)
        if not rota.startswith("api/v1/") or classe is None or classe is ApiNotFound:
            continue
        for metodo in classe.http_method_names:
            if metodo not in FORA and hasattr(classe, metodo):
                achadas[(metodo, _caminho(rota))] = classe
    return achadas


def _operacoes(esquema: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (metodo, caminho): operacao
        for caminho, item in esquema["paths"].items()
        for metodo, operacao in item.items()
        if metodo != "parameters"
    }


# --- valido e limpo -----------------------------------------------------------------------


def test_v14_o_gerador_nao_da_aviso_nem_erro() -> None:
    # a contagem e de classe e o comando nao a zera: um aviso de outro teste reprovaria este
    GENERATOR_STATS.reset()
    call_command("spectacular", "--validate", "--fail-on-warn", stdout=StringIO())


def test_v14_a_rota_do_esquema() -> None:
    resposta = APIClient().get(SCHEMA)
    assert resposta.status_code == 200
    assert resposta["Content-Type"].startswith("application/vnd.oai.openapi+json")
    assert resposta.json()["openapi"].startswith("3.")


def test_v08_a_chave_le_o_esquema() -> None:
    ana = usuario(organizacao("acme"), "ana@acme.test")
    segredo = services.create_api_key(ana, name="minha", ip=None)[1]
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    assert cliente.get(SCHEMA).status_code == 200


# --- o resolvedor contra o esquema --------------------------------------------------------


def test_v14_toda_rota_do_resolvedor_esta_no_esquema_e_vice_versa(
    esquema: dict[str, Any],
) -> None:
    rotas = set(_rotas_da_api())
    operacoes = set(_operacoes(esquema))
    assert len(rotas) >= 20  # contra a varredura inerte
    assert rotas - operacoes == set(), "rota fora do esquema"
    assert operacoes - rotas == set(), "operacao do esquema sem rota"


def test_v14_os_dois_esquemas_de_seguranca(esquema: dict[str, Any]) -> None:
    assert esquema["components"]["securitySchemes"] == {
        "sessionAuth": {"type": "apiKey", "in": "cookie", "name": "sessionid"},
        "apiKeyAuth": {"type": "http", "scheme": "bearer"},
    }


def test_v14_a_seguranca_segue_o_api_key_scope(esquema: dict[str, Any]) -> None:
    operacoes = _operacoes(esquema)
    for chave, classe in _rotas_da_api().items():
        seguranca = operacoes[chave]["security"]
        nomes = [next(iter(s), "{}") for s in seguranca]
        if classe.__dict__["api_key_scope"] == "read":
            assert nomes == ["sessionAuth", "apiKeyAuth", "{}"], chave
        else:
            assert "apiKeyAuth" not in nomes, chave
            assert "sessionAuth" in nomes, chave


def test_v14_toda_operacao_tem_o_erro_default(esquema: dict[str, Any]) -> None:
    for chave, operacao in _operacoes(esquema).items():
        conteudo = operacao["responses"]["default"]["content"]["application/json"]
        assert conteudo["schema"] == {"$ref": ERRO}, chave
    erro = esquema["components"]["schemas"]["ApiError"]
    assert set(erro["properties"]) == {"error"}


def test_v14_todo_corpo_de_sucesso_e_descrito(esquema: dict[str, Any]) -> None:
    for chave, operacao in _operacoes(esquema).items():
        sucessos = {c: r for c, r in operacao["responses"].items() if c.startswith("2")}
        assert len(sucessos) == 1, chave
        ((codigo, resposta),) = sucessos.items()
        if chave in SEM_CORPO:
            assert codigo == "204" or chave == ("get", SCHEMA), chave
            continue
        esquema_do_corpo = resposta["content"]["application/json"]["schema"]
        assert "$ref" in esquema_do_corpo, (chave, esquema_do_corpo)
