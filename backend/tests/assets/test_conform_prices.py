"""A conformacao de series, provada sobre as fixtures reais do Yahoo (RF-06 e RF-09).

Nenhum teste aqui toca banco, cliente ou rede: `conform_chart` recebe o payload como
dicionario, lido de `tests/fixtures/yahoo/`. Os cenarios de fuso e de desdobramento sao
declarados aqui, porque as respostas reais nao os tem: os timestamps reais caem no mesmo
dia civil em UTC e em Sao Paulo, e a Petrobras nao desdobrou nos ultimos dez anos.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest

from apps.assets.conform_prices import (
    Bar,
    ConformedChart,
    Event,
    conform_chart,
    q6,
    quantize,
)
from tests.assets.conftest import fixture_json


def conform(nome: str) -> ConformedChart:
    return conform_chart(fixture_json(nome, subdir="yahoo"))


def chart_with_one_bar(timezone_name: str, ts: int) -> dict[str, Any]:
    """Uma resposta minima na forma do Yahoo, com um pregao no timestamp dado."""
    return {
        "chart": {
            "result": [
                {
                    "meta": {"exchangeTimezoneName": timezone_name},
                    "timestamp": [ts],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10.0],
                                "high": [11.0],
                                "low": [9.0],
                                "close": [10.5],
                                "volume": [1000],
                            }
                        ],
                        "adjclose": [{"adjclose": [10.5]}],
                    },
                }
            ],
            "error": None,
        }
    }


# --- RF-06: pregoes, data no fuso, descarte do nulo ----------------------------------


def test_rf06_petr4_10y_tem_2490_barras_e_um_descarte() -> None:
    chart = conform("PETR4_10y")
    assert len(chart.bars) == 2490
    assert chart.discarded == 1


def test_rf06_a_barra_nula_de_petr4_e_a_de_2026_09_21() -> None:
    chart = conform("PETR4_10y")
    dates = [bar.date for bar in chart.bars]
    assert date(2026, 9, 21) not in dates
    assert dates[-1] == date(2026, 9, 18)
    assert dates[0] == date(2016, 9, 21)


def test_rf06_bvsp_10y_tem_2483_barras_e_oito_descartes() -> None:
    chart = conform("BVSP_10y")
    assert len(chart.bars) == 2483
    assert chart.discarded == 8


def test_rf06_data_no_fuso_da_bolsa_01z_de_d_mais_1_e_d_em_sao_paulo() -> None:
    # 2026-09-19 01:00Z e 22:00 de 2026-09-18 em America/Sao_Paulo.
    ts = int(datetime(2026, 9, 19, 1, 0, tzinfo=UTC).timestamp())
    chart = conform_chart(chart_with_one_bar("America/Sao_Paulo", ts))
    assert [bar.date for bar in chart.bars] == [date(2026, 9, 18)]


def test_rf06_data_no_fuso_da_bolsa_01z_de_d_mais_1_e_d_mais_1_em_utc() -> None:
    # Mesmo timestamp, meta com UTC: a data muda, logo a regra le o meta.
    ts = int(datetime(2026, 9, 19, 1, 0, tzinfo=UTC).timestamp())
    chart = conform_chart(chart_with_one_bar("UTC", ts))
    assert [bar.date for bar in chart.bars] == [date(2026, 9, 19)]


def test_rf06_precos_quantizados_a_seis_casas() -> None:
    assert q6 == Decimal("0.000001")
    assert quantize(48.400001525878906) == Decimal("48.400002")
    assert quantize(14.0) == Decimal("14.000000")


def test_rf06_barra_da_fixture_chega_quantizada() -> None:
    chart = conform("PETR4_10y")
    # A abertura de 2026-09-18 e 48.400001525878906 na fixture.
    last = chart.bars[-1]
    assert last.date == date(2026, 9, 18)
    assert last.open == Decimal("48.400002")
    # As tres primeiras barras: ajustado e fechamento diferem.
    assert [bar.close for bar in chart.bars[:3]] == [
        Decimal("13.660000"),
        Decimal("14.000000"),
        Decimal("13.690000"),
    ]
    assert [bar.adj_close for bar in chart.bars[:3]] == [
        Decimal("3.421980"),
        Decimal("3.507154"),
        Decimal("3.429496"),
    ]
    assert chart.bars[0] == Bar(
        date=date(2016, 9, 21),
        open=Decimal("13.600000"),
        high=Decimal("13.690000"),
        low=Decimal("13.400000"),
        close=Decimal("13.660000"),
        adj_close=Decimal("3.421980"),
        volume=61094100,
    )
    assert isinstance(chart.bars[0].volume, int)


def test_rf06_sem_result_levanta_value_error() -> None:
    with pytest.raises(ValueError, match=r"chart\.result"):
        conform_chart(fixture_json("not_found", subdir="yahoo"))
    with pytest.raises(ValueError):
        conform_chart({})


# --- RF-09: eventos -----------------------------------------------------------------


def test_rf09_petr4_10y_tem_34_dividendos() -> None:
    chart = conform("PETR4_10y")
    assert len(chart.events) == 34
    assert all(event.kind == "dividend" for event in chart.events)
    first = chart.events[0]
    assert first == Event(
        date=date(2018, 5, 22), kind="dividend", amount=Decimal("0.050000")
    )
    assert first.numerator is None
    assert first.denominator is None


def test_rf09_sem_a_chave_events_e_zero_eventos() -> None:
    payload = fixture_json("BVSP_10y", subdir="yahoo")
    assert "events" not in payload["chart"]["result"][0]
    assert conform_chart(payload).events == []
    assert conform("PETR4_tail").events == []


def test_rf09_events_sem_dividends_ou_splits_e_zero_eventos() -> None:
    payload = chart_with_one_bar("America/Sao_Paulo", 1474462800)
    payload["chart"]["result"][0]["events"] = {}
    assert conform_chart(payload).events == []


def test_rf09_desdobramento_inserido_vira_split_4_por_1() -> None:
    payload = fixture_json("PETR4_10y", subdir="yahoo")
    result = payload["chart"]["result"][0]
    assert "splits" not in result["events"]
    # Inserido na forma exata do Yahoo, no timestamp do primeiro pregao (2016-09-21).
    result["events"]["splits"] = {
        "1474462800": {
            "date": 1474462800,
            "numerator": 4.0,
            "denominator": 1.0,
            "splitRatio": "4:1",
        }
    }
    chart = conform_chart(payload)
    splits = [event for event in chart.events if event.kind == "split"]
    assert splits == [
        Event(
            date=date(2016, 9, 21),
            kind="split",
            numerator=Decimal("4.0000"),
            denominator=Decimal("1.0000"),
        )
    ]
    assert splits[0].amount is None
    assert len(chart.events) == 35
