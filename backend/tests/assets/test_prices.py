"""`run_import_prices` contra a `FakeYahoo`: coleta, transacao por ativo, rebusca e *upsert*
(RF-02 a RF-05, RF-07 a RF-13, RF-16).

Todo teste grava no banco de teste (`@pytest.mark.django_db`), dentro da transacao por
teste do pytest-django — o `transaction.atomic()` por ativo vira *savepoint*, e o `failed`
da `collection_run` fica na transacao do teste, que e o que se inspeciona.

Os cenarios sao compostos das respostas reais (spec, "Fixtures"): `PETR4_10y` para a carga
inicial, `BVSP_10y` para o IBOV, `PETR4_tail` para a incremental e para o terceiro ativo dos
cenarios de tres, `not_found` para o 404. `meta.symbol` nao e validado, entao uma resposta
da Petrobras serve a outro ticker. Toda alteracao sobre uma fixture — recorte de pregoes,
dividendo inserido, `adj_close` multiplicado, `close` alterado — e declarada no teste que a
faz.

Todo teste que espera falha asserta o **comeco** de `error`: `_import_asset` captura
`Exception`, e um cenario mal montado (`AssertionError` da `FakeYahoo`) produziria "segundo
falho, coleta `failed`" exatamente como o teste espera.
"""

from __future__ import annotations

import copy
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

import apps.assets.prices as prices_module
from apps.assets.conform_prices import ConformedChart
from apps.assets.models import Asset, CollectionRun, CorporateEvent, Price, YahooChart
from apps.assets.prices import (
    InvalidTickers,
    PricesFailed,
    PricesReport,
    WriteCounts,
    run_import_prices,
    write_conformed,
)
from apps.assets.yahoo import ChartResponse, YahooClientError
from tests.assets.conftest import FakeYahoo, fixture_json

pytestmark = pytest.mark.django_db

SP = ZoneInfo("America/Sao_Paulo")

# Relogio fixo do RF-10: 2026-09-22 15:00 em Sao Paulo (18:00Z).
FIXED_NOW = datetime(2026, 9, 22, 15, 0, tzinfo=SP)
FIXED_PERIOD2 = 1790100000  # int(FIXED_NOW.timestamp())
MIDNIGHT_2016_09_22 = 1474513200  # inicial: data local do relogio menos 10 anos
MIDNIGHT_2016_09_21 = 1474426800  # completa: primeira `date` de PETR4_10y
MIDNIGHT_2026_09_11 = 1789095600  # incremental: ultima `date` (2026-09-18) menos 7 dias
MIDNIGHT_2018_02_28 = 1519786800  # 29/02/2028 menos 10 anos -> 28/02/2018

# Um timestamp de PETR4_tail (2026-09-15 10:00 SP), usado como data do dividendo inserido.
TAIL_TS_2026_09_15 = 1789477200

PETR4_10Y_BARS = 2491
PETR4_10Y_DISCARDED = 1
PETR4_10Y_DIVIDENDS = 34


def fixed_now() -> datetime:
    return FIXED_NOW


def chart(nome: str, status: int = 200) -> ChartResponse:
    return ChartResponse(status, fixture_json(nome, subdir="yahoo"))


def make_asset(
    ticker: str,
    *,
    provider_symbol: str | None = None,
    status: str = Asset.Status.ACTIVE,
) -> Asset:
    now = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=provider_symbol or f"{ticker}.SA",
        created_at=now,
        updated_at=now,
    )


def sliced(payload: dict[str, Any], start: int, stop: int) -> dict[str, Any]:
    """Modificacao declarada: recorta os pregoes `[start:stop]` de uma resposta real.

    `timestamp`, as cinco series de `quote[0]` e `adjclose` sao recortados juntos; `meta`
    e `events` ficam como vieram.
    """
    payload = copy.deepcopy(payload)
    result = payload["chart"]["result"][0]
    result["timestamp"] = result["timestamp"][start:stop]
    quote = result["indicators"]["quote"][0]
    for key in ("open", "high", "low", "close", "volume"):
        quote[key] = quote[key][start:stop]
    adj = result["indicators"]["adjclose"][0]
    adj["adjclose"] = adj["adjclose"][start:stop]
    return payload


def with_dividend(payload: dict[str, Any], ts: int, amount: float) -> dict[str, Any]:
    """Modificacao declarada: insere um dividendo na forma do Yahoo (`events.dividends`)."""
    payload = copy.deepcopy(payload)
    result = payload["chart"]["result"][0]
    events = result.setdefault("events", {})
    events.setdefault("dividends", {})[str(ts)] = {"amount": amount, "date": ts}
    return payload


def with_adjclose_scaled(payload: dict[str, Any], factor: float) -> dict[str, Any]:
    """Modificacao declarada: multiplica todo `adjclose` nao-nulo por `factor`."""
    payload = copy.deepcopy(payload)
    adj = payload["chart"]["result"][0]["indicators"]["adjclose"][0]
    adj["adjclose"] = [v if v is None else v * factor for v in adj["adjclose"]]
    return payload


def yahoo_runs() -> list[CollectionRun]:
    return list(CollectionRun.objects.filter(source="yahoo-chart").order_by("pk"))


def last_run() -> CollectionRun:
    return yahoo_runs()[-1] if yahoo_runs() else pytest.fail("nenhuma collection_run")


def price_rows(asset: Asset) -> list[dict[str, Any]]:
    return [dict(row) for row in asset.prices.order_by("date").values()]


def event_rows(asset: Asset) -> list[dict[str, Any]]:
    return [
        dict(row) for row in asset.corporate_events.order_by("date", "kind").values()
    ]


def result_for(report: PricesReport, ticker: str) -> Any:
    return next(r for r in report.results if r.ticker == ticker)


def load_petr4() -> Asset:
    """PETR4 com a carga inicial de `PETR4_10y`, o ponto de partida dos cenarios incrementais."""
    petr4 = make_asset("PETR4")
    run_import_prices(FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]}), ["PETR4"])
    assert petr4.prices.count() == PETR4_10Y_BARS - PETR4_10Y_DISCARDED
    return petr4


def three_assets() -> tuple[Asset, Asset, Asset]:
    """Os cenarios de tres ativos, em ordem de ticker: IBOV, PETR4, VALE3 (o segundo e PETR4)."""
    ibov = Asset.objects.get(ticker="IBOV")  # da migration 0002, provider_symbol ^BVSP
    petr4 = make_asset("PETR4")
    vale3 = make_asset("VALE3")
    return ibov, petr4, vale3


# --- RF-02: collection_run `ok` ou `failed`, e a linha existe nos dois casos -------------


def test_rf02_coleta_ok_registra_a_collection_run() -> None:
    make_asset("PETR4")
    before = len(yahoo_runs())
    report = run_import_prices(FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]}), ["PETR4"])
    assert len(yahoo_runs()) == before + 1
    run = last_run()
    assert run.source == "yahoo-chart"
    assert run.status == CollectionRun.Status.OK
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.error == ""
    assert not report.failed


def test_rf02_ativo_que_falha_deixa_a_run_failed_e_levanta_com_o_relatorio() -> None:
    three_assets()
    source = FakeYahoo(
        {
            "^BVSP": [chart("BVSP_10y")],
            "PETR4.SA": [chart("not_found", 404)],
            "VALE3.SA": [chart("PETR4_tail")],
        }
    )
    with pytest.raises(PricesFailed) as info:
        run_import_prices(source, ["IBOV", "PETR4", "VALE3"])
    report = info.value.report
    assert report.failed
    assert [r.ticker for r in report.results] == ["IBOV", "PETR4", "VALE3"]
    error = result_for(report, "PETR4").error
    assert error is not None and error.startswith("InvalidResponse: HTTP 404")
    run = last_run()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "PETR4"
    assert run.finished_at is not None


# --- RF-03: payload cru na bronze, 404 inclusive --------------------------------------


def test_rf03_resposta_vai_para_a_bronze_como_veio() -> None:
    make_asset("PETR4")
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    run_import_prices(source, ["PETR4"], now=fixed_now)
    row = YahooChart.objects.get(run=last_run())
    assert row.payload == fixture_json("PETR4_10y", subdir="yahoo")
    assert row.http_status == 200
    assert row.symbol == "PETR4.SA"
    assert (row.symbol, row.period1, row.period2) == source.calls[0]


def test_rf03_o_404_tambem_e_gravado_na_bronze() -> None:
    petr4 = make_asset("PETR4")
    with pytest.raises(PricesFailed) as info:
        run_import_prices(FakeYahoo({"PETR4.SA": [chart("not_found", 404)]}), ["PETR4"])
    error = result_for(info.value.report, "PETR4").error
    assert error == "InvalidResponse: HTTP 404: No data found, symbol may be delisted"
    row = YahooChart.objects.get(run=last_run())
    assert row.http_status == 404
    assert row.payload == fixture_json("not_found", subdir="yahoo")
    assert petr4.prices.count() == 0


# --- RF-04: ticker desconhecido ou inativo aborta antes de qualquer chamada ------------


def test_rf04_ticker_desconhecido_aborta_antes_de_chamar() -> None:
    make_asset("PETR4")
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    before = len(yahoo_runs())
    with pytest.raises(InvalidTickers) as info:
        run_import_prices(source, ["PETR4", "XXXX9"])
    assert info.value.tickers == ["XXXX9"]
    assert source.calls == []
    assert len(yahoo_runs()) == before


def test_rf04_ticker_inativo_aborta_antes_de_chamar() -> None:
    make_asset("PETR4")
    make_asset("VALE3", status=Asset.Status.INACTIVE)
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    before = len(yahoo_runs())
    with pytest.raises(InvalidTickers) as info:
        run_import_prices(source, ["VALE3", "PETR4"])
    assert info.value.tickers == ["VALE3"]
    assert source.calls == []
    assert len(yahoo_runs()) == before


def test_rf04_tickers_sao_deduplicados_e_ordenados() -> None:
    three_assets()
    source = FakeYahoo(
        {
            "^BVSP": [chart("BVSP_10y")],
            "PETR4.SA": [chart("PETR4_10y")],
            "VALE3.SA": [chart("PETR4_tail")],
        }
    )
    report = run_import_prices(source, ["VALE3", "PETR4", "IBOV", "PETR4"])
    assert [c[0] for c in source.calls] == ["^BVSP", "PETR4.SA", "VALE3.SA"]
    assert [r.ticker for r in report.results] == ["IBOV", "PETR4", "VALE3"]


# --- RF-05: sem argumentos, os ativos `active` com preco ---------------------------------


def test_rf05_sem_argumentos_atua_sobre_os_ativos_ativos_com_preco() -> None:
    _, _, vale3 = three_assets()
    make_asset("ITUB4")  # ativo, sem preco: fica fora
    run_import_prices(
        FakeYahoo(
            {
                "^BVSP": [chart("BVSP_10y")],
                "PETR4.SA": [chart("PETR4_10y")],
                "VALE3.SA": [chart("PETR4_tail")],
            }
        ),
        ["IBOV", "PETR4", "VALE3"],
    )
    vale3.status = Asset.Status.INACTIVE
    vale3.save(update_fields=["status"])

    source = FakeYahoo(
        {"^BVSP": [chart("BVSP_10y")], "PETR4.SA": [chart("PETR4_tail")]}
    )
    report = run_import_prices(source, [])
    assert [c[0] for c in source.calls] == ["^BVSP", "PETR4.SA"]
    assert [(r.ticker, r.skipped) for r in report.results] == [
        ("VALE3", True),
        ("IBOV", False),
        ("PETR4", False),
    ]
    assert result_for(report, "IBOV").mode == "incremental"
    assert "VALE3: pulado, inativo no catalogo" in report.render().splitlines()
    assert (
        report.render().splitlines()[-1]
        == "coleta: 2 ativos, 2 ok, 0 falhos, 1 pulados"
    )


def test_rf05_nenhum_candidato_termina_sem_coleta() -> None:
    vale3 = make_asset("VALE3")
    run_import_prices(FakeYahoo({"VALE3.SA": [chart("PETR4_tail")]}), ["VALE3"])
    vale3.status = Asset.Status.INACTIVE
    vale3.save(update_fields=["status"])
    make_asset("ITUB4")  # ativo, sem preco

    source = FakeYahoo({})
    before = len(yahoo_runs())
    report = run_import_prices(source, [])
    assert source.calls == []
    assert len(yahoo_runs()) == before
    assert not report.failed
    assert report.render().splitlines() == [
        "VALE3: pulado, inativo no catalogo",
        "nenhum ativo ativo com preco; informe tickers",
    ]


# --- RF-07: log_return sobre o adj_close quantizado, antecessor do banco ----------------


def test_rf07_log_return_das_tres_primeiras_barras_conferido_a_mao() -> None:
    """`PETR4_10y`: adj_close 3.421980 / 3.507154 / 3.429496 (close 13.66 / 14.00 / 13.69).

    ln(3.507154 / 3.421980) = 0.0245855515; sobre o `close` daria 0.0245854755 — e a
    diferenca na oitava casa que separa ajustado de fechamento.
    """
    petr4 = load_petr4()
    first, second, third = petr4.prices.order_by("date")[:3]
    assert (first.date, second.date, third.date) == (
        date(2016, 9, 21),
        date(2016, 9, 22),
        date(2016, 9, 23),
    )
    assert (first.adj_close, second.adj_close, third.adj_close) == (
        Decimal("3.421980"),
        Decimal("3.507154"),
        Decimal("3.429496"),
    )
    assert (first.close, second.close, third.close) == (
        Decimal("13.660000"),
        Decimal("14.000000"),
        Decimal("13.690000"),
    )
    assert first.log_return is None
    assert second.log_return == Decimal("0.0245855515")
    assert third.log_return == Decimal("-0.0223915708")
    assert petr4.prices.filter(log_return__isnull=True).count() == 1


def test_rf07_primeiro_pregao_da_janela_incremental_recebe_retorno_contra_o_banco() -> (
    None
):
    petr4 = make_asset("PETR4")
    ten_years = fixture_json("PETR4_10y", subdir="yahoo")
    # coleta 1: os dois primeiros pregoes (2016-09-21 e 22); coleta 2: so o terceiro (23)
    run_import_prices(
        FakeYahoo({"PETR4.SA": [ChartResponse(200, sliced(ten_years, 0, 2))]}),
        ["PETR4"],
    )
    assert petr4.prices.count() == 2
    report = run_import_prices(
        FakeYahoo({"PETR4.SA": [ChartResponse(200, sliced(ten_years, 2, 3))]}),
        ["PETR4"],
    )
    assert result_for(report, "PETR4").mode == "incremental"
    third = petr4.prices.get(date=date(2016, 9, 23))
    assert third.log_return == Decimal("-0.0223915708")  # ln(3.429496 / 3.507154)


# --- RF-08: unico em (asset, date); so o que mudou conta e avanca run/updated_at --------


def test_rf08_duas_coletas_iguais_nao_atualizam_nada() -> None:
    petr4 = load_petr4()
    before = price_rows(petr4)
    report = run_import_prices(FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]}), ["PETR4"])
    result = result_for(report, "PETR4")
    assert (result.created, result.updated) == (0, 0)
    assert "0 atualizados" in result.render()
    assert price_rows(petr4) == before  # count, updated_at e run intactos
    assert len(yahoo_runs()) == 2


def test_rf08_close_alterado_atualiza_so_aquela_linha() -> None:
    petr4 = load_petr4()
    before = {row["date"]: row for row in price_rows(petr4)}
    # modificacao declarada: o `close` de 2026-09-18 (penultimo pregao) vai de 48.5 a 49.0
    payload = fixture_json("PETR4_10y", subdir="yahoo")
    quote = payload["chart"]["result"][0]["indicators"]["quote"][0]
    assert quote["close"][-2] == 48.5
    quote["close"][-2] = 49.0
    report = run_import_prices(
        FakeYahoo({"PETR4.SA": [ChartResponse(200, payload)]}), ["PETR4"]
    )
    result = result_for(report, "PETR4")
    assert (result.created, result.updated) == (0, 1)
    assert "1 atualizados" in result.render()
    after = {row["date"]: row for row in price_rows(petr4)}
    assert after.keys() == before.keys()
    changed = after[date(2026, 9, 18)]
    assert changed["close"] == Decimal("49.000000")
    assert changed["run_id"] == last_run().pk
    assert changed["updated_at"] > before[date(2026, 9, 18)]["updated_at"]
    for d, row in before.items():
        if d != date(2026, 9, 18):
            assert after[d] == row


# --- RF-09: eventos, unicos em (asset, date, kind) ---------------------------------------


def test_rf09_dividendos_criados_uma_vez() -> None:
    petr4 = make_asset("PETR4")
    report = run_import_prices(FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]}), ["PETR4"])
    assert result_for(report, "PETR4").events == PETR4_10Y_DIVIDENDS
    events = petr4.corporate_events.all()
    assert events.count() == PETR4_10Y_DIVIDENDS
    assert all(e.kind == CorporateEvent.Kind.DIVIDEND for e in events)
    assert events.get(date=date(2018, 5, 22)).amount == Decimal("0.050000")

    report = run_import_prices(FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]}), ["PETR4"])
    assert result_for(report, "PETR4").events == 0
    assert petr4.corporate_events.count() == PETR4_10Y_DIVIDENDS


def test_rf09_desdobramento_inserido_vira_evento_split() -> None:
    petr4 = make_asset("PETR4")
    # modificacao declarada: um desdobramento 4:1 em 2026-09-15, na forma do Yahoo
    payload = fixture_json("PETR4_tail", subdir="yahoo")
    payload["chart"]["result"][0]["events"] = {
        "splits": {
            str(TAIL_TS_2026_09_15): {
                "date": TAIL_TS_2026_09_15,
                "numerator": 4.0,
                "denominator": 1.0,
                "splitRatio": "4:1",
            }
        }
    }
    report = run_import_prices(
        FakeYahoo({"PETR4.SA": [ChartResponse(200, payload)]}), ["PETR4"]
    )
    assert result_for(report, "PETR4").events == 1
    split = petr4.corporate_events.get()
    assert split.kind == CorporateEvent.Kind.SPLIT
    assert split.date == date(2026, 9, 15)
    assert (split.numerator, split.denominator, split.amount) == (
        Decimal("4.0000"),
        Decimal("1.0000"),
        None,
    )
    assert split.run_id == last_run().pk


# --- RF-10: period1/period2, relogio injetavel --------------------------------------


def test_rf10_carga_inicial_pede_dez_anos_ate_agora() -> None:
    make_asset("PETR4")
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    report = run_import_prices(source, ["PETR4"], now=fixed_now)
    assert result_for(report, "PETR4").mode == "inicial"
    assert source.calls == [("PETR4.SA", MIDNIGHT_2016_09_22, FIXED_PERIOD2)]


def test_rf10_incremental_pede_da_ultima_data_menos_sete_dias() -> None:
    petr4 = load_petr4()
    last = petr4.prices.order_by("-date").first()
    assert last is not None and last.date == date(2026, 9, 18)
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_tail")]})
    report = run_import_prices(source, ["PETR4"], now=fixed_now)
    assert result_for(report, "PETR4").mode == "incremental"
    assert source.calls == [("PETR4.SA", MIDNIGHT_2026_09_11, FIXED_PERIOD2)]


def test_rf10_completa_pede_da_primeira_data_conhecida() -> None:
    load_petr4()
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    report = run_import_prices(source, ["PETR4"], full=True, now=fixed_now)
    assert result_for(report, "PETR4").mode == "completa"
    assert source.calls == [("PETR4.SA", MIDNIGHT_2016_09_21, FIXED_PERIOD2)]


def test_rf10_vinte_e_nove_de_fevereiro_vira_vinte_e_oito() -> None:
    make_asset("PETR4")
    leap_now = datetime(2028, 2, 29, 15, 0, tzinfo=SP)
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    run_import_prices(source, ["PETR4"], now=lambda: leap_now)
    assert source.calls == [
        ("PETR4.SA", MIDNIGHT_2018_02_28, int(leap_now.timestamp()))
    ]


# --- RF-11: evento novo rebusca a serie; --full -----------------------------------------


def test_rf11_dividendo_novo_na_incremental_rebusca_a_serie_inteira() -> None:
    petr4 = load_petr4()
    before = {row["date"]: row for row in price_rows(petr4)}
    assert not petr4.corporate_events.filter(date=date(2026, 9, 15)).exists()

    # modificacoes declaradas: o mesmo dividendo (0.15 em 2026-09-15) inserido na cauda e
    # na serie de dez anos; nesta, todo `adj_close` multiplicado por 0.98
    tail = with_dividend(
        fixture_json("PETR4_tail", subdir="yahoo"), TAIL_TS_2026_09_15, 0.15
    )
    rebuilt = with_dividend(
        with_adjclose_scaled(fixture_json("PETR4_10y", subdir="yahoo"), 0.98),
        TAIL_TS_2026_09_15,
        0.15,
    )
    source = FakeYahoo(
        {"PETR4.SA": [ChartResponse(200, tail), ChartResponse(200, rebuilt)]}
    )
    report = run_import_prices(source, ["PETR4"], now=fixed_now)

    assert source.calls == [
        ("PETR4.SA", MIDNIGHT_2026_09_11, FIXED_PERIOD2),
        ("PETR4.SA", MIDNIGHT_2016_09_21, FIXED_PERIOD2),
    ]
    result = result_for(report, "PETR4")
    assert result.mode == "completa"
    assert result.events == 1
    assert result.received == PETR4_10Y_BARS  # e a segunda resposta que foi conformada
    assert result.updated == PETR4_10Y_BARS - PETR4_10Y_DISCARDED
    assert petr4.corporate_events.count() == PETR4_10Y_DIVIDENDS + 1
    assert petr4.corporate_events.get(date=date(2026, 9, 15)).amount == Decimal(
        "0.150000"
    )
    after = {row["date"]: row for row in price_rows(petr4)}
    old = before[date(2016, 9, 21)]
    new = after[date(2016, 9, 21)]
    assert old["adj_close"] == Decimal("3.421980")
    assert new["adj_close"] == Decimal(
        "3.353541"
    )  # 3.421980381011963 * 0.98, a 6 casas
    assert new["updated_at"] > old["updated_at"]
    assert new["run_id"] == last_run().pk
    # as duas respostas estao na bronze, na mesma coleta
    assert list(
        YahooChart.objects.filter(run=last_run())
        .order_by("pk")
        .values_list("period1", flat=True)
    ) == [MIDNIGHT_2026_09_11, MIDNIGHT_2016_09_21]


def test_rf11_full_em_ticker_com_preco_e_uma_chamada_completa() -> None:
    load_petr4()
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    report = run_import_prices(source, ["PETR4"], full=True, now=fixed_now)
    assert len(source.calls) == 1
    assert source.calls[0][1] == MIDNIGHT_2016_09_21
    assert result_for(report, "PETR4").mode == "completa"


def test_rf11_full_em_ticker_sem_preco_e_inicial() -> None:
    make_asset("PETR4")
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_10y")]})
    report = run_import_prices(source, ["PETR4"], full=True, now=fixed_now)
    assert source.calls == [("PETR4.SA", MIDNIGHT_2016_09_22, FIXED_PERIOD2)]
    assert result_for(report, "PETR4").mode == "inicial"


# --- RF-12: transacao por ativo, formas (a), (c) e (d) -------------------------------------


def assert_first_and_third_conformed(
    ibov: Asset, petr4: Asset, vale3: Asset, report: PricesReport
) -> None:
    assert ibov.prices.count() == 2483  # BVSP_10y: 2491 pregoes, 8 nulos
    assert vale3.prices.count() == 13  # PETR4_tail: 14 pregoes, 1 nulo
    assert price_rows(petr4) == []
    assert event_rows(petr4) == []
    assert result_for(report, "IBOV").error is None
    assert result_for(report, "VALE3").error is None
    run = last_run()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "PETR4"


def test_rf12_a_404_no_segundo_de_tres_nao_impede_os_demais() -> None:
    ibov, petr4, vale3 = three_assets()
    source = FakeYahoo(
        {
            "^BVSP": [chart("BVSP_10y")],
            "PETR4.SA": [chart("not_found", 404)],
            "VALE3.SA": [chart("PETR4_tail")],
        }
    )
    with pytest.raises(PricesFailed) as info:
        run_import_prices(source, ["IBOV", "PETR4", "VALE3"])
    report = info.value.report
    assert_first_and_third_conformed(ibov, petr4, vale3, report)
    error = result_for(report, "PETR4").error
    assert error is not None and error.startswith("InvalidResponse: HTTP 404")
    assert YahooChart.objects.filter(run=last_run()).count() == 3
    assert YahooChart.objects.get(run=last_run(), asset=petr4).http_status == 404


def test_rf12_c_yahoo_client_error_no_segundo_nao_grava_bronze() -> None:
    ibov, petr4, vale3 = three_assets()
    source = FakeYahoo(
        {
            "^BVSP": [chart("BVSP_10y")],
            "PETR4.SA": [YahooClientError("fonte falsa: tentativas esgotadas")],
            "VALE3.SA": [chart("PETR4_tail")],
        }
    )
    with pytest.raises(PricesFailed) as info:
        run_import_prices(source, ["IBOV", "PETR4", "VALE3"])
    report = info.value.report
    assert_first_and_third_conformed(ibov, petr4, vale3, report)
    assert result_for(report, "PETR4").error == (
        "YahooClientError: fonte falsa: tentativas esgotadas"
    )
    assert YahooChart.objects.filter(run=last_run()).count() == 2
    assert not YahooChart.objects.filter(run=last_run(), asset=petr4).exists()


def test_rf12_d_gravacao_que_levanta_no_segundo_reverte_so_ele(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ibov, petr4, vale3 = three_assets()
    seen: list[str] = []

    def fake_write(
        asset: Asset, run: CollectionRun, conformed: ConformedChart
    ) -> WriteCounts:
        seen.append(asset.ticker)
        if asset.ticker != "PETR4":
            return write_conformed(asset, run, conformed)
        bar = conformed.bars[0]
        Price.objects.create(
            asset=asset,
            date=bar.date,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            adj_close=bar.adj_close,
            volume=bar.volume,
            run=run,
            updated_at=timezone.now(),
        )
        raise RuntimeError("gravacao quebrou depois de um pregao")

    monkeypatch.setattr("apps.assets.prices.write_conformed", fake_write)
    assert prices_module.write_conformed is fake_write

    source = FakeYahoo(
        {
            "^BVSP": [chart("BVSP_10y")],
            "PETR4.SA": [chart("PETR4_10y")],
            "VALE3.SA": [chart("PETR4_tail")],
        }
    )
    with pytest.raises(PricesFailed) as info:
        run_import_prices(source, ["IBOV", "PETR4", "VALE3"])
    report = info.value.report
    assert seen == ["IBOV", "PETR4", "VALE3"]
    assert_first_and_third_conformed(ibov, petr4, vale3, report)
    assert result_for(report, "PETR4").error == (
        "RuntimeError: gravacao quebrou depois de um pregao"
    )
    # a bronze do PETR4 fica; a silver dele e igual a antes
    assert YahooChart.objects.filter(run=last_run(), asset=petr4).count() == 1


# --- RF-13: o relatorio ------------------------------------------------------------------


def test_rf13_render_com_os_numeros_do_cenario_e_a_linha_final() -> None:
    three_assets()
    report = run_import_prices(
        FakeYahoo(
            {
                "^BVSP": [chart("BVSP_10y")],
                "PETR4.SA": [chart("PETR4_10y")],
                "VALE3.SA": [chart("PETR4_tail")],
            }
        ),
        ["IBOV", "PETR4", "VALE3"],
    )
    assert report.render().splitlines() == [
        "IBOV inicial: 2491 pregoes, 8 descartados, 2483 criados, 0 atualizados, 0 eventos",
        "PETR4 inicial: 2491 pregoes, 1 descartados, 2490 criados, 0 atualizados, 34 eventos",
        "VALE3 inicial: 14 pregoes, 1 descartados, 13 criados, 0 atualizados, 0 eventos",
        "coleta: 3 ativos, 3 ok, 0 falhos, 0 pulados",
    ]


def test_rf13_render_com_ativo_falho_e_pulado() -> None:
    petr4 = make_asset("PETR4")
    vale3 = make_asset("VALE3")
    run_import_prices(
        FakeYahoo(
            {"PETR4.SA": [chart("PETR4_10y")], "VALE3.SA": [chart("PETR4_tail")]}
        ),
        ["PETR4", "VALE3"],
    )
    vale3.status = Asset.Status.INACTIVE
    vale3.save(update_fields=["status"])

    with pytest.raises(PricesFailed) as info:
        run_import_prices(FakeYahoo({"PETR4.SA": [chart("not_found", 404)]}), [])
    assert info.value.report.render().splitlines() == [
        "VALE3: pulado, inativo no catalogo",
        "PETR4 incremental: FALHOU (InvalidResponse: HTTP 404: No data found, symbol may be delisted)",
        "coleta: 1 ativos, 0 ok, 1 falhos, 1 pulados",
    ]
    assert petr4.prices.count() == PETR4_10Y_BARS - PETR4_10Y_DISCARDED  # intacto


# --- RF-16: o simbolo sai so do provider_symbol -----------------------------------------


def test_rf16_o_simbolo_pedido_e_o_provider_symbol_do_catalogo() -> None:
    make_asset("PETR4", provider_symbol="PETR4.XX")
    source = FakeYahoo({"PETR4.XX": [chart("PETR4_10y")]})
    run_import_prices(source, ["PETR4"])
    assert source.calls[0][0] == "PETR4.XX"
    assert YahooChart.objects.get(run=last_run()).symbol == "PETR4.XX"
