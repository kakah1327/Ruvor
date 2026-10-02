"""V-02 do M1.7: a busca casa o nome e o nome de pregao sem distincao de acento (RF-02).

O lookup `unaccent` do Django e bilateral: aplica `UNACCENT` ao campo e ao valor procurado.
Por isso os dois sentidos -- acento so na consulta ("itaú" acha "ITAU") e acento so no dado
("locacao" acha "LOCAÇÃO") -- e o indice, que a migration de dados grava como "Índice
Bovespa". A mutacao que volta a `icontains` sem `unaccent` reprova aqui: "itaú", "locacao",
"indice" e "construcao" deixam de casar.

Os tickers sao inventados e nao comecam pelas letras procuradas, para que o casamento venha
do nome (grupo 2 do RF-12 do M1.6a), nunca do prefixo de ticker.
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


def _ativo(ticker: str, name: str, trading_name: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=name,
        trading_name=trading_name,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


@pytest.fixture
def acentos() -> None:
    _ativo("QQIT4", "ITAU UNIBANCO HOLDING S.A.", "QQIT")
    _ativo("QQAR3", "ARMAC LOCAÇÃO, LOGÍSTICA E SERVIÇOS S.A.", "QQAR")
    _ativo("QQCO3", "Companhia QQCO", "CONSTRUÇÃO QQ")  # o acento so no nome de pregao


def _tickers(client: Client, q: str) -> list[str]:
    resposta = client.get("/api/v1/assets", {"q": q})
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    tickers = [item["ticker"] for item in corpo["results"]]
    assert corpo["count"] == len(tickers)
    return tickers


@pytest.mark.usefixtures("acentos")
def test_acento_so_na_consulta_acha_o_nome_sem_acento(client: Client) -> None:
    assert _tickers(client, "itaú") == ["QQIT4"]
    assert _tickers(client, "ITAÚ UNIBANCO") == ["QQIT4"]


@pytest.mark.usefixtures("acentos")
def test_acento_so_no_dado_acha_a_consulta_sem_acento(client: Client) -> None:
    assert _tickers(client, "locacao") == ["QQAR3"]
    assert _tickers(client, "LOGISTICA E SERVICOS") == ["QQAR3"]


@pytest.mark.usefixtures("acentos")
def test_nome_de_pregao_tambem_sem_acento(client: Client) -> None:
    assert _tickers(client, "construcao") == ["QQCO3"]


@pytest.mark.parametrize("q", ["ÍNDICE", "indice", "Indice Bovespa", "índice"])
def test_o_indice_nos_dois_sentidos(client: Client, q: str) -> None:
    assert _tickers(client, q) == ["IBOV"]
