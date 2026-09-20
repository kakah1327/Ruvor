"""O cliente real da B3, com `urlopen` falso injetado no mesmo ponto que a guarda usa.

Nenhum teste aqui sai para a rede (RF-15): o `urlopen` e substituido por um objeto que
devolve corpos das fixtures ou levanta o erro programado, e registra as `Request` que
recebeu. `sleep` e substituido por um registrador, para provar a repeticao sem esperar.
"""

from __future__ import annotations

import base64
import email.message
import importlib.metadata
import io
import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from apps.assets.b3 import B3Client, B3ClientError, Page
from tests.assets.conftest import fixture_json

LISTING_URL = (
    "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/"
    "GetInitialCompanies/"
)
DETAIL_URL = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetDetail/"


class FakeUrlopen:
    """Responde, em ordem, com cada item de `responses`: corpo (bytes) ou excecao."""

    def __init__(self, responses: list[bytes | Exception]) -> None:
        self.responses = list(responses)
        self.requests: list[urllib.request.Request] = []
        self.timeouts: list[float | None] = []

    def __call__(
        self, request: urllib.request.Request, timeout: float | None = None
    ) -> io.BytesIO:
        self.requests.append(request)
        self.timeouts.append(timeout)
        assert self.responses, (
            "o cliente chamou urlopen mais vezes que o cenario previa"
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return io.BytesIO(response)


def body(nome: str) -> bytes:
    return json.dumps(fixture_json(nome)).encode("utf-8")


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://exemplo.invalido", code, "erro", email.message.Message(), None
    )


def decoded_param(request: urllib.request.Request, prefix: str) -> dict[str, Any]:
    url = request.full_url
    assert url.startswith(prefix), url
    decoded: dict[str, Any] = json.loads(base64.b64decode(url[len(prefix) :]))
    return decoded


@pytest.fixture
def sleeps() -> list[float]:
    """Registro do `sleep` falso que `make_client` entrega ao construtor do cliente."""
    registrados: list[float] = []
    return registrados


def make_client(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[bytes | Exception],
    sleeps: list[float],
) -> tuple[B3Client, FakeUrlopen]:
    fake = FakeUrlopen(responses)
    monkeypatch.setattr("urllib.request.urlopen", fake)
    return B3Client(sleep=sleeps.append), fake


def test_rf15_pagina_1_vira_page_com_120_itens_e_30_paginas(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [body("listing_page_1")], sleeps)

    page = next(client.list_companies())

    assert isinstance(page, Page)
    assert page.page_number == 1
    assert page.total_pages == 30
    assert len(page.items) == 120
    assert page.items == fixture_json("listing_page_1")["results"]
    assert decoded_param(fake.requests[0], LISTING_URL) == {
        "language": "pt-br",
        "pageNumber": 1,
        "pageSize": 120,
    }
    assert fake.timeouts == [30.0]
    assert sleeps == []


def test_rf15_listagem_percorre_todas_as_paginas(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    listing = fixture_json("listing_page_1")
    page_1 = {
        "page": {**listing["page"], "totalPages": 2},
        "results": listing["results"][:2],
    }
    page_2 = {
        "page": {**listing["page"], "pageNumber": 2, "totalPages": 2},
        "results": listing["results"][2:3],
    }
    responses: list[bytes | Exception] = [
        json.dumps(page_1).encode("utf-8"),
        json.dumps(page_2).encode("utf-8"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    pages = list(client.list_companies())

    assert [p.page_number for p in pages] == [1, 2]
    assert [len(p.items) for p in pages] == [2, 1]
    assert [decoded_param(r, LISTING_URL)["pageNumber"] for r in fake.requests] == [
        1,
        2,
    ]


def test_rf15_page_size_invalido_levanta_b3clienterror(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [body("listing_invalid_page_size")], sleeps)

    with pytest.raises(B3ClientError, match="totalPages"):
        list(client.list_companies())

    assert len(fake.requests) == 1
    assert sleeps == []


def test_rf15_detalhe_vazio_e_devolvido_como_dicionario_vazio(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [body("detail_empty")], sleeps)

    detail = client.get_company("999999999")

    assert detail == {}
    assert decoded_param(fake.requests[0], DETAIL_URL) == {
        "codeCVM": "999999999",
        "language": "pt-br",
    }


def test_rf15_detalhe_e_devolvido_sem_transformacao(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, _ = make_client(monkeypatch, [body("detail_PETR")], sleeps)

    assert client.get_company("9512") == fixture_json("detail_PETR")


def test_repeticao_falha_duas_vezes_e_responde_na_terceira(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[bytes | Exception] = [
        urllib.error.URLError("conexao recusada"),
        http_error(503),
        body("detail_PETR"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    assert client.get_company("9512") == fixture_json("detail_PETR")
    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_repeticao_tambem_cobre_timeout(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[bytes | Exception] = [
        TimeoutError("timed out"),
        body("detail_empty"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    assert client.get_company("999999999") == {}
    assert len(fake.requests) == 2
    assert sleeps == [1]


def test_repeticao_nao_ocorre_em_4xx(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [http_error(404)], sleeps)

    with pytest.raises(B3ClientError, match="HTTP 404"):
        client.get_company("9512")

    assert len(fake.requests) == 1
    assert sleeps == []


def test_repeticao_desiste_apos_tres_falhas(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[bytes | Exception] = [
        http_error(500),
        http_error(502),
        TimeoutError(),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    with pytest.raises(B3ClientError, match="falhou 3 vezes"):
        client.get_company("9512")

    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_rf15_user_agent_presente_na_request(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [body("detail_empty")], sleeps)

    client.get_company("999999999")

    esperado = f"Ruvor/{importlib.metadata.version('ruvor-backend')}"
    assert fake.requests[0].get_header("User-agent") == esperado
