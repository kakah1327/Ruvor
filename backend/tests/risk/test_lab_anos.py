"""Os anos de teste (M2.4, RF-03): o V-03 do plano, Tarefa 3.

`split_years` se prova sobre series sinteticas -- retornos e VaR montados aqui, com datas de
dias uteis --, contra os backtests do motor chamados sobre o mesmo recorte: nenhum numero
esperado sai do codigo sob teste. O veredito do trecho (Kupiec **e** Christoffersen) se prova
com os dois testes substituidos por duplos que respondem o que o teste escolhe, porque nenhuma
serie produz as quatro combinacoes sob encomenda.

A soma divergente passa por `run_lab` inteiro, com o motor de troca de
`tests/risk/lab_de_teste.py` e as violacoes do Kupiec de um (modelo, nivel) aumentadas em um.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from engine.backtesting import get_backtest, load_all_backtest_modules
from engine.backtesting.base import BacktestResult, BacktestTest
from engine.experiments.runner import ModelRunResult

from apps.risk import config
from apps.risk.lab import YearSlice, run_lab, split_years
from apps.risk.models import LabResult, LabRun, LabYear
from tests.risk.lab_de_teste import ativo, motor_parcial, serie_rala


@pytest.fixture(autouse=True)
def backtests() -> None:
    load_all_backtest_modules()


def dias_uteis(quantidade: int, inicio: date = date(2017, 9, 25)) -> pd.DatetimeIndex:
    datas: list[date] = []
    dia = inicio
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia += timedelta(days=1)
    return pd.DatetimeIndex(pd.to_datetime(datas), name="date")


def serie(quantidade: int, *, semente: int = 3) -> tuple[pd.Series, pd.Series]:
    """Retornos normais de desvio 1,5% e um VaR constante de 2% sobre as mesmas datas."""
    indice = dias_uteis(quantidade)
    retornos = pd.Series(
        np.random.default_rng(semente).normal(0, 0.015, quantidade), index=indice
    )
    return retornos, pd.Series(0.02, index=indice)


# --- os cortes ----------------------------------------------------------------------------


def test_trechos_de_252_a_partir_da_posicao_0_e_o_ultimo_curto() -> None:
    retornos, var = serie(252 * 2 + 200)
    trechos = split_years(retornos, var, 0.05)
    assert [t.index for t in trechos] == [0, 1, 2]
    assert [t.test_count for t in trechos] == [252, 252, 200]
    inicios = [0, 252, 504]
    fins = [251, 503, 703]
    assert [t.start_date for t in trechos] == [
        retornos.index[i].date() for i in inicios
    ]
    assert [t.end_date for t in trechos] == [retornos.index[i].date() for i in fins]
    for t, inicio in zip(trechos, inicios, strict=True):
        r = retornos.iloc[inicio : inicio + 252]
        v = var.iloc[inicio : inicio + 252]
        assert t.violations == int((r < -v).sum())
        assert t.expected == pytest.approx(len(r) * 0.05)
    assert sum(t.violations for t in trechos) == int((retornos < -var).sum())


def test_o_alinhamento_e_o_do_runner() -> None:
    """O teste alinhado ao indice do VaR, sem as datas que o VaR nao tem."""
    retornos, var = serie(600)
    var_sem_o_comeco = var.iloc[10:]
    trechos = split_years(retornos, var_sem_o_comeco, 0.05)
    assert trechos[0].start_date == retornos.index[10].date()
    assert sum(t.test_count for t in trechos) == 590


def test_os_trechos_nao_seguem_o_ano_de_calendario() -> None:
    """O primeiro retorno e de setembro: o trecho 0 atravessa a virada do ano."""
    retornos, var = serie(300)
    trechos = split_years(retornos, var, 0.05)
    assert trechos[0].start_date.year == 2017
    assert trechos[0].end_date.year == 2018
    assert trechos[0].test_count == 252


@pytest.mark.parametrize(("ultimo", "julgado"), [(125, False), (126, True)])
def test_o_trecho_com_menos_de_126_nao_e_julgado(ultimo: int, julgado: bool) -> None:
    retornos, var = serie(252 + ultimo)
    trechos = split_years(retornos, var, 0.05)
    assert [t.test_count for t in trechos] == [252, ultimo]
    curto = trechos[-1]
    assert (curto.kupiec is not None) is julgado
    assert (curto.christoffersen is not None) is julgado
    assert (curto.adequate is not None) is julgado
    # violacoes e esperadas sempre
    r, v = retornos.iloc[252:], var.iloc[252:]
    assert curto.violations == int((r < -v).sum())
    assert curto.expected == pytest.approx(ultimo * 0.05)


def test_a_95_os_testes_sao_os_do_motor_sobre_o_recorte() -> None:
    retornos, var = serie(252 * 2)
    for t, inicio in zip(split_years(retornos, var, 0.05), [0, 252], strict=True):
        r = retornos.iloc[inicio : inicio + 252]
        v = var.iloc[inicio : inicio + 252]
        kupiec = get_backtest("kupiec")().run(r, v, 0.05)
        christoffersen = get_backtest("christoffersen")().run(r, v, 0.05)
        assert t.kupiec is not None and t.christoffersen is not None
        assert t.kupiec.p_value == kupiec.p_value
        assert t.kupiec.details["violations"] == t.violations
        assert t.christoffersen.p_value == christoffersen.p_value
        assert t.adequate is (kupiec.passed and christoffersen.passed)


def test_a_99_os_testes_sao_nulos_em_todo_trecho() -> None:
    retornos, var = serie(252 * 3 + 200)
    trechos = split_years(retornos, var, 0.01)
    assert len(trechos) == 4
    for t in trechos:
        assert t.kupiec is None
        assert t.christoffersen is None
        assert t.adequate is None
    assert [t.expected for t in trechos] == pytest.approx(
        [252 * 0.01, 252 * 0.01, 252 * 0.01, 200 * 0.01]
    )


def test_o_nivel_julgado_e_o_float_de_config() -> None:
    assert config.LAB_JUDGED_ALPHAS == (0.05,)
    assert config.ALPHAS == (0.05, 0.01)


# --- o veredito do trecho -----------------------------------------------------------------


def _duplo(nome: str, passou: bool) -> type[BacktestTest]:
    class Duplo(BacktestTest):
        def run(
            self, returns: pd.Series, var_series: pd.Series, alpha: float
        ) -> BacktestResult:
            return BacktestResult(nome, 0.0, 0.5, passou, {"violations": 0})

    Duplo.name = nome
    return Duplo


@pytest.mark.parametrize(
    ("kupiec", "christoffersen", "veredito"),
    [
        (True, True, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
    ],
)
def test_o_veredito_do_trecho_e_kupiec_e_christoffersen(
    monkeypatch: pytest.MonkeyPatch, kupiec: bool, christoffersen: bool, veredito: bool
) -> None:
    duplos = {
        "kupiec": _duplo("kupiec", kupiec),
        "christoffersen": _duplo("christoffersen", christoffersen),
    }
    monkeypatch.setattr("apps.risk.lab.get_backtest", duplos.__getitem__)
    retornos, var = serie(252)
    (trecho,) = split_years(retornos, var, 0.05)
    assert trecho.adequate is veredito


def test_o_veredito_e_nulo_sem_os_testes() -> None:
    sem = YearSlice(0, date(2020, 1, 2), date(2020, 12, 30), 100, 3, 5.0, None, None)
    assert sem.adequate is None


# --- a soma divergente --------------------------------------------------------------------


@pytest.mark.django_db
def test_a_soma_divergente_grava_so_um_lab_run_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def desalinha(runs: list[ModelRunResult]) -> None:
        for run in runs:
            if (run.model_name, run.alpha) == ("historical", 0.01):
                for bt in run.backtests:
                    if bt.test_name == "kupiec":
                        bt.details["violations"] += 1

    motor_parcial(monkeypatch, ajuste=desalinha)
    asset = ativo()
    serie_rala(asset)
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)

    assert desfecho.kind == desfecho.WRITTEN
    runs = list(LabRun.objects.filter(asset=asset))
    assert len(runs) == 1
    (run,) = runs
    assert run.status == LabRun.Status.FAILED
    assert "historical" in run.error
    assert "0.01" in run.error
    # as duas somas: a dos anos e a da decada, que difere em um
    numeros = [int(p) for p in run.error.replace(",", " ").split() if p.isdigit()]
    assert len(numeros) == 2 and numeros[1] == numeros[0] + 1, run.error
    assert LabResult.objects.count() == 0
    assert LabYear.objects.count() == 0
    assert desfecho.run is not None and desfecho.run.pk == run.pk


@pytest.mark.django_db
def test_sem_divergencia_os_dezoito_resultados_e_os_anos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O contraponto da soma: com o motor de troca intacto, nada falha."""
    motor_parcial(monkeypatch)
    asset = ativo()
    serie_rala(asset)
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.run is not None
    assert desfecho.run.status == LabRun.Status.OK, desfecho.run.error
    assert LabResult.objects.filter(run=desfecho.run).count() == 18
    for resultado in LabResult.objects.filter(run=desfecho.run):
        anos = list(resultado.years.order_by("index"))
        assert sum(a.violations for a in anos) == resultado.violations
        assert len(anos) == desfecho.run.year_count
        if resultado.alpha == Decimal("0.0100"):
            assert all(a.kupiec_passed is None and a.adequate is None for a in anos)
        else:
            assert all(a.adequate is not None for a in anos if a.test_count >= 126)
