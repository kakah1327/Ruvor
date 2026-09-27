"""A segunda fase de `run_compute_fundamentals`: a comparacao com os pares, gravada em
`gold.peer_comparison` (RF-10, RF-11 de ponta a ponta, RF-15).

A `silver` e o catalogo sao os de `test_compute.py` (a fixture `silver`, as seis fixtures da
CVM, `now` em 2025-06-30): PETR4 (Petrobras), VALE3 (Vale), ITUB4 (Itau) e SAPR3, SAPR4 e
SAPR11 (Sanepar). O catalogo do teste nao traz classificacao; cada teste a poe, declarada, em
`silver.asset`. Os numeros da mediana e do percentil se conferem em `test_peers.py`; aqui se
confere a ligacao: quais linhas entram, qual transacao, que linhas no relatorio.
"""

from __future__ import annotations

import functools
import re
from datetime import datetime, timedelta
from io import StringIO
from typing import Any

import pytest
from django.core.management import CommandError, call_command
from django.forms.models import model_to_dict

from apps.assets.models import Asset
from apps.fundamentals import compute
from apps.fundamentals.compute import FundamentalsFailed, run_compute_fundamentals
from apps.fundamentals.models import FundamentalIndicator, PeerComparison
from apps.fundamentals.peers import Comparison
from tests.fundamentals.test_compute import (
    COMMAND_POINT,
    NOW,
    TICKERS,
    add_base_prices,
    clock,
    silver,  # noqa: F401 -- a fixture, usada por `usefixtures`
)

pytestmark = pytest.mark.django_db

ENERGY = (
    "Petróleo, Gás e Biocombustíveis",
    "Petróleo, Gás e Biocombustíveis",
    "Exploração",
)
SANITATION = ("Utilidade Pública", "Água e Saneamento", "Água e Saneamento")


def classify(tickers: list[str], group: tuple[str, str, str]) -> None:
    """Declarado: a classificacao da B3 de `tickers`, posta no catalogo do teste."""
    sector, subsector, segment = group
    Asset.objects.filter(ticker__in=tickers).update(
        sector=sector, subsector=subsector, segment=segment
    )


def comparison(ticker: str) -> PeerComparison:
    return PeerComparison.objects.get(asset__ticker=ticker)


# RF-10


@pytest.mark.usefixtures("silver")
def test_rf10_duas_execucoes_duas_linhas_por_acao_a_primeira_intacta() -> None:
    add_base_prices()
    classify(TICKERS, ENERGY)

    run_compute_fundamentals(now=clock(NOW))
    first = {c.pk: model_to_dict(c) for c in PeerComparison.objects.all()}
    run_compute_fundamentals(now=clock(NOW + timedelta(hours=1)))

    assert len(first) == len(TICKERS)
    for ticker in TICKERS:
        rows = PeerComparison.objects.filter(asset__ticker=ticker)
        assert rows.count() == 2
        assert sorted(r.calculated_at for r in rows) == [
            NOW,
            NOW + timedelta(hours=1),
        ]
    for pk, fields in first.items():
        assert model_to_dict(PeerComparison.objects.get(pk=pk)) == fields
    for row in PeerComparison.objects.select_related("indicator"):
        assert row.indicator.asset_id == row.asset_id
        assert row.indicator.calculated_at == row.calculated_at


@pytest.mark.usefixtures("silver")
def test_rf10_acao_que_falhou_na_primeira_fase_fica_fora_do_grupo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """As quatro companhias no mesmo segmento; a VALE3 falha no indicador. O grupo das
    outras e o das tres que ficaram gravadas, e a contagem do `roe` e 3, nao 4."""
    add_base_prices()
    classify(TICKERS, ENERGY)
    real = compute.write_indicator

    def vale_breaks(
        asset: Asset, calculated_at: datetime, values: Any, statement: Any
    ) -> None:
        if asset.ticker == "VALE3":
            raise RuntimeError("gravacao quebrou")
        real(asset, calculated_at, values, statement)

    monkeypatch.setattr("apps.fundamentals.compute.write_indicator", vale_breaks)

    with pytest.raises(FundamentalsFailed) as info:
        run_compute_fundamentals(now=clock(NOW))

    assert str(info.value) == "VALE3"
    assert not PeerComparison.objects.filter(asset__ticker="VALE3").exists()
    others = [t for t in TICKERS if t != "VALE3"]
    assert (
        sorted(PeerComparison.objects.values_list("asset__ticker", flat=True)) == others
    )
    for ticker in others:
        row = comparison(ticker)
        assert row.peer_level == PeerComparison.Level.SEGMENT
        assert row.roe_peer_count == 3
    assert re.search(
        r"^comparacao: 5 acoes, 0 sem grupo, 0 falhas$",
        info.value.report.render(),
        re.MULTILINE,
    )


@pytest.mark.usefixtures("silver")
def test_rf10_sem_comparacao_sem_indicador_da_execucao() -> None:
    """A segunda fase le so as linhas deste `calculated_at`: uma linha de outra execucao
    nao ganha comparacao nesta."""
    add_base_prices()
    classify(TICKERS, ENERGY)
    run_compute_fundamentals(now=clock(NOW))
    PeerComparison.objects.all().delete()  # declarado: so para isolar a segunda execucao

    later = NOW + timedelta(hours=1)
    run_compute_fundamentals(now=clock(later))

    assert PeerComparison.objects.count() == len(TICKERS)
    assert set(PeerComparison.objects.values_list("calculated_at", flat=True)) == {
        later
    }
    assert FundamentalIndicator.objects.count() == 2 * len(TICKERS)


# RF-11, de ponta a ponta


@pytest.mark.usefixtures("silver")
def test_rf11_tres_companhias_no_segmento_e_o_resto_sem_grupo() -> None:
    add_base_prices()
    classify(["PETR4", "VALE3", "ITUB4"], ENERGY)
    classify(["SAPR3", "SAPR4", "SAPR11"], SANITATION)

    report = run_compute_fundamentals(now=clock(NOW))

    for ticker in ("PETR4", "VALE3", "ITUB4"):
        row = comparison(ticker)
        assert row.peer_level == PeerComparison.Level.SEGMENT
        assert (row.group_sector, row.group_subsector, row.group_segment) == ENERGY
        assert row.roe_peer_count == 3
        assert row.roe_peer_median is not None
        assert row.roe_percentile is not None
        assert 0 <= row.roe_percentile <= 1
    for ticker in ("SAPR3", "SAPR4", "SAPR11"):
        row = comparison(ticker)
        assert row.peer_level == PeerComparison.Level.NONE
        assert (row.group_sector, row.group_subsector, row.group_segment) == (
            None,
            None,
            None,
        )
        assert row.roe_peer_median is None
        assert row.roe_percentile is None
        assert row.roe_peer_count is None
    assert re.search(
        r"^comparacao: 6 acoes, 3 sem grupo, 0 falhas$",
        report.render(),
        re.MULTILINE,
    )


# RF-15


def petr4_breaks_after_writing(
    monkeypatch: pytest.MonkeyPatch, written: list[str]
) -> None:
    """A comparacao da PETR4 grava e so entao levanta: o `atomic()` dela tem de reverter."""
    real = compute.write_peer_comparison

    def substitute(indicator: FundamentalIndicator, found: Comparison) -> None:
        real(indicator, found)
        written.append(indicator.asset.ticker)
        if indicator.asset.ticker == "PETR4":
            assert PeerComparison.objects.filter(indicator=indicator).exists()
            raise RuntimeError("falha depois de gravar")

    monkeypatch.setattr("apps.fundamentals.compute.write_peer_comparison", substitute)


@pytest.mark.usefixtures("silver")
def test_rf15_falha_na_comparacao_de_uma_acao_reverte_so_ela(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_base_prices()
    classify(TICKERS, ENERGY)
    written: list[str] = []
    petr4_breaks_after_writing(monkeypatch, written)

    with pytest.raises(FundamentalsFailed) as info:
        run_compute_fundamentals(now=clock(NOW))

    assert "PETR4" in written  # o cenario montou: gravou antes de levantar
    assert FundamentalIndicator.objects.filter(asset__ticker="PETR4").exists()
    assert not PeerComparison.objects.filter(asset__ticker="PETR4").exists()
    others = [t for t in TICKERS if t != "PETR4"]
    assert (
        sorted(PeerComparison.objects.values_list("asset__ticker", flat=True)) == others
    )
    assert str(info.value) == "PETR4 (comparacao)"
    lines = info.value.report.render().splitlines()
    assert lines[-3:] == [
        "PETR4: comparacao FALHOU (RuntimeError: falha depois de gravar)",
        "comparacao: 6 acoes, 0 sem grupo, 1 falhas",
        "calculo: 6 acoes, 0 sem balanco, 0 fora de escala, 0 falhas",
    ]
    assert [line.split(":")[0] for line in lines[:-3]] == TICKERS


@pytest.mark.usefixtures("silver")
def test_rf15_comando_com_falha_na_comparacao_sai_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_base_prices()
    classify(TICKERS, ENERGY)
    petr4_breaks_after_writing(monkeypatch, [])
    monkeypatch.setattr(
        COMMAND_POINT, functools.partial(run_compute_fundamentals, now=clock(NOW))
    )
    stdout = StringIO()

    with pytest.raises(CommandError) as info:
        call_command("compute_fundamentals", stdout=stdout)

    assert info.value.returncode == 1
    assert str(info.value) == "calculo com falhas: PETR4 (comparacao)"
    assert str(info.value).endswith("PETR4 (comparacao)")
    saida = stdout.getvalue()
    assert re.search(
        r"^PETR4: comparacao FALHOU \(RuntimeError: falha depois de gravar\)$",
        saida,
        re.MULTILINE,
    )
    assert saida.splitlines()[-1].startswith("calculo: ")


@pytest.mark.usefixtures("silver")
def test_rf15_mensagem_com_as_duas_fases(monkeypatch: pytest.MonkeyPatch) -> None:
    """VALE3 falha no indicador e PETR4 na comparacao: a mensagem lista as duas fases, a
    primeira antes."""
    add_base_prices()
    classify(TICKERS, ENERGY)
    real = compute.write_indicator

    def vale_breaks(
        asset: Asset, calculated_at: datetime, values: Any, statement: Any
    ) -> None:
        if asset.ticker == "VALE3":
            raise RuntimeError("gravacao quebrou")
        real(asset, calculated_at, values, statement)

    monkeypatch.setattr("apps.fundamentals.compute.write_indicator", vale_breaks)
    petr4_breaks_after_writing(monkeypatch, [])
    monkeypatch.setattr(
        COMMAND_POINT, functools.partial(run_compute_fundamentals, now=clock(NOW))
    )

    with pytest.raises(CommandError) as info:
        call_command("compute_fundamentals", stdout=StringIO())

    assert str(info.value) == "calculo com falhas: VALE3, PETR4 (comparacao)"
