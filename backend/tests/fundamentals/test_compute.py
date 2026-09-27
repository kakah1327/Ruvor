"""`run_compute_fundamentals` e a casca `compute_fundamentals` sobre a `silver` montada das
fixtures (RF-20, RF-23, RF-24, RF-24b, RF-25, RF-27).

A `silver` vem de `run_import_fundamentals` com a `FakeCvm` servindo as seis fixtures, com o
catalogo do teste: PETR4 (Petrobras), VALE3 (Vale), ITUB4 (Itau) e SAPR3, SAPR4 e SAPR11
(Sanepar). O `Price` e inserido no teste, **so** para PETR4, VALE3, ITUB4 e SAPR11: SAPR3 e
SAPR4 ficam sem preco, e a Sanepar sai `no_price` na capitalizacao (nenhum ticker de classe
com preco; a unit nao conta). PETR3 e ITUB3 nao estao no catalogo.

**`now` injetado em 2025-06-30**, horario de Brasilia: o ultimo balanco de Itau e Vale nas
fixtures e 2024-12-31, e com o relogio real a regra 0 (`stale_statement`) encobriria as
outras. O ultimo balanco da Petrobras nas fixtures e 2025-09-30 -- posterior a esse `now`,
porque as fixtures foram baixadas em 2026; o calculo usa o mais recente que existe.

Os numeros dos indicadores se conferem em `test_indicators.py`; aqui se confere a ligacao:
qual balanco, qual preco, quais tickers de classe, qual transacao, que linhas no relatorio.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Callable
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from apps.assets.models import Asset, CollectionRun, Price
from apps.fundamentals import compute
from apps.fundamentals.compute import (
    ComputeReport,
    FundamentalsFailed,
    run_compute_fundamentals,
)
from apps.fundamentals.importer import run_import_fundamentals
from apps.fundamentals.indicators import IndicatorValues
from apps.fundamentals.models import FinancialStatement, FundamentalIndicator
from tests.fundamentals.conftest import FakeCvm, fixture_zip, serve_range

pytestmark = pytest.mark.django_db

SP = ZoneInfo("America/Sao_Paulo")
NOW = datetime(2025, 6, 30, 12, 0, tzinfo=SP)
TODAY = date(2025, 6, 30)
PRICE_DAY = date(2025, 6, 27)  # sexta-feira, 3 dias antes
Q6 = Decimal("0.000001")

PETROBRAS, VALE, ITAU, SANEPAR = "9512", "4170", "19348", "18627"
CATALOG = (
    ("PETR4", PETROBRAS),
    ("VALE3", VALE),
    ("ITUB4", ITAU),
    ("SAPR3", SANEPAR),
    ("SAPR4", SANEPAR),
    ("SAPR11", SANEPAR),
)
TICKERS = sorted(ticker for ticker, _ in CATALOG)
CLOSES = {
    "PETR4": Decimal("30.50"),
    "VALE3": Decimal("55.00"),
    "ITUB4": Decimal("35.20"),
    "SAPR11": Decimal("28.00"),
}

ALL_FIXTURES = {
    ("itr", 2016): "itr_2016",
    ("itr", 2019): "itr_2019",
    ("itr", 2024): "itr_2024",
    ("dfp", 2024): "dfp_2024",
    ("itr", 2025): "itr_2025",
    ("dfp", 2025): "dfp_2025",
}

COMMAND_POINT = (
    "apps.fundamentals.management.commands.compute_fundamentals"
    ".run_compute_fundamentals"
)


def clock(moment: datetime) -> Callable[[], datetime]:
    return lambda: moment


def add_stock(
    ticker: str, code_cvm: str | None, *, status: str = Asset.Status.ACTIVE
) -> Asset:
    moment = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        code_cvm=code_cvm,
        created_at=moment,
        updated_at=moment,
    )


def add_price(
    ticker: str, day: date, close: Decimal, adj_close: Decimal | None = None
) -> None:
    run = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    Price.objects.create(
        asset=Asset.objects.get(ticker=ticker),
        date=day,
        open=close,
        high=close,
        low=close,
        close=close,
        adj_close=close if adj_close is None else adj_close,
        volume=1000,
        log_return=None,
        run=run,
        updated_at=timezone.now(),
    )


def add_base_prices() -> None:
    """Os precos de todos os testes: PETR4, VALE3, ITUB4 e SAPR11, em `PRICE_DAY`."""
    for ticker, close in CLOSES.items():
        add_price(ticker, PRICE_DAY, close)


@pytest.fixture
def silver() -> None:
    """O catalogo do teste e a `silver` conformada das seis fixtures, sem preco."""
    for ticker, code in CATALOG:
        add_stock(ticker, code)
    fake = FakeCvm({}, {})
    served = {key: fixture_zip(name) for key, name in ALL_FIXTURES.items()}
    serve_range(fake, NOW, served)
    run_import_fundamentals(fake, now=clock(NOW))


def computing(now: datetime = NOW) -> ComputeReport:
    """A execucao, devolvendo o relatorio tambem quando ela termina com falha."""
    try:
        return run_compute_fundamentals(now=clock(now))
    except FundamentalsFailed as exc:
        return exc.report


def row(ticker: str) -> FundamentalIndicator:
    return FundamentalIndicator.objects.get(asset__ticker=ticker)


def latest_statement(code_cvm: str) -> FinancialStatement:
    return FinancialStatement.objects.filter(company__code_cvm=code_cvm).latest(
        "reference_date"
    )


def eps_of(code_cvm: str) -> Decimal:
    """O LPA sem quantizar, dos quatro ultimos trimestres da companhia."""
    four = list(
        FinancialStatement.objects.filter(company__code_cvm=code_cvm).order_by(
            "-reference_date"
        )[:4]
    )
    incomes = [s.net_income_parent for s in four]
    head = four[0]
    assert None not in incomes
    assert head.shares_on is not None
    assert head.shares_pn is not None
    net_income = sum((v for v in incomes if v is not None), Decimal(0))
    return net_income / (head.shares_on + head.shares_pn)


# RF-20


@pytest.mark.usefixtures("silver")
def test_rf20_uma_linha_por_acao_com_balanco_e_um_now_por_execucao() -> None:
    add_base_prices()
    add_stock("XPTO3", "999999")  # companhia fora da CVM: sem balanco
    add_stock("NULO3", None)  # sem code_cvm: sem balanco
    add_stock("VALE5", VALE, status=Asset.Status.INACTIVE)  # inativa: fora
    ticks = iter(NOW + timedelta(seconds=s) for s in range(100))
    calls: list[datetime] = []

    def moving() -> datetime:
        calls.append(next(ticks))
        return calls[-1]

    report = run_compute_fundamentals(now=moving)

    assert len(calls) == 1  # calculated_at = now() uma vez
    rows = FundamentalIndicator.objects.all()
    assert sorted(r.asset.ticker for r in rows) == TICKERS  # o IBOV (index) fica fora
    assert {r.calculated_at for r in rows} == {NOW}
    assert [r.ticker for r in report.results] == TICKERS
    assert report.without_statements == 2
    for ticker, code in CATALOG:
        assert row(ticker).statement == latest_statement(code)


@pytest.mark.usefixtures("silver")
def test_rf20_duas_execucoes_duas_linhas_por_acao_a_primeira_intacta() -> None:
    add_base_prices()
    run_compute_fundamentals(now=clock(NOW))
    first = list(FundamentalIndicator.objects.order_by("pk").values())
    add_price("PETR4", date(2025, 6, 30), Decimal("40.00"))  # muda a segunda execucao
    later = NOW + timedelta(hours=1)

    run_compute_fundamentals(now=clock(later))

    for ticker in TICKERS:
        assert FundamentalIndicator.objects.filter(asset__ticker=ticker).count() == 2
    assert len(first) == len(TICKERS)
    after = list(FundamentalIndicator.objects.order_by("pk").values())
    assert after[: len(first)] == first  # a primeira execucao, campo a campo
    second_petr = FundamentalIndicator.objects.get(
        asset__ticker="PETR4", calculated_at=later
    )
    assert second_petr.close == Decimal("40.000000")
    assert FundamentalIndicator.objects.get(
        asset__ticker="PETR4", calculated_at=NOW
    ).close == Decimal("30.500000")


# RF-23


@pytest.mark.usefixtures("silver")
def test_rf23_sem_preco_e_preco_de_11_dias_sao_sem_preco() -> None:
    add_price("PETR4", TODAY - timedelta(days=10), Decimal("30.50"))  # no limite: vale
    add_price("PETR4", TODAY + timedelta(days=1), Decimal("99.00"))  # depois de hoje
    add_price("VALE3", TODAY - timedelta(days=11), Decimal("55.00"))  # 11 dias: nao
    # ITUB4: nenhum preco

    computing()

    petr = row("PETR4")
    assert petr.price_date == TODAY - timedelta(days=10)
    assert petr.close == Decimal("30.500000")
    assert petr.per_share_missing is None
    for ticker in ("VALE3", "ITUB4"):
        sem = row(ticker)
        assert sem.price_date is None
        assert sem.close is None
        assert sem.pe is None
        assert sem.pb is None
        assert sem.per_share_missing == "no_price"
    vale = row("VALE3")
    assert vale.eps is not None  # no_price nao anula eps nem bvps
    assert vale.bvps is not None
    assert vale.market_cap is None
    assert vale.market_cap_missing == "no_price"


@pytest.mark.usefixtures("silver")
def test_rf23_usa_close_e_nao_adj_close() -> None:
    add_price("PETR4", PRICE_DAY, Decimal("30.50"), adj_close=Decimal("20.00"))

    computing()

    petr = row("PETR4")
    eps = eps_of(PETROBRAS)
    assert petr.close == Decimal("30.500000")
    assert petr.price_date == PRICE_DAY
    assert petr.pe == (Decimal("30.50") / eps).quantize(Q6)
    assert petr.pe != (Decimal("20.00") / eps).quantize(Q6)


# RF-24


@pytest.mark.usefixtures("silver")
def test_rf24_de_ponta_a_ponta_unit_sem_preco_e_banco() -> None:
    add_base_prices()

    computing()

    sapr11 = row("SAPR11")
    assert sapr11.per_share_missing == "unit"
    for column in ("price_date", "close", "eps", "bvps", "pe", "pb"):
        assert getattr(sapr11, column) is None, column
    for ticker in ("SAPR3", "SAPR4"):
        sem = row(ticker)
        assert sem.per_share_missing == "no_price"
        assert sem.eps is not None
        assert sem.bvps is not None
    itub = row("ITUB4")
    assert itub.account_plan == "bank"
    assert itub.net_margin is None
    assert itub.roe is not None
    assert itub.pe is not None
    assert itub.pb is not None
    for ticker in ("PETR4", "VALE3", "ITUB4"):
        assert row(ticker).per_share_missing is None, ticker


# RF-24b


@pytest.mark.usefixtures("silver")
def test_rf24b_de_ponta_a_ponta_capitalizacao() -> None:
    add_base_prices()

    computing()

    petr = row("PETR4")  # sem PETR3 no catalogo
    assert petr.market_cap is None
    assert petr.market_cap_missing == "missing_class_price"
    assert petr.pe is not None
    vale = row("VALE3")  # so ON, com preco
    shares_on = latest_statement(VALE).shares_on
    assert shares_on is not None
    assert vale.market_cap == (Decimal("55.00") * shares_on).quantize(Decimal("0.01"))
    assert vale.market_cap_missing is None
    for ticker in ("SAPR3", "SAPR4", "SAPR11"):  # a unit tem preco, mas nao conta
        sanepar = row(ticker)
        assert sanepar.market_cap is None
        assert sanepar.market_cap_missing == "no_price"


@pytest.mark.usefixtures("silver")
def test_rf24b_ticker_inativo_nao_e_da_classe() -> None:
    # Insercoes declaradas: PN > 0 no balanco mais recente da Vale, e VALE5 no catalogo
    # com o code_cvm da Vale, inativa e com preco valido.
    statement = latest_statement(VALE)
    statement.shares_pn = 1_000_000
    statement.save(update_fields=["shares_pn"])
    add_stock("VALE5", VALE, status=Asset.Status.INACTIVE)
    add_base_prices()
    add_price("VALE5", PRICE_DAY, Decimal("50.00"))

    computing()

    vale = row("VALE3")
    assert vale.market_cap is None
    assert vale.market_cap_missing == "missing_class_price"
    assert not FundamentalIndicator.objects.filter(asset__ticker="VALE5").exists()


# RF-25


@pytest.mark.usefixtures("silver")
def test_rf25_falha_na_escrita_de_uma_acao_reverte_so_ela(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_base_prices()
    real = compute.write_indicator
    written: list[str] = []

    def second_breaks(
        asset: Asset, calculated_at: datetime, values: IndicatorValues
    ) -> None:
        real(asset, calculated_at, values)
        written.append(asset.ticker)
        if len(written) == 2:  # grava e so entao levanta
            assert FundamentalIndicator.objects.filter(asset=asset).exists()
            raise RuntimeError("falha depois de gravar")

    monkeypatch.setattr("apps.fundamentals.compute.write_indicator", second_breaks)

    with pytest.raises(FundamentalsFailed) as info:
        run_compute_fundamentals(now=clock(NOW))

    broken = written[1]
    assert broken == TICKERS[1]
    assert not FundamentalIndicator.objects.filter(asset__ticker=broken).exists()
    others = [t for t in TICKERS if t != broken]
    assert sorted(
        FundamentalIndicator.objects.values_list("asset__ticker", flat=True)
    ) == sorted(others)
    text = info.value.report.render()
    assert re.search(
        rf"^{broken}: FALHOU \(RuntimeError: falha depois de gravar\)$",
        text,
        re.MULTILINE,
    )
    assert re.search(
        r"^calculo: 6 acoes, 0 sem balanco, 0 fora de escala, 1 falhas$",
        text,
        re.MULTILINE,
    )


# RF-27


@pytest.mark.usefixtures("silver")
def test_rf27_relatorio_ancorado_nos_rotulos() -> None:
    add_base_prices()
    add_stock("XPTO3", "999999")

    text = computing().render()

    lines = text.splitlines()
    assert [line for line in lines if re.match(r"^calculo: ", line)] == [
        "calculo: 6 acoes, 1 sem balanco, 0 fora de escala, 0 falhas"
    ]
    assert lines[-1].startswith("calculo: ")
    per_asset = [line for line in lines if re.match(r"^[A-Z0-9]+: ", line)]
    assert [line.split(":")[0] for line in per_asset] == TICKERS
    assert re.search(
        r"^PETR4: 2025-09-30, pe -?\d+\.\d{6}, market_cap missing_class_price$",
        text,
        re.MULTILINE,
    )
    assert re.search(
        r"^VALE3: 2024-12-31, pe -?\d+\.\d{6}, market_cap \d+\.\d{2}$",
        text,
        re.MULTILINE,
    )
    assert re.search(
        r"^SAPR11: 2024-12-31, pe -, market_cap no_price$", text, re.MULTILINE
    )


@pytest.mark.usefixtures("silver")
def test_rf27_fora_de_escala_e_contado() -> None:
    # Insercao declarada: PL de R$ 1 no balanco mais recente da Vale -> `roe` nao cabe.
    statement = latest_statement(VALE)
    statement.equity_parent = Decimal("1.00")
    statement.save(update_fields=["equity_parent"])
    add_base_prices()

    text = computing().render()

    assert row("VALE3").roe is None
    assert re.search(
        r"^calculo: 6 acoes, 0 sem balanco, 1 fora de escala, 0 falhas$",
        text,
        re.MULTILINE,
    )


# A casca


def with_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """O comando chama o calculo verdadeiro, so com o relogio de `NOW`."""
    monkeypatch.setattr(
        COMMAND_POINT, functools.partial(run_compute_fundamentals, now=clock(NOW))
    )


@pytest.mark.usefixtures("silver")
def test_rf27_comando_grava_e_escreve_o_relatorio_em_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_base_prices()
    with_clock(monkeypatch)
    stdout = StringIO()

    call_command("compute_fundamentals", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(
        r"^calculo: 6 acoes, 0 sem balanco, 0 fora de escala, 0 falhas$",
        saida,
        re.MULTILINE,
    )
    assert re.search(r"^VALE3: 2024-12-31, ", saida, re.MULTILINE)
    assert FundamentalIndicator.objects.count() == len(TICKERS)


@pytest.mark.usefixtures("silver")
def test_rf25_comando_com_falha_escreve_o_relatorio_e_sai_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_base_prices()
    with_clock(monkeypatch)
    real = compute.write_indicator

    def vale_breaks(asset: Asset, calculated_at: datetime, values: Any) -> None:
        if asset.ticker == "VALE3":
            raise RuntimeError("gravacao quebrou")
        real(asset, calculated_at, values)

    monkeypatch.setattr("apps.fundamentals.compute.write_indicator", vale_breaks)
    stdout = StringIO()

    with pytest.raises(CommandError) as info:
        call_command("compute_fundamentals", stdout=stdout)

    assert str(info.value) == "calculo com falhas: VALE3"
    assert info.value.returncode == 1
    saida = stdout.getvalue()  # o relatorio inteiro saiu antes do erro
    assert re.search(
        r"^VALE3: FALHOU \(RuntimeError: gravacao quebrou\)$", saida, re.MULTILINE
    )
    assert re.search(r"^calculo: 6 acoes, .*, 1 falhas$", saida, re.MULTILINE)
    assert FundamentalIndicator.objects.count() == len(TICKERS) - 1
