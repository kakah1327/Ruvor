"""V-08: o formato de erro da D-86, com `DEBUG` ligado e desligado.

Todo erro sai como `{"error": {"code", "message", "details"}}`, com `details` presente. Os
casos de 400 de parametro, 404 de ativo, 409, 422 e 429 entram com as rotas que os levantam
(T7 e T12 do M1.6a), pela mesma fixture `debug`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from django.test import Client
from rest_framework.exceptions import ParseError, ValidationError

from apps.api.errors import ApiError, handle_exception
from apps.api.views import ApiNotFound
from tests.api.urls_de_teste import SEGREDO

if TYPE_CHECKING:
    # so existe nos stubs: e o tipo que o cliente de teste devolve
    from django.test.client import _MonkeyPatchedWSGIResponse

URLS_DE_TESTE = pytest.mark.urls("tests.api.urls_de_teste")


def _erro(
    resposta: _MonkeyPatchedWSGIResponse, status: int, code: str
) -> dict[str, Any]:
    """Confere status, tipo e o formato inteiro do corpo; devolve o `error`."""
    assert resposta.status_code == status, resposta.content
    assert resposta["Content-Type"] == "application/json"
    corpo = resposta.json()
    assert set(corpo) == {"error"}
    erro: dict[str, Any] = corpo["error"]
    assert set(erro) == {"code", "message", "details"}
    assert erro["code"] == code
    assert isinstance(erro["message"], str) and erro["message"]
    assert isinstance(erro["details"], dict)
    return erro


@pytest.mark.parametrize(
    "caminho", ["/api/v1/nada", "/api/qualquer", "/api/v1/nada/", "/api/qualquer/"]
)
def test_rota_inexistente_sob_api_e_not_found(
    client: Client, debug: bool, caminho: str
) -> None:
    erro = _erro(client.get(caminho), 404, "not_found")
    assert erro["details"] == {}


@pytest.mark.parametrize("metodo", ApiNotFound.http_method_names)
def test_view_final_responde_not_found_em_todo_metodo(
    client: Client, debug: bool, metodo: str
) -> None:
    resposta = client.generic(metodo.upper(), "/api/v1/nada")
    if metodo == "head":
        # o cliente de teste tira o corpo do HEAD, como o servidor faria
        assert resposta.status_code == 404
        return
    _erro(resposta, 404, "not_found")


def test_rota_inexistente_fora_de_api_segue_o_django(
    client: Client, debug: bool
) -> None:
    resposta = client.get("/nada")
    assert resposta.status_code == 404
    assert resposta["Content-Type"].startswith("text/html")


@URLS_DE_TESTE
def test_metodo_nao_permitido(client: Client, debug: bool) -> None:
    erro = _erro(client.put("/test/so-get"), 405, "method_not_allowed")
    assert "PUT" in erro["message"]
    assert erro["details"] == {}


@URLS_DE_TESTE
def test_formato_de_resposta_nao_aceito(client: Client, debug: bool) -> None:
    resposta = client.get("/test/so-get", headers={"Accept": "text/html"})
    erro = _erro(resposta, 406, "not_acceptable")
    assert erro["details"] == {}


@URLS_DE_TESTE
def test_formato_do_corpo_nao_suportado(client: Client, debug: bool) -> None:
    resposta = client.post("/test/corpo", data="x=1", content_type="text/plain")
    erro = _erro(resposta, 415, "unsupported_media_type")
    assert erro["details"] == {}


@URLS_DE_TESTE
def test_corpo_json_malformado_e_invalid_parameter(client: Client, debug: bool) -> None:
    resposta = client.post("/test/corpo", data="{nao", content_type="application/json")
    erro = _erro(resposta, 400, "invalid_parameter")
    assert erro["details"] == {}


@URLS_DE_TESTE
def test_view_sem_permissao_declarada_nasce_fechada(
    client: Client, debug: bool
) -> None:
    erro = _erro(client.get("/test/sem-permissao"), 403, "permission_denied")
    assert erro["details"] == {}


@URLS_DE_TESTE
def test_erro_nao_previsto_e_500_sem_traceback(debug: bool) -> None:
    # Sem relancar no teste: o que se confere e o que o Django devolveria ao navegador.
    # Com o tratador devolvendo `None`, isto seria a pagina de depuracao (DEBUG ligado)
    # ou a pagina de erro do Django (desligado) — HTML, fora do formato.
    cliente = Client(raise_request_exception=False)
    resposta = cliente.get("/test/erro")
    erro = _erro(resposta, 500, "internal_error")
    assert erro["details"] == {}
    texto = resposta.content.decode()
    assert "Traceback" not in texto
    assert "ValueError" not in texto
    assert SEGREDO not in texto


def test_rota_de_saude_nao_muda(client: Client, debug: bool) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


# O mapeamento, direto no tratador: as excecoes do Django que as views de teste nao
# alcancam, a de negocio com detalhes, e uma do DRF fora da lista fechada.
@pytest.mark.parametrize(
    ("excecao", "status", "code", "details"),
    [
        (Http404(), 404, "not_found", {}),
        (DjangoPermissionDenied(), 403, "permission_denied", {}),
        (ParseError(), 400, "invalid_parameter", {}),
        (
            ApiError(
                404, "asset_not_found", "Ativo XPTO9 não existe.", {"ticker": "XPTO9"}
            ),
            404,
            "asset_not_found",
            {"ticker": "XPTO9"},
        ),
        (ApiError(422, "asset_inactive", "Ativo inativo."), 422, "asset_inactive", {}),
        (ValidationError("fora da lista"), 500, "internal_error", {}),
    ],
)
def test_mapeamento_do_tratador(
    excecao: Exception, status: int, code: str, details: dict[str, Any]
) -> None:
    resposta = handle_exception(excecao, {})
    assert resposta.status_code == status
    assert resposta.data == {
        "error": {
            "code": code,
            "message": resposta.data["error"]["message"],
            "details": details,
        }
    }
    assert resposta.data["error"]["message"]
