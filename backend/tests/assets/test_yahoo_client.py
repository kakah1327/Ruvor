"""O cliente real do Yahoo, com `urlopen` falso injetado no mesmo ponto que a guarda usa.

Nenhum teste aqui sai para a rede (RF-14): o `urlopen` e substituido por um objeto que
devolve corpos das fixtures ou levanta o erro programado, e registra as `Request` que
recebeu. `sleep` e substituido por um registrador, para provar a repeticao sem esperar.
"""

from __future__ import annotations

import email.message
import importlib.metadata
import io
import json
import urllib.error
import urllib.request
from types import TracebackType

import pytest

from apps.assets.yahoo import ChartResponse, YahooClient, YahooClientError
from tests.assets.conftest import FakeYahoo, fixture_json

CHART_URL = "https://query2.finance.yahoo.com/v8/finance/chart/"


class FakeResponse:
    """O que `urlopen` devolve num 2xx: gerenciador de contexto com `status` e `read()`."""

    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

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
        return self._body


class FakeUrlopen:
    """Responde, em ordem, com cada item de `responses`: corpo (bytes) ou excecao."""

    def __init__(self, responses: list[bytes | Exception]) -> None:
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
        return FakeResponse(response)


def body(nome: str) -> bytes:
    return json.dumps(fixture_json(nome, subdir="yahoo")).encode("utf-8")


def http_error(code: int, body: bytes | None = None) -> urllib.error.HTTPError:
    """`HTTPError` como o `urlopen` levanta; `body` e o corpo que `read()` devolve."""
    fp = io.BytesIO(body) if body is not None else None
    return urllib.error.HTTPError(
        "https://exemplo.invalido", code, "erro", email.message.Message(), fp
    )


@pytest.fixture
def sleeps() -> list[float]:
    """Registro do `sleep` falso que `make_client` entrega ao construtor do cliente."""
    registrados: list[float] = []
    return registrados


def make_client(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[bytes | Exception],
    sleeps: list[float],
) -> tuple[YahooClient, FakeUrlopen]:
    fake = FakeUrlopen(responses)
    monkeypatch.setattr("urllib.request.urlopen", fake)
    return YahooClient(sleep=sleeps.append), fake


def test_rf14_serie_de_dez_anos_vira_chartresponse_200_com_result(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [body("PETR4_10y")], sleeps)

    response = client.chart("PETR4.SA", 1474426800, 1758510000)

    assert isinstance(response, ChartResponse)
    assert response.http_status == 200
    assert response.payload == fixture_json("PETR4_10y", subdir="yahoo")
    result = response.payload["chart"]["result"][0]
    assert len(result["timestamp"]) == 2491
    assert len(result["events"]["dividends"]) == 34
    assert fake.timeouts == [30.0]
    assert sleeps == []


def test_rf14_404_com_corpo_json_e_resposta_nao_excecao(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(
        monkeypatch, [http_error(404, body("not_found"))], sleeps
    )

    response = client.chart("XXXX9.SA", 1474426800, 1758510000)

    assert response == ChartResponse(404, fixture_json("not_found", subdir="yahoo"))
    assert response.payload["chart"]["result"] is None
    assert response.payload["chart"]["error"]["code"] == "Not Found"
    assert len(fake.requests) == 1
    assert sleeps == []


def test_rf14_corpo_nao_json_em_200_levanta_sem_repetir(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [b"<html>bloqueado</html>"], sleeps)

    with pytest.raises(YahooClientError, match="corpo nao e JSON"):
        client.chart("PETR4.SA", 1474426800, 1758510000)

    assert len(fake.requests) == 1
    assert sleeps == []


def test_rf14_corpo_nao_json_em_4xx_levanta_sem_repetir(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(
        monkeypatch, [http_error(429, b"Too Many Requests")], sleeps
    )

    with pytest.raises(YahooClientError, match="HTTP 429, corpo nao e JSON"):
        client.chart("PETR4.SA", 1474426800, 1758510000)

    assert len(fake.requests) == 1
    assert sleeps == []


def test_rf14_json_que_nao_e_objeto_levanta(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [b"[1, 2, 3]"], sleeps)

    with pytest.raises(YahooClientError, match="esperava objeto JSON, veio list"):
        client.chart("PETR4.SA", 1474426800, 1758510000)

    assert len(fake.requests) == 1


def test_repeticao_falha_duas_vezes_com_5xx_e_responde_na_terceira(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[bytes | Exception] = [
        http_error(503),
        http_error(500),
        body("PETR4_tail"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    response = client.chart("PETR4.SA", 1756695600, 1758510000)

    assert response.http_status == 200
    assert response.payload == fixture_json("PETR4_tail", subdir="yahoo")
    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_repeticao_tambem_cobre_timeout_e_erro_de_rede(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[bytes | Exception] = [
        TimeoutError("timed out"),
        urllib.error.URLError("conexao recusada"),
        body("PETR4_tail"),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    response = client.chart("PETR4.SA", 1756695600, 1758510000)

    assert response.http_status == 200
    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_repeticao_desiste_apos_tres_5xx(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    responses: list[bytes | Exception] = [
        http_error(500),
        http_error(502),
        http_error(503),
    ]
    client, fake = make_client(monkeypatch, responses, sleeps)

    with pytest.raises(YahooClientError, match="falhou 3 vezes"):
        client.chart("PETR4.SA", 1474426800, 1758510000)

    assert len(fake.requests) == 3
    assert sleeps == [1, 2]


def test_rf14_url_escapa_o_simbolo_e_pede_dividendos_e_desdobramentos(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [body("BVSP_10y")], sleeps)

    client.chart("^BVSP", 1474426800, 1758510000)

    url = fake.requests[0].full_url
    assert url.startswith(f"{CHART_URL}%5EBVSP?"), url
    assert "%5EBVSP" in url
    assert "^" not in url
    assert "period1=1474426800" in url
    assert "period2=1758510000" in url
    assert "interval=1d" in url
    assert "events=div%2Csplits" in url


def test_rf14_user_agent_presente_na_request(
    monkeypatch: pytest.MonkeyPatch, sleeps: list[float]
) -> None:
    client, fake = make_client(monkeypatch, [body("PETR4_tail")], sleeps)

    client.chart("PETR4.SA", 1756695600, 1758510000)

    esperado = f"Ruvor/{importlib.metadata.version('ruvor-backend')}"
    assert fake.requests[0].get_header("User-agent") == esperado


def test_rf14_fake_yahoo_registra_chamadas_e_reprova_cenario_mal_montado() -> None:
    ok = ChartResponse(200, fixture_json("PETR4_tail", subdir="yahoo"))
    fake = FakeYahoo({"PETR4.SA": [ok, YahooClientError("programada")]})

    assert fake.chart("PETR4.SA", 1, 2) is ok
    with pytest.raises(YahooClientError, match="programada"):
        fake.chart("PETR4.SA", 3, 4)
    with pytest.raises(AssertionError, match="esgotaram"):
        fake.chart("PETR4.SA", 5, 6)
    with pytest.raises(AssertionError, match="nao tem resposta"):
        fake.chart("VALE3.SA", 7, 8)
    assert fake.calls == [
        ("PETR4.SA", 1, 2),
        ("PETR4.SA", 3, 4),
        ("PETR4.SA", 5, 6),
        ("VALE3.SA", 7, 8),
    ]
