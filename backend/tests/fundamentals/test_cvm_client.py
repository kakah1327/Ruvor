"""O cliente real da CVM, com `urlopen` falso injetado no mesmo ponto que a guarda usa.

Nenhum teste aqui sai para a rede (RF-32): o `urlopen` e substituido por um objeto que
devolve respostas programadas ou levanta o erro programado, e registra as `Request` que
recebeu. `sleep` e substituido por um registrador, para provar a repeticao sem esperar.
"""

from __future__ import annotations

import email.message
import http.client
import importlib.metadata
import urllib.error
import urllib.request
from datetime import datetime
from types import TracebackType
from zoneinfo import ZoneInfo

import pytest

from apps.fundamentals.cvm import CvmClient, CvmClientError, CvmDownload, CvmHead
from tests.fundamentals.conftest import FakeCvm, fixture_zip, serve_range

LAST_MODIFIED = "Sun, 20 Sep 2026 11:11:59 GMT"


class FakeResponse:
    """O que `urlopen` devolve num 2xx: gerenciador de contexto com `status`, `headers`
    e `read()`. `read()` levanta `read_error`, se houver — a leitura interrompida do corpo.
    """

    def __init__(
        self,
        body: bytes,
        last_modified: str | None,
        read_error: Exception | None = None,
    ) -> None:
        self._body = body
        self._read_error = read_error
        self.status = 200
        self.headers = email.message.Message()
        if last_modified is not None:
            self.headers["Last-Modified"] = last_modified
        self.reads = 0

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def read(self) -> bytes:
        self.reads += 1
        if self._read_error is not None:
            raise self._read_error
        return self._body


class FakeUrlopen:
    """Responde, em ordem, com cada item de `responses`: `FakeResponse` ou excecao."""

    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self.responses = list(responses)
        self.requests: list[urllib.request.Request] = []
        self.timeouts: list[float | None] = []

    def __call__(
        self, request: urllib.request.Request, timeout: float | None = None
    ) -> FakeResponse:
        self.requests.append(request)
        self.timeouts.append(timeout)
        assert self.responses, (
            "o cliente chamou urlopen mais vezes que o cenario previa"
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def ok(body: bytes = b"", last_modified: str | None = LAST_MODIFIED) -> FakeResponse:
    return FakeResponse(body, last_modified)


def http_error(code: int) -> urllib.error.HTTPError:
    """`HTTPError` como o `urlopen` levanta, com `Last-Modified` — que o 4xx ignora."""
    headers = email.message.Message()
    headers["Last-Modified"] = LAST_MODIFIED
    return urllib.error.HTTPError(
        "https://exemplo.invalido", code, "erro", headers, None
    )


@pytest.fixture
def sleeps() -> list[float]:
    """Registro do `sleep` falso que `make_client` entrega ao construtor do cliente."""
    registrados: list[float] = []
    return registrados


def make_client(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[FakeResponse | Exception],
    sleeps: list[float],
) -> tuple[CvmClient, FakeUrlopen]:
    fake = FakeUrlopen(responses)
    monkeypatch.setattr("urllib.request.urlopen", fake)
    return CvmClient(sleep=sleeps.append), fake


def test_rf32_get_monta_a_url_do_itr_e_devolve_o_zip(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    payload = fixture_zip("itr_2024")
    client, fake = make_client(monkeypatch, [ok(payload)], sleeps)

    response = client.get("itr", 2024)

    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2024.zip"
    assert response == CvmDownload(200, LAST_MODIFIED, url, payload)
    assert fake.requests[0].full_url == url
    assert fake.requests[0].get_method() == "GET"
    assert fake.timeouts == [120.0]
    assert sleeps == []


def test_rf32_url_do_dfp_tem_o_tipo_em_maiuscula_no_caminho(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [ok(b"zip")], sleeps)

    response = client.get("dfp", 2025)

    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2025.zip"
    assert response.url == url
    assert fake.requests[0].full_url == url


def test_rf32_head_usa_o_metodo_head_le_o_last_modified_e_nao_le_o_corpo(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    resposta = ok(b"nao deveria ser lido")
    client, fake = make_client(monkeypatch, [resposta], sleeps)

    response = client.head("itr", 2024)

    assert response == CvmHead(200, LAST_MODIFIED)
    assert fake.requests[0].get_method() == "HEAD"
    assert fake.requests[0].full_url.endswith("/ITR/DADOS/itr_cia_aberta_2024.zip")
    assert resposta.reads == 0


def test_rf32_sem_last_modified_vira_none(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, _ = make_client(
        monkeypatch, [ok(last_modified=None), ok(b"zip", last_modified=None)], sleeps
    )

    assert client.head("dfp", 2016) == CvmHead(200, None)
    assert client.get("dfp", 2016).last_modified is None


def test_rf32_404_e_devolvido_sem_excecao_e_sem_repetir(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [http_error(404), http_error(404)], sleeps)

    assert client.head("itr", 2026) == CvmHead(404, None)
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2026.zip"
    assert client.get("itr", 2026) == CvmDownload(404, None, url, None)
    assert len(fake.requests) == 2
    assert sleeps == []


def test_rf32_user_agent_presente_nas_duas_chamadas(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [ok(), ok(b"zip")], sleeps)

    client.head("itr", 2024)
    client.get("itr", 2024)

    esperado = f"Ruvor/{importlib.metadata.version('ruvor-backend')}"
    assert [r.get_header("User-agent") for r in fake.requests] == [esperado, esperado]


def test_rf32_tipo_desconhecido_levanta_sem_chamar_a_rede(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [], sleeps)

    with pytest.raises(ValueError, match="tipo de documento desconhecido"):
        client.get("fre", 2024)
    assert fake.requests == []


def test_repeticao_falha_duas_vezes_com_5xx_e_responde_na_terceira(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[FakeResponse | Exception] = [
        http_error(503),
        http_error(500),
        ok(b"zip"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    response = client.get("itr", 2024)

    assert response.http_status == 200
    assert response.payload == b"zip"
    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_repeticao_cobre_a_leitura_interrompida_do_corpo(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[FakeResponse | Exception] = [
        FakeResponse(b"", LAST_MODIFIED, http.client.IncompleteRead(b"parte", 100)),
        FakeResponse(b"", LAST_MODIFIED, ConnectionResetError("reset pelo par")),
        ok(b"zip inteiro"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    response = client.get("itr", 2025)

    assert response.payload == b"zip inteiro"
    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_repeticao_cobre_timeout_e_erro_de_rede_no_head(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[FakeResponse | Exception] = [
        TimeoutError("timed out"),
        urllib.error.URLError("conexao recusada"),
        ok(),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    assert client.head("dfp", 2024) == CvmHead(200, LAST_MODIFIED)
    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_repeticao_desiste_apos_tres_falhas(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[FakeResponse | Exception] = [
        http_error(502),
        FakeResponse(b"", LAST_MODIFIED, http.client.IncompleteRead(b"", 10)),
        ConnectionResetError("reset pelo par"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    with pytest.raises(CvmClientError, match="falhou 3 vezes"):
        client.get("itr", 2024)

    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_rf32_fake_cvm_registra_antes_e_reprova_cenario_mal_montado() -> None:
    head = CvmHead(200, "gen-1-itr-2024")
    fake = FakeCvm(
        {("itr", 2024): [head, CvmClientError("programada")]},
        {},
    )

    assert fake.head("itr", 2024) is head
    with pytest.raises(CvmClientError, match="programada"):
        fake.head("itr", 2024)
    with pytest.raises(AssertionError, match="esgotaram"):
        fake.head("itr", 2024)
    with pytest.raises(AssertionError, match="nao tem resposta"):
        fake.get("dfp", 2024)
    assert fake.calls == [
        ("head", "itr", 2024),
        ("head", "itr", 2024),
        ("head", "itr", 2024),
        ("get", "dfp", 2024),
    ]


def test_rf32_serve_range_cobre_o_intervalo_e_repete_o_last_modified_por_geracao() -> (
    None
):
    fake = FakeCvm({}, {})
    # 2025-01-01 00h30 em UTC ainda e 2024 em Sao Paulo: o ano corrente e 2024
    now = datetime(2025, 1, 1, 0, 30, tzinfo=ZoneInfo("UTC"))
    itr_2024 = fixture_zip("itr_2024")

    serve_range(fake, now, {("itr", 2024): itr_2024})
    serve_range(fake, now, {("itr", 2024): itr_2024})
    serve_range(fake, now, {("itr", 2024): itr_2024}, generation=2)

    assert len(fake.heads[("dfp", 2019)]) == 3
    assert sorted(fake.heads) == sorted(
        (kind, year) for year in range(2016, 2025) for kind in ("itr", "dfp")
    )
    heads = fake.heads[("dfp", 2019)]
    assert [h.last_modified for h in heads if isinstance(h, CvmHead)] == [
        "gen-1-dfp-2019",
        "gen-1-dfp-2019",
        "gen-2-dfp-2019",
    ]
    downloads = fake.gets[("itr", 2024)]
    assert all(isinstance(d, CvmDownload) for d in downloads)
    assert [d.payload for d in downloads if isinstance(d, CvmDownload)] == [
        itr_2024
    ] * 3
    vazio = fake.gets[("itr", 2016)][0]
    assert isinstance(vazio, CvmDownload)
    assert vazio.http_status == 200
    assert vazio.url.endswith("/ITR/DADOS/itr_cia_aberta_2016.zip")
    assert vazio.payload is not None and vazio.payload != itr_2024
