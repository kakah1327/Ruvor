"""V-03, V-04 e a parte do V-05 do M1.7: o `has_risk` do item da busca (RF-03 a RF-06).

`has_risk` e "a execucao fechada mais recente do ativo e `ok` ou `partial`" -- a mesma que o
`/risk` devolve como `latest`. As cinco fixtures do V-03 separam as tres leituras erradas:

- "algum `ok`" em vez do ultimo fechado: o `QQFA3` (ultimo fechado `failed`, um `ok` mais
  antigo) vira verdadeiro;
- contar a `running`: o `QQRU3` (so `running`) vira verdadeiro;
- "a execucao mais recente, de qualquer status": o `QQE23` (ultimo fechado `ok`, uma `running`
  mais nova -- o E2 da tela) vira falso.

Nas duas fixtures com mais de uma execucao, a mais recente e gravada **primeiro**: a ordem
por `id` daria a outra, e so a ordem por `calculated_at` acerta.

O parametro e comparado como texto (RF-04): `true` e `false`, em minusculas; o resto e 400
`invalid_parameter`. A conversao permissiva do DRF aceitaria `True` e `1`.

Os tickers sao inventados e comecam por `QQ`, para nao casar com o IBOV da migration de
dados, que nao tem execucao e entra nas listas sem `q`.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client
from rest_framework.test import APIClient

from apps.api.serializers import HAS_RISK_DESCRIPTION
from apps.assets.models import Asset, CollectionRun
from apps.risk.models import RiskRun
from tests.api.test_busca import _confere_400

pytestmark = pytest.mark.django_db

AGORA = datetime(2026, 9, 25, 13, 0, tzinfo=ZoneInfo("UTC"))
ANTES = AGORA - timedelta(days=1)

# a regra do RF-03, como o RF-06 a escreve
REGRA = "o último cálculo fechado terminou `ok` ou `partial`"

COM_RISCO = ["QQE23", "QQPA3"]
SEM_RISCO = ["QQFA3", "QQRU3", "QQSE3"]


def _ativo(ticker: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"Companhia {ticker}",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


def _execucao(asset: Asset, status: str, calculated_at: datetime) -> RiskRun:
    coleta = CollectionRun.objects.create(
        source="yahoo_chart",
        started_at=calculated_at - timedelta(minutes=10),
        finished_at=calculated_at - timedelta(minutes=9),
        status=CollectionRun.Status.OK,
    )
    return RiskRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=None
        if status == RiskRun.Status.RUNNING
        else calculated_at + timedelta(minutes=2),
        engine_version="0.3.0",
        seed=42,
        train_window_days=252,
        as_of_date=date(2026, 9, 25),
        first_price_date=date(2016, 9, 26),
        price_count=2480,
        train_count=252,
        test_count=2227,
        price_run=coleta,
        requested_by=None,
        status=status,
        requested_models=["historical", "parametric"],
        full_recompute=False,
    )


@pytest.fixture
def cinco() -> None:
    """As cinco fixtures do V-03."""
    _ativo("QQSE3")  # sem execucao

    _execucao(_ativo("QQRU3"), RiskRun.Status.RUNNING, AGORA)  # so `running`

    # ultimo fechado `failed`, com um `ok` mais antigo gravado depois
    falhou = _ativo("QQFA3")
    _execucao(falhou, RiskRun.Status.FAILED, AGORA)
    _execucao(falhou, RiskRun.Status.OK, ANTES)

    # ultimo fechado `partial`
    _execucao(_ativo("QQPA3"), RiskRun.Status.PARTIAL, AGORA)

    # o E2: ultimo fechado `ok`, com uma `running` mais nova gravada antes
    e2 = _ativo("QQE23")
    _execucao(e2, RiskRun.Status.RUNNING, AGORA)
    _execucao(e2, RiskRun.Status.OK, ANTES)


def _busca(client: Client, params: dict[str, str]) -> dict[str, Any]:
    resposta = client.get("/api/v1/assets", params)
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    return corpo


def _tickers(corpo: dict[str, Any]) -> list[str]:
    return [item["ticker"] for item in corpo["results"]]


# --- V-03: a anotacao -------------------------------------------------------------------


@pytest.mark.usefixtures("cinco")
def test_v03_so_o_ultimo_fechado_ok_ou_partial_tem_risco(client: Client) -> None:
    corpo = _busca(client, {"q": "QQ"})

    assert {item["ticker"]: item["has_risk"] for item in corpo["results"]} == {
        "QQE23": True,
        "QQPA3": True,
        "QQFA3": False,
        "QQRU3": False,
        "QQSE3": False,
    }


@pytest.mark.usefixtures("cinco")
def test_v03_o_has_risk_concorda_com_o_latest_do_risk(client: Client) -> None:
    # a mesma regra que a tela usa: `latest` presente e nao `failed`
    for item in _busca(client, {"q": "QQ"})["results"]:
        resposta = client.get(f"/api/v1/assets/{item['ticker']}/risk")
        assert resposta.status_code == 200, resposta.content
        latest = resposta.json()["latest"]
        mostra = latest is not None and latest["status"] in ("ok", "partial")
        assert item["has_risk"] is mostra, item["ticker"]


# --- V-04: o filtro ---------------------------------------------------------------------


@pytest.mark.usefixtures("cinco")
def test_v04_true_devolve_so_os_com_risco(client: Client) -> None:
    corpo = _busca(client, {"has_risk": "true"})

    assert _tickers(corpo) == COM_RISCO
    assert corpo["count"] == 2
    assert all(item["has_risk"] is True for item in corpo["results"])


@pytest.mark.usefixtures("cinco")
def test_v04_false_devolve_so_os_sem_risco(client: Client) -> None:
    corpo = _busca(client, {"has_risk": "false"})

    # o IBOV da migration de dados nao tem execucao
    assert _tickers(corpo) == ["IBOV", *SEM_RISCO]
    assert corpo["count"] == 4
    assert all(item["has_risk"] is False for item in corpo["results"])


@pytest.mark.usefixtures("cinco")
def test_v04_ausente_devolve_todos(client: Client) -> None:
    corpo = _busca(client, {})

    assert _tickers(corpo) == ["IBOV", *sorted(COM_RISCO + SEM_RISCO)]
    assert corpo["count"] == 6


@pytest.mark.usefixtures("cinco")
def test_v04_combina_com_q(client: Client) -> None:
    _execucao(_ativo("ZZPA3"), RiskRun.Status.OK, AGORA)  # com risco, nao casa o `q`

    assert _tickers(_busca(client, {"q": "QQ", "has_risk": "true"})) == COM_RISCO
    assert _tickers(_busca(client, {"q": "QQP", "has_risk": "true"})) == ["QQPA3"]
    assert _tickers(_busca(client, {"q": "QQP", "has_risk": "false"})) == []
    assert _tickers(_busca(client, {"has_risk": "true"})) == [*COM_RISCO, "ZZPA3"]


@pytest.mark.usefixtures("cinco")
def test_v04_count_e_depois_do_filtro_e_combina_com_a_paginacao(
    client: Client,
) -> None:
    corpo = _busca(client, {"has_risk": "false", "limit": "2", "offset": "1"})

    assert corpo["count"] == 4
    assert (corpo["limit"], corpo["offset"]) == (2, 1)
    assert _tickers(corpo) == SEM_RISCO[:2]


@pytest.mark.parametrize("valor", ["True", "TRUE", "1", "0", "sim", ""])
def test_v04_valor_fora_de_true_e_false_e_invalid_parameter(
    client: Client, debug: bool, valor: str
) -> None:
    resposta = client.get("/api/v1/assets", {"has_risk": valor})

    _confere_400(resposta.status_code, resposta.json(), "has_risk")


# --- V-05: o esquema --------------------------------------------------------------------


@pytest.fixture
def esquema() -> dict[str, Any]:
    resposta = APIClient().get("/api/v1/schema")
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    return corpo


def test_v05_o_parametro_has_risk_da_busca_tem_a_regra(esquema: dict[str, Any]) -> None:
    operacao = esquema["paths"]["/api/v1/assets"]["get"]
    assert operacao["operationId"] == "v1_assets_search"
    parametros = [p for p in operacao["parameters"] if p["name"] == "has_risk"]

    assert len(parametros) == 1
    parametro = parametros[0]
    assert parametro["in"] == "query"
    assert parametro.get("required", False) is False
    assert parametro["schema"] == {"type": "boolean"}
    assert REGRA in parametro["description"]
    assert HAS_RISK_DESCRIPTION in parametro["description"]


def test_v05_o_campo_has_risk_do_item_tem_a_regra(esquema: dict[str, Any]) -> None:
    item = esquema["components"]["schemas"]["AssetItem"]
    campo = item["properties"]["has_risk"]

    assert campo["type"] == "boolean"
    assert campo["readOnly"] is True
    assert REGRA in campo["description"]
    assert campo["description"] == HAS_RISK_DESCRIPTION


def test_v05_a_identidade_nao_ganha_has_risk(esquema: dict[str, Any]) -> None:
    identidade = esquema["components"]["schemas"]["AssetDetail"]

    assert "has_risk" not in identidade["properties"]
