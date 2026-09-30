"""V-02: `GET /api/v1/assets/{ticker}/fundamentals` (M1.6c, RF-02).

O corpo e uma lista fechada: o teste confere as chaves **na ordem**, no indicador, no balanco
e nos pares — campo a mais, a menos ou fora de lugar reprova. A lista e escrita aqui, campo a
campo, e nao tirada do modelo: coluna nova em `gold.fundamental_indicator` pode nascer (a regra
"so cresce" dos contratos) sem entrar na rota.

`peers` e a comparacao **do proprio indicador**, a ligacao um-para-um do M3.2: com um
indicador antigo com comparacao e um mais novo sem (a segunda fase que falhou, RF-15 do M3.2),
a rota devolve o mais novo com `peers: null` — e nao a comparacao antiga.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client

from apps.assets.models import Asset, CollectionRun
from apps.fundamentals.models import (
    Company,
    FinancialStatement,
    FundamentalIndicator,
    PeerComparison,
)

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

pytestmark = pytest.mark.django_db

# 13h UTC = 10h em Sao Paulo: o instante sai no fuso de `TIME_ZONE`, com deslocamento
ANTIGO = datetime(2026, 9, 21, 13, 0, tzinfo=ZoneInfo("UTC"))
NOVO = datetime(2026, 9, 28, 13, 0, tzinfo=ZoneInfo("UTC"))

CHAVES = ["ticker", "indicator", "peers"]
CHAVES_INDICADOR = [
    "calculated_at",
    "statement",
    "account_plan",
    "scope",
    "revenue_ttm",
    "ebit_ttm",
    "net_income_ttm",
    "equity_parent",
    "total_assets",
    "gross_debt",
    "cash",
    "net_debt",
    "net_margin",
    "ebit_margin",
    "roe",
    "net_debt_to_equity",
    "price_date",
    "close",
    "shares_total",
    "eps",
    "bvps",
    "pe",
    "pb",
    "per_share_missing",
    "market_cap",
    "market_cap_missing",
]
CHAVES_BALANCO = ["reference_date", "source", "scope"]
INDICADORES_COMPARADOS = [
    "roe",
    "net_margin",
    "ebit_margin",
    "net_debt_to_equity",
    "pe",
    "pb",
]
CHAVES_PARES = [
    "peer_level",
    "group_sector",
    "group_subsector",
    "group_segment",
    *INDICADORES_COMPARADOS,
]
CHAVES_POSICAO = ["median", "percentile", "count"]


def _ok(resposta: _MonkeyPatchedWSGIResponse) -> dict[str, Any]:
    assert resposta.status_code == 200, resposta.content
    assert resposta["Content-Type"] == "application/json"
    corpo: dict[str, Any] = resposta.json()
    return corpo


def _coleta() -> CollectionRun:
    return CollectionRun.objects.create(
        source="teste", started_at=ANTIGO, status=CollectionRun.Status.OK
    )


def _ativo(ticker: str, code_cvm: str | None = "9512") -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        code_cvm=code_cvm,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=ANTIGO,
        updated_at=ANTIGO,
    )


def _balanco(
    reference_date: date, source: str = "itr", code_cvm: str = "9512"
) -> FinancialStatement:
    run = _coleta()
    company, _ = Company.objects.get_or_create(
        code_cvm=code_cvm,
        defaults={
            "cnpj": "33000167000101",
            "name": "PETROLEO BRASILEIRO S.A. PETROBRAS",
            "account_plan": "general",
            "source_reference_date": reference_date,
            "run": run,
            "updated_at": ANTIGO,
        },
    )
    return FinancialStatement.objects.create(
        company=company,
        reference_date=reference_date,
        source=source,
        version=1,
        scope="consolidated",
        account_plan="general",
        share_composition=True,
        run=run,
        updated_at=ANTIGO,
    )


def _indicador(
    asset: Asset,
    calculated_at: datetime,
    statement: FinancialStatement,
    **extra: Any,
) -> FundamentalIndicator:
    valores: dict[str, Any] = {
        "account_plan": "general",
        "scope": "consolidated",
        "revenue_ttm": Decimal("500000000.00"),
        "ebit_ttm": Decimal("120000000.00"),
        "net_income_ttm": Decimal("80000000.00"),
        "equity_parent": Decimal("400000000.00"),
        "total_assets": Decimal("900000000.00"),
        "gross_debt": Decimal("300000000.00"),
        "cash": Decimal("100000000.00"),
        "net_debt": Decimal("200000000.00"),
        "net_margin": Decimal("0.1600000000"),
        "ebit_margin": Decimal("0.2400000000"),
        "roe": Decimal("0.2000000000"),
        "net_debt_to_equity": Decimal("0.5000000000"),
        "price_date": date(2026, 9, 25),
        "close": Decimal("38.500000"),
        "shares_total": 13_000_000,
        "eps": Decimal("6.153846"),
        "bvps": Decimal("30.769231"),
        "pe": Decimal("6.256250"),
        "pb": Decimal("1.251250"),
        "per_share_missing": None,
        "market_cap": None,
        "market_cap_missing": "missing_class_price",
    }
    valores.update(extra)
    return FundamentalIndicator.objects.create(
        asset=asset, calculated_at=calculated_at, statement=statement, **valores
    )


def _comparacao(indicator: FundamentalIndicator, **extra: Any) -> PeerComparison:
    valores: dict[str, Any] = {
        "peer_level": "segment",
        "group_sector": "Petróleo, Gás e Biocombustíveis",
        "group_subsector": "Petróleo, Gás e Biocombustíveis",
        "group_segment": "Exploração, Refino e Distribuição",
        # valores distintos por indicador: a troca de uma coluna por outra aparece
        "roe_peer_median": Decimal("0.1100000000"),
        "roe_percentile": Decimal("1.0000"),
        "roe_peer_count": 8,
        "net_margin_peer_median": Decimal("0.0700000000"),
        "net_margin_percentile": Decimal("0.8571"),
        "net_margin_peer_count": 8,
        "ebit_margin_peer_median": Decimal("0.1300000000"),
        "ebit_margin_percentile": Decimal("0.6667"),
        "ebit_margin_peer_count": 7,
        "net_debt_to_equity_peer_median": Decimal("0.4900000000"),
        "net_debt_to_equity_percentile": Decimal("0.5000"),
        "net_debt_to_equity_peer_count": 3,
        "pe_peer_median": None,
        "pe_percentile": None,
        "pe_peer_count": 1,
        "pb_peer_median": None,
        "pb_percentile": None,
        "pb_peer_count": None,
    }
    valores.update(extra)
    return PeerComparison.objects.create(
        indicator=indicator,
        asset=indicator.asset,
        calculated_at=indicator.calculated_at,
        **valores,
    )


# --- o corpo --------------------------------------------------------------------------


def test_v02_o_corpo_inteiro_com_indicador_e_pares(client: Client) -> None:
    petr = _ativo("PETR4")
    indicador = _indicador(petr, NOVO, _balanco(date(2026, 6, 30)))
    _comparacao(indicador)

    corpo = _ok(client.get("/api/v1/assets/petr4/fundamentals"))

    assert list(corpo) == CHAVES
    assert corpo["ticker"] == "PETR4"
    ind = corpo["indicator"]
    assert list(ind) == CHAVES_INDICADOR
    assert list(ind["statement"]) == CHAVES_BALANCO
    assert ind["statement"] == {
        "reference_date": "2026-06-30",
        "source": "itr",
        "scope": "consolidated",
    }
    assert ind["calculated_at"] == "2026-09-28T10:00:00-03:00"
    assert ind["account_plan"] == "general"
    assert ind["revenue_ttm"] == "500000000.00"  # decimal como string, com as casas
    assert ind["roe"] == "0.2000000000"
    assert ind["price_date"] == "2026-09-25"
    assert ind["close"] == "38.500000"
    assert ind["shares_total"] == 13_000_000
    assert ind["pe"] == "6.256250"
    assert ind["per_share_missing"] is None
    assert ind["market_cap"] is None
    assert ind["market_cap_missing"] == "missing_class_price"

    pares = corpo["peers"]
    assert list(pares) == CHAVES_PARES
    assert pares["peer_level"] == "segment"
    assert pares["group_segment"] == "Exploração, Refino e Distribuição"
    for nome in INDICADORES_COMPARADOS:
        assert list(pares[nome]) == CHAVES_POSICAO, nome
    assert pares["roe"] == {
        "median": "0.1100000000",
        "percentile": "1.0000",
        "count": 8,
    }
    assert pares["net_margin"] == {
        "median": "0.0700000000",
        "percentile": "0.8571",
        "count": 8,
    }
    assert pares["ebit_margin"] == {
        "median": "0.1300000000",
        "percentile": "0.6667",
        "count": 7,
    }
    assert pares["net_debt_to_equity"] == {
        "median": "0.4900000000",
        "percentile": "0.5000",
        "count": 3,
    }
    assert pares["pe"] == {"median": None, "percentile": None, "count": 1}
    assert pares["pb"] == {"median": None, "percentile": None, "count": None}


def test_v02_as_casas_da_mediana_sao_as_da_coluna(client: Client) -> None:
    # `pe` e `pb` tem seis casas; as fracoes, dez
    petr = _ativo("PETR4")
    indicador = _indicador(petr, NOVO, _balanco(date(2026, 6, 30)))
    _comparacao(
        indicador,
        pe_peer_median=Decimal("7.25"),
        pe_percentile=Decimal("0.25"),
        pe_peer_count=5,
    )
    pares = _ok(client.get("/api/v1/assets/PETR4/fundamentals"))["peers"]
    assert pares["pe"] == {"median": "7.250000", "percentile": "0.2500", "count": 5}


def test_v02_o_indice_nao_tem_indicador(client: Client) -> None:
    # o IBOV vem da migration do catalogo
    corpo = _ok(client.get("/api/v1/assets/IBOV/fundamentals"))
    assert corpo == {"ticker": "IBOV", "indicator": None, "peers": None}


def test_v02_acao_sem_indicador(client: Client) -> None:
    _ativo("AZEV11", code_cvm=None)
    corpo = _ok(client.get("/api/v1/assets/AZEV11/fundamentals"))
    assert corpo == {"ticker": "AZEV11", "indicator": None, "peers": None}


def test_v02_o_indicador_de_maior_calculated_at(client: Client) -> None:
    petr = _ativo("PETR4")
    balanco = _balanco(date(2026, 6, 30))
    # criado fora de ordem: o novo primeiro, o antigo depois
    _indicador(petr, NOVO, balanco, roe=Decimal("0.3000000000"))
    _indicador(petr, ANTIGO, balanco, roe=Decimal("0.1000000000"))
    ind = _ok(client.get("/api/v1/assets/PETR4/fundamentals"))["indicator"]
    assert ind["calculated_at"] == "2026-09-28T10:00:00-03:00"
    assert ind["roe"] == "0.3000000000"


def test_v02_o_novo_sem_comparacao_da_peers_nulo_e_nao_a_antiga(
    client: Client,
) -> None:
    petr = _ativo("PETR4")
    balanco = _balanco(date(2026, 6, 30))
    antigo = _indicador(petr, ANTIGO, balanco, roe=Decimal("0.1000000000"))
    _comparacao(antigo)
    _indicador(petr, NOVO, balanco, roe=Decimal("0.3000000000"))
    # o cenario: a comparacao mais recente do ativo existe, e e a do indicador antigo
    assert PeerComparison.objects.filter(asset=petr).count() == 1

    corpo = _ok(client.get("/api/v1/assets/PETR4/fundamentals"))
    assert corpo["indicator"]["calculated_at"] == "2026-09-28T10:00:00-03:00"
    assert corpo["indicator"]["roe"] == "0.3000000000"
    assert corpo["peers"] is None


def test_v02_com_os_dois_comparados_vem_a_do_proprio_indicador(
    client: Client,
) -> None:
    petr = _ativo("PETR4")
    balanco = _balanco(date(2026, 6, 30))
    _comparacao(
        _indicador(petr, ANTIGO, balanco), peer_level="subsector", roe_peer_count=4
    )
    _comparacao(_indicador(petr, NOVO, balanco), peer_level="segment")
    pares = _ok(client.get("/api/v1/assets/PETR4/fundamentals"))["peers"]
    assert pares["peer_level"] == "segment"
    assert pares["roe"]["count"] == 8


def test_v02_o_banco_com_os_nulos_do_plano(client: Client) -> None:
    itub = _ativo("ITUB4", code_cvm="19348")
    balanco = _balanco(date(2026, 6, 30), source="dfp", code_cvm="19348")
    nulos = {
        "revenue_ttm": None,
        "ebit_ttm": None,
        "net_margin": None,
        "ebit_margin": None,
        "gross_debt": None,
        "cash": None,
        "net_debt": None,
        "net_debt_to_equity": None,
    }
    _indicador(itub, NOVO, balanco, account_plan="bank", **nulos)
    ind = _ok(client.get("/api/v1/assets/ITUB4/fundamentals"))["indicator"]
    assert ind["account_plan"] == "bank"
    assert ind["statement"]["source"] == "dfp"
    for nome in nulos:
        assert ind[nome] is None, nome


@pytest.mark.parametrize("ticker", ["XPTO3", "xpto3"])
def test_v02_ticker_ausente_e_404(client: Client, debug: bool, ticker: str) -> None:
    resposta = client.get(f"/api/v1/assets/{ticker}/fundamentals")
    assert resposta.status_code == 404
    assert resposta.json() == {
        "error": {
            "code": "asset_not_found",
            "message": "Ativo XPTO3 não existe.",
            "details": {"ticker": "XPTO3"},
        }
    }


# --- o esquema (V-05) ---------------------------------------------------------------


def test_v05_as_duas_rotas_no_esquema_com_ref(client: Client) -> None:
    esquema = _ok_esquema(client)
    for caminho, nome in (
        ("/api/v1/assets/{ticker}/fundamentals", "FundamentalsOut"),
        ("/api/v1/assets/{ticker}/disclosures", "DisclosuresOut"),
    ):
        respostas = esquema["paths"][caminho]["get"]["responses"]
        sucessos = [codigo for codigo in respostas if codigo.startswith("2")]
        assert sucessos == ["200"], caminho
        assert respostas["200"]["content"]["application/json"]["schema"] == {
            "$ref": f"#/components/schemas/{nome}"
        }


def _ok_esquema(client: Client) -> dict[str, Any]:
    resposta = client.get("/api/v1/schema")
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    return corpo
