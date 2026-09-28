"""V-12: a busca e a paginacao de `/api/v1/assets` (RF-12), e os parametros invalidos.

A ordem e `(grupo, ticker)`: ticker igual a `q`, prefixo de ticker, nome ou nome de pregao
contendo `q`. O cenario poe os ativos do grupo do nome **antes**, por ticker, dos do grupo do
ticker: uma ordem so por ticker os traria primeiro e reprova.

Os tickers sao inventados, para nao casar com o IBOV que a migration de dados grava.
Parametro invalido e 400 `invalid_parameter` com o nome dele em `details`, com `DEBUG`
ligado e desligado (a fixture `debug`, V-08).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client

from apps.assets.models import Asset

pytestmark = pytest.mark.django_db

AGORA = datetime(2026, 9, 25, 13, 0, tzinfo=ZoneInfo("UTC"))


def _ativo(ticker: str, name: str = "", trading_name: str = "") -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=name or f"Companhia {ticker}",
        trading_name=trading_name or ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


@pytest.fixture
def zeta() -> None:
    _ativo("ZETA3")
    _ativo("ZETA")
    _ativo("ZETA11")
    _ativo("AAAA3", name="Grupo Zeta S.A.")  # grupo do nome
    _ativo("BBBB3", trading_name="ZETAPAR")  # grupo do nome de pregao
    _ativo("CCCC3", name="Outra Companhia")  # nao casa


def _busca(client: Client, query: str) -> dict[str, Any]:
    resposta = client.get(f"/api/v1/assets{query}")
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    return corpo


def _tickers(corpo: dict[str, Any]) -> list[str]:
    return [item["ticker"] for item in corpo["results"]]


@pytest.mark.usefixtures("zeta")
def test_ordem_igual_prefixo_depois_nome(client: Client) -> None:
    corpo = _busca(client, "?q=%20%20zeta%20")  # aparado e sem distincao de caixa

    assert _tickers(corpo) == ["ZETA", "ZETA11", "ZETA3", "AAAA3", "BBBB3"]
    assert corpo["count"] == 5
    assert (corpo["limit"], corpo["offset"]) == (20, 0)


@pytest.mark.usefixtures("zeta")
def test_ticker_igual_vem_antes_do_nome_que_o_contem(client: Client) -> None:
    # AAAA3 casa pelo nome e vem, por ticker, antes de ZETA; o grupo o poe depois
    _ativo("AAAA4", name="Holding ZETA3")

    corpo = _busca(client, "?q=zeta3")

    assert _tickers(corpo) == ["ZETA3", "AAAA4"]
    assert corpo["count"] == 2


@pytest.mark.usefixtures("zeta")
def test_limit_e_offset_recortam_a_ordem_e_count_e_o_total(client: Client) -> None:
    corpo = _busca(client, "?q=zeta&limit=2&offset=1")

    assert _tickers(corpo) == ["ZETA11", "ZETA3"]
    assert (corpo["count"], corpo["limit"], corpo["offset"]) == (5, 2, 1)


@pytest.mark.usefixtures("zeta")
def test_offset_alem_do_fim_da_lista_vazia_com_o_total(client: Client) -> None:
    corpo = _busca(client, "?q=zeta&offset=50")

    assert corpo["results"] == []
    assert corpo["count"] == 5


@pytest.mark.usefixtures("zeta")
def test_q_sem_casamento_da_lista_vazia(client: Client) -> None:
    corpo = _busca(client, "?q=xyzw")

    assert corpo == {"count": 0, "limit": 20, "offset": 0, "results": []}


@pytest.mark.parametrize("query", ["", "?q=", "?q=%20%20"])
def test_q_vazio_ou_ausente_lista_o_catalogo_por_ticker_com_o_padrao(
    client: Client, query: str
) -> None:
    for i in range(25):
        _ativo(f"T{i:03d}3")

    corpo = _busca(client, query)

    todos = list(Asset.objects.order_by("ticker").values_list("ticker", flat=True))
    assert len(todos) > 20  # os 25 mais o IBOV da migration
    assert corpo["count"] == len(todos)
    assert (corpo["limit"], corpo["offset"]) == (20, 0)
    assert _tickers(corpo) == todos[:20]


@pytest.mark.parametrize("limit", ["1", "100"])
def test_limit_nas_bordas_e_aceito(client: Client, limit: str) -> None:
    for i in range(3):
        _ativo(f"T{i:03d}3")

    corpo = _busca(client, f"?q=T0&limit={limit}")

    assert corpo["limit"] == int(limit)
    assert len(corpo["results"]) == min(int(limit), 3)


@pytest.mark.parametrize(
    ("query", "parametro"),
    [
        ("?limit=0", "limit"),
        ("?limit=101", "limit"),
        ("?limit=abc", "limit"),
        ("?limit=", "limit"),
        ("?limit=1_0", "limit"),
        ("?limit=2.5", "limit"),
        ("?offset=-1", "offset"),
        ("?offset=abc", "offset"),
    ],
)
def test_limit_e_offset_invalidos_sao_invalid_parameter(
    client: Client, debug: bool, query: str, parametro: str
) -> None:
    resposta = client.get(f"/api/v1/assets{query}")

    _confere_400(resposta.status_code, resposta.json(), parametro)


@pytest.mark.parametrize(
    ("query", "parametro"),
    [
        ("?from=2026-13-01", "from"),
        ("?from=ontem", "from"),
        ("?to=2026-02-30", "to"),
        ("?from=", "from"),
        ("?from=2026-09-25&to=2026-09-24", "from"),
    ],
)
def test_from_e_to_invalidos_sao_invalid_parameter(
    client: Client, debug: bool, query: str, parametro: str
) -> None:
    _ativo("ZETA3")

    resposta = client.get(f"/api/v1/assets/ZETA3/prices{query}")

    _confere_400(resposta.status_code, resposta.json(), parametro)


def test_from_igual_a_to_e_aceito(client: Client) -> None:
    _ativo("ZETA3")

    resposta = client.get("/api/v1/assets/ZETA3/prices?from=2026-09-24&to=2026-09-24")

    assert resposta.status_code == 200, resposta.content


def _confere_400(status: int, corpo: dict[str, Any], parametro: str) -> None:
    assert status == 400, corpo
    assert set(corpo) == {"error"}
    assert set(corpo["error"]) == {"code", "message", "details"}
    assert corpo["error"]["code"] == "invalid_parameter"
    assert corpo["error"]["details"] == {"parameter": parametro}
    assert parametro in corpo["error"]["message"]
