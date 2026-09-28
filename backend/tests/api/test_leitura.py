"""V-11: as rotas de leitura, uma a uma, com o corpo inteiro (RF-11).

Cada corpo e uma lista fechada: o teste confere o **conjunto** de chaves por igualdade, nos
objetos aninhados tambem — campo a mais ou a menos reprova. As colunas de metrica vem de
`BehaviorMetric._meta`, nao de uma lista copiada: coluna nova no modelo sem campo na rota
reprova. O ticker entra em minusculas e acha o ativo; ticker ausente e 404 `asset_not_found`,
com `DEBUG` ligado e desligado (a fixture `debug`, V-08).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client

from apps.analytics.models import BehaviorMetric, ReturnHistogramBin
from apps.assets.models import Asset, CollectionRun, CorporateEvent, Price

if TYPE_CHECKING:
    # so existe nos stubs: e o tipo que o cliente de teste devolve
    from django.test.client import _MonkeyPatchedWSGIResponse

pytestmark = pytest.mark.django_db

# 13h UTC = 10h em Sao Paulo: o instante sai no fuso de `TIME_ZONE`, com deslocamento
CALCULADO = datetime(2026, 9, 25, 13, 0, tzinfo=ZoneInfo("UTC"))

CHAVES_ITEM = {
    "ticker",
    "name",
    "trading_name",
    "kind",
    "sector",
    "status",
    "has_prices",
}
CHAVES_ATIVO = {
    "ticker",
    "name",
    "trading_name",
    "kind",
    "sector",
    "subsector",
    "segment",
    "listing_segment",
    "status",
    "has_prices",
    "last_price",
}
CHAVES_ULTIMO_PRECO = {"date", "close", "adj_close"}
CHAVES_PRECO = {"date", "open", "high", "low", "close", "adj_close", "volume"}
CHAVES_EVENTO = {"date", "kind", "amount", "numerator", "denominator"}
CHAVES_BALDE = {"bin_index", "lower_bound", "upper_bound", "count"}
CABECALHO_METRICA = {"calculated_at", "as_of_date", "first_price_date", "price_count"}


def _colunas_de_metrica() -> set[str]:
    """As colunas de metrica do modelo: todas as concretas menos `id`, `asset` e o cabecalho."""
    nomes = {f.name for f in BehaviorMetric._meta.concrete_fields}
    return nomes - {"id", "asset"} - CABECALHO_METRICA


def _ok(resposta: _MonkeyPatchedWSGIResponse) -> dict[str, Any]:
    assert resposta.status_code == 200, resposta.content
    assert resposta["Content-Type"] == "application/json"
    corpo: dict[str, Any] = resposta.json()
    return corpo


def _coleta() -> CollectionRun:
    return CollectionRun.objects.create(
        source="teste", started_at=CALCULADO, status=CollectionRun.Status.OK
    )


def _ativo(ticker: str, **extra: Any) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=CALCULADO,
        updated_at=CALCULADO,
        **extra,
    )


def _precos(asset: Asset, dias: list[date]) -> None:
    run = _coleta()
    for i, dia in enumerate(dias):
        base = Decimal(30 + i)
        Price.objects.create(
            asset=asset,
            date=dia,
            open=base,
            high=base + 1,
            low=base - 1,
            close=base + Decimal("0.5"),
            adj_close=base + Decimal("0.25"),
            volume=1000 + i,
            log_return=None if i == 0 else Decimal("0.01"),
            run=run,
            updated_at=CALCULADO,
        )


def _metrica(asset: Asset, calculated_at: datetime, **extra: Any) -> BehaviorMetric:
    valores: dict[str, Any] = {
        nome: Decimal("0.1234567890") for nome in _colunas_de_metrica()
    }
    valores.update(
        as_of_date=date(2026, 9, 24),
        first_price_date=date(2016, 9, 26),
        price_count=2480,
        max_drawdown_peak_date=date(2024, 1, 2),
        max_drawdown_trough_date=date(2024, 3, 4),
        max_drawdown_recovery_date=None,
        max_drawdown_recovery_sessions=None,
        benchmark_observations=1200,
        statistical_observations=2400,
        dividends_12m=Decimal("1.500000"),
        dividend_payments_12m=4,
        avg_volume_21d=Decimal("123456.78"),
        avg_volume_252d=Decimal("234567.89"),
    )
    valores.update(extra)
    metrica = BehaviorMetric.objects.create(
        asset=asset, calculated_at=calculated_at, **valores
    )
    # fora de ordem de proposito: a rota entrega por `bin_index`
    for indice in reversed(range(42)):
        ReturnHistogramBin.objects.create(
            metric=metrica,
            bin_index=indice,
            lower_bound=None if indice == 0 else Decimal(indice - 21) / 100,
            upper_bound=None if indice == 41 else Decimal(indice - 20) / 100,
            count=indice,
        )
    return metrica


# --- /assets/{ticker} ------------------------------------------------------------------


def test_ativo_em_minusculas_acha_o_ativo_com_o_ultimo_pregao(client: Client) -> None:
    ativo = _ativo(
        "ITUB4",
        sector="Financeiro",
        subsector="Intermediários Financeiros",
        segment="Bancos",
        listing_segment="N1",
    )
    _precos(ativo, [date(2026, 9, 22), date(2026, 9, 24), date(2026, 9, 23)])

    corpo = _ok(client.get("/api/v1/assets/itub4"))

    assert set(corpo) == CHAVES_ATIVO
    assert set(corpo["last_price"]) == CHAVES_ULTIMO_PRECO
    assert corpo == {
        "ticker": "ITUB4",
        "name": "ITUB4 S.A.",
        "trading_name": "ITUB4",
        "kind": "stock",
        "sector": "Financeiro",
        "subsector": "Intermediários Financeiros",
        "segment": "Bancos",
        "listing_segment": "N1",
        "status": "active",
        "has_prices": True,
        # o de maior data, nao o ultimo gravado; decimal como string
        "last_price": {
            "date": "2026-09-24",
            "close": "31.500000",
            "adj_close": "31.250000",
        },
    }


def test_ativo_sem_preco_tem_last_price_nulo(client: Client) -> None:
    _ativo("SEMP3")

    corpo = _ok(client.get("/api/v1/assets/SEMP3"))

    assert set(corpo) == CHAVES_ATIVO
    assert corpo["has_prices"] is False
    assert corpo["last_price"] is None
    assert corpo["sector"] is None
    assert corpo["listing_segment"] is None


@pytest.mark.parametrize("sufixo", ["", "/prices", "/events", "/metrics"])
def test_ticker_ausente_e_asset_not_found(
    client: Client, debug: bool, sufixo: str
) -> None:
    resposta = client.get(f"/api/v1/assets/zzzz9{sufixo}")

    assert resposta.status_code == 404, resposta.content
    assert resposta["Content-Type"] == "application/json"
    assert resposta.json() == {
        "error": {
            "code": "asset_not_found",
            "message": "Ativo ZZZZ9 não existe.",
            "details": {"ticker": "ZZZZ9"},
        }
    }


# --- /assets (o item da busca; a ordem e a paginacao estao em test_busca.py) -----------


def test_busca_devolve_o_corpo_e_o_item_inteiros(client: Client) -> None:
    ativo = _ativo("ITUB4", sector="Financeiro")
    _precos(ativo, [date(2026, 9, 24)])

    corpo = _ok(client.get("/api/v1/assets?q=itub4"))

    assert set(corpo) == {"count", "limit", "offset", "results"}
    assert corpo["count"] == 1
    assert [set(item) for item in corpo["results"]] == [CHAVES_ITEM]
    assert corpo["results"] == [
        {
            "ticker": "ITUB4",
            "name": "ITUB4 S.A.",
            "trading_name": "ITUB4",
            "kind": "stock",
            "sector": "Financeiro",
            "status": "active",
            "has_prices": True,
        }
    ]


def test_busca_acha_o_indice_sem_preco(client: Client) -> None:
    # o IBOV vem da migration de dados, sem preco
    corpo = _ok(client.get("/api/v1/assets?q=ibov"))

    assert [item["ticker"] for item in corpo["results"]] == ["IBOV"]
    assert corpo["results"][0]["kind"] == "index"
    assert corpo["results"][0]["has_prices"] is False


# --- /prices -----------------------------------------------------------------------------


def test_precos_sem_intervalo_devolvem_a_serie_inteira(client: Client) -> None:
    ativo = _ativo("ITUB4")
    _precos(ativo, [date(2026, 9, 23), date(2026, 9, 21), date(2026, 9, 22)])

    corpo = _ok(client.get("/api/v1/assets/itub4/prices"))

    assert set(corpo) == {"ticker", "from", "to", "results"}
    assert corpo["ticker"] == "ITUB4"
    assert corpo["from"] is None
    assert corpo["to"] is None
    assert all(set(p) == CHAVES_PRECO for p in corpo["results"])
    assert [p["date"] for p in corpo["results"]] == [
        "2026-09-21",
        "2026-09-22",
        "2026-09-23",
    ]
    assert corpo["results"][0] == {
        "date": "2026-09-21",
        "open": "31.000000",
        "high": "32.000000",
        "low": "30.000000",
        "close": "31.500000",
        "adj_close": "31.250000",
        "volume": 1001,
    }


def test_precos_com_intervalo_fechado_nas_duas_pontas(client: Client) -> None:
    ativo = _ativo("ITUB4")
    _precos(ativo, [date(2026, 9, d) for d in (21, 22, 23, 24, 25)])

    corpo = _ok(client.get("/api/v1/assets/ITUB4/prices?from=2026-09-22&to=2026-09-24"))

    assert set(corpo) == {"ticker", "from", "to", "results"}
    assert corpo["from"] == "2026-09-22"
    assert corpo["to"] == "2026-09-24"
    assert [p["date"] for p in corpo["results"]] == [
        "2026-09-22",
        "2026-09-23",
        "2026-09-24",
    ]


def test_precos_so_com_from_ou_so_com_to(client: Client) -> None:
    ativo = _ativo("ITUB4")
    _precos(ativo, [date(2026, 9, d) for d in (21, 22, 23)])

    so_from = _ok(client.get("/api/v1/assets/ITUB4/prices?from=2026-09-22"))
    so_to = _ok(client.get("/api/v1/assets/ITUB4/prices?to=2026-09-22"))

    assert (so_from["from"], so_from["to"]) == ("2026-09-22", None)
    assert [p["date"] for p in so_from["results"]] == ["2026-09-22", "2026-09-23"]
    assert (so_to["from"], so_to["to"]) == (None, "2026-09-22")
    assert [p["date"] for p in so_to["results"]] == ["2026-09-21", "2026-09-22"]


def test_precos_de_um_ativo_nao_trazem_os_de_outro(client: Client) -> None:
    _precos(_ativo("ITUB4"), [date(2026, 9, 21)])
    _precos(_ativo("PETR4"), [date(2026, 9, 22)])

    corpo = _ok(client.get("/api/v1/assets/ITUB4/prices"))

    assert [p["date"] for p in corpo["results"]] == ["2026-09-21"]


# --- /events -----------------------------------------------------------------------------


def test_eventos_devolvem_provento_e_desdobramento(client: Client) -> None:
    ativo = _ativo("ITUB4")
    run = _coleta()
    CorporateEvent.objects.create(
        asset=ativo,
        date=date(2025, 3, 10),
        kind=CorporateEvent.Kind.SPLIT,
        numerator=Decimal("11"),
        denominator=Decimal("10"),
        run=run,
    )
    CorporateEvent.objects.create(
        asset=ativo,
        date=date(2024, 12, 2),
        kind=CorporateEvent.Kind.DIVIDEND,
        amount=Decimal("0.017500"),
        run=run,
    )
    CorporateEvent.objects.create(
        asset=_ativo("PETR4"),
        date=date(2024, 12, 3),
        kind=CorporateEvent.Kind.DIVIDEND,
        amount=Decimal("1"),
        run=run,
    )

    corpo = _ok(client.get("/api/v1/assets/itub4/events"))

    assert set(corpo) == {"ticker", "results"}
    assert corpo["ticker"] == "ITUB4"
    assert all(set(e) == CHAVES_EVENTO for e in corpo["results"])
    assert corpo["results"] == [
        {
            "date": "2024-12-02",
            "kind": "dividend",
            "amount": "0.017500",
            "numerator": None,
            "denominator": None,
        },
        {
            "date": "2025-03-10",
            "kind": "split",
            "amount": None,
            "numerator": "11.0000",
            "denominator": "10.0000",
        },
    ]


def test_eventos_de_ativo_sem_evento_e_lista_vazia(client: Client) -> None:
    _ativo("ITUB4")

    corpo = _ok(client.get("/api/v1/assets/ITUB4/events"))

    assert corpo == {"ticker": "ITUB4", "results": []}


# --- /metrics ----------------------------------------------------------------------------


def test_as_colunas_de_metrica_sao_26() -> None:
    # guarda do teste abaixo: a lista que ele confere nao pode ter encolhido por engano
    assert len(_colunas_de_metrica()) == 26


def test_metricas_devolvem_a_ultima_linha_com_as_colunas_e_os_baldes(
    client: Client,
) -> None:
    ativo = _ativo("ITUB4")
    _metrica(ativo, CALCULADO - timedelta(days=1), price_count=1)
    _metrica(ativo, CALCULADO)

    corpo = _ok(client.get("/api/v1/assets/itub4/metrics"))

    assert set(corpo) == {"ticker", "metric"}
    assert corpo["ticker"] == "ITUB4"
    metrica = corpo["metric"]
    assert set(metrica) == CABECALHO_METRICA | _colunas_de_metrica() | {"histogram"}
    # a ultima linha, nao a primeira; instante no fuso de TIME_ZONE, com deslocamento
    assert metrica["calculated_at"] == "2026-09-25T10:00:00-03:00"
    assert metrica["price_count"] == 2480
    assert metrica["as_of_date"] == "2026-09-24"
    assert metrica["first_price_date"] == "2016-09-26"
    assert metrica["return_1m"] == "0.1234567890"
    assert metrica["max_drawdown_peak_date"] == "2024-01-02"
    assert metrica["max_drawdown_recovery_date"] is None
    assert metrica["max_drawdown_recovery_sessions"] is None
    assert metrica["benchmark_observations"] == 1200
    assert metrica["dividends_12m"] == "1.500000"
    assert metrica["avg_volume_21d"] == "123456.78"

    baldes = metrica["histogram"]
    assert len(baldes) == 42
    assert all(set(b) == CHAVES_BALDE for b in baldes)
    assert [b["bin_index"] for b in baldes] == list(range(42))
    assert baldes[0] == {
        "bin_index": 0,
        "lower_bound": None,
        "upper_bound": "-0.2000000000",
        "count": 0,
    }
    assert baldes[41]["upper_bound"] is None


def test_metricas_de_ativo_nunca_calculado_sao_nulas(client: Client) -> None:
    _ativo("ITUB4")

    corpo = _ok(client.get("/api/v1/assets/ITUB4/metrics"))

    assert corpo == {"ticker": "ITUB4", "metric": None}


def test_metricas_do_indice_tem_beta_correlacao_e_observacoes_nulos(
    client: Client,
) -> None:
    ibov = Asset.objects.get(ticker="IBOV")
    _metrica(
        ibov,
        CALCULADO,
        beta_60m=None,
        correlation_60m=None,
        benchmark_observations=None,
    )

    corpo = _ok(client.get("/api/v1/assets/ibov/metrics"))

    metrica = corpo["metric"]
    assert set(metrica) == CABECALHO_METRICA | _colunas_de_metrica() | {"histogram"}
    assert metrica["beta_60m"] is None
    assert metrica["correlation_60m"] is None
    assert metrica["benchmark_observations"] is None
    # o resto vem preenchido: e identidade do indice, nao falta de dado
    assert metrica["volatility_12m"] == "0.1234567890"
