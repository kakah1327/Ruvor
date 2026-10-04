"""O calculo do laboratorio (M2.4, RF-01, RF-07, RF-10): V-04, V-05, o registry e o devido.

- **V-04, o prefixo**: com o motor real, o ativo de 800 pregoes, um a cada 5 dias de
  calendario. A decada (`decade_of(valid_bars(asset))`) fica com ~731 -- teste de ~478, que
  cruza o retreino de 252 --, e a serie inteira tem teste de 547, que cruza o de 504. Para cada
  um dos seis modelos nao neurais, `run_experiment` sobre a decada e sobre a serie inteira, sem
  retratos: o VaR da decada e igual, ponto a ponto, ao comeco do VaR da inteira;
- **V-05, os retratos**: o `run_models` da producao para o `caviar` sobre a serie inteira grava
  os retratos; o `run_lab` depois os reaproveita todos e nao treina nenhum, nos dois niveis.
  Sem retratos, treina um por ponto de retreino da decada. Os outros oito modelos saem do motor
  de troca (`tests/risk/lab_de_teste.py`): nenhum teste treina as redes;
- **o registry** (D-66): com o `_REGISTRY` do motor trocado por um vazio e as funcoes de carga
  por espioes que o preenchem, `run_lab` as chama antes de calcular; faltando um modelo, grava
  o `lab_run` `failed` com o nome e nao chama o motor;
- **o devido**: cada condicao o derruba sozinha, e o `partial` e o `failed` gravados nao.
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import date, timedelta
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd
import pytest
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, run_experiment
from engine.models import load_all_model_modules
from engine.models import registry as model_registry

from apps.assets.models import Asset, Price
from apps.risk import config
from apps.risk.compute import MODELS, run_models
from apps.risk.decade import Decade, decade_of, valid_bars
from apps.risk.lab import LabIdentity, LabOutcome, identity_for, lab_due, run_lab
from apps.risk.models import LabResult, LabRun
from apps.risk.provider import SilverPriceProvider
from apps.risk.snapshots import SnapshotKey, library_versions
from tests.risk.lab_de_teste import ativo, motor_parcial, serie_rala

pytestmark = pytest.mark.django_db

NAO_NEURAIS = [
    "historical",
    "parametric",
    "monte_carlo",
    "garch_1_1",
    "egarch",
    "caviar",
]


@pytest.fixture(autouse=True)
def registry() -> None:
    load_all_model_modules()
    load_all_backtest_modules()


def _var(model_name: str, bars: list[Price], ticker: str) -> pd.Series:
    resultado = run_experiment(
        ExperimentConfig(
            ticker=ticker,
            start=bars[0].date.isoformat(),
            end=bars[-1].date.isoformat(),
            model_names=[model_name],
            backtest_names=[],
            alphas=list(config.ALPHAS),
            train_window_days=config.TRAIN_WINDOW_DAYS,
            seed=config.DEFAULT_SEED,
        ),
        SilverPriceProvider(),
    )
    series = []
    for run in resultado.runs:
        assert run.error is None, run.error
        assert run.estimate is not None
        series.append(run.estimate.var_series)
    return pd.concat(series, keys=[str(a) for a in config.ALPHAS])


def _decada(asset: Asset) -> Decade:
    decada = decade_of(valid_bars(asset))
    assert decada is not None
    return decada


# --- V-04: a decada e o prefixo da serie de producao ---------------------------------------


@pytest.mark.parametrize("modelo", NAO_NEURAIS)
def test_v04_o_var_da_decada_e_o_comeco_do_var_da_serie_inteira(modelo: str) -> None:
    asset = ativo()
    serie_rala(asset)
    inteira = valid_bars(asset)
    decada = _decada(asset)

    assert len(inteira) == 800
    assert decada.end_date == date(2025, 1, 5)  # dez anos depois de 2015-01-05
    assert 725 <= decada.sessions <= 735
    teste_decada = decada.sessions - 1 - config.TRAIN_WINDOW_DAYS
    teste_inteira = len(inteira) - 1 - config.TRAIN_WINDOW_DAYS
    assert 252 < teste_decada < 504  # cruza o retreino de 252
    assert teste_inteira == 547  # cruza o de 504

    var_decada = _var(modelo, decada.series, asset.ticker)
    var_inteira = _var(modelo, inteira, asset.ticker)
    for alpha in config.ALPHAS:
        d = var_decada.loc[str(alpha)]
        i = var_inteira.loc[str(alpha)]
        assert len(d) == teste_decada and len(i) == teste_inteira
        comeco = i.iloc[: len(d)]
        assert list(d.index) == list(comeco.index)
        # igual ponto a ponto: nenhuma tolerancia
        assert np.array_equal(d.to_numpy(), comeco.to_numpy()), (
            modelo,
            alpha,
            float(np.max(np.abs(d.to_numpy() - comeco.to_numpy()))),
        )


# --- V-05: os retratos da producao ---------------------------------------------------------


def _pontos_de_retreino(decada: Decade) -> int:
    teste = decada.sessions - 1 - config.TRAIN_WINDOW_DAYS
    return math.ceil(teste / 252)


def _caviar(run: LabRun) -> dict[str, tuple[int | None, int | None]]:
    return {
        str(r.alpha): (r.reused_snapshots, r.trained_snapshots)
        for r in LabResult.objects.filter(run=run, model_name="caviar")
    }


def test_v05_com_os_retratos_da_producao_o_caviar_nao_treina(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = ativo()
    serie_rala(asset)
    inteira = valid_bars(asset)
    chave = SnapshotKey(
        asset=asset,
        seed=config.DEFAULT_SEED,
        engine_version=version("ruvor-engine"),
        train_window_days=config.TRAIN_WINDOW_DAYS,
        first_price_date=inteira[0].date,
        library_versions=library_versions(),
    )
    _, contagens = run_models(chave, inteira, ["caviar"], full=False)
    assert contagens[("caviar", 0.05)] == (0, 3)  # a producao treina os tres pontos

    motor_parcial(monkeypatch, frozenset({"caviar"}))
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.run is not None
    assert desfecho.run.status == LabRun.Status.OK, desfecho.run.error
    pontos = _pontos_de_retreino(_decada(asset))
    assert pontos == 2
    assert _caviar(desfecho.run) == {"0.0500": (pontos, 0), "0.0100": (pontos, 0)}


def test_v05_sem_retratos_o_caviar_treina_um_por_ponto_da_decada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = ativo()
    serie_rala(asset)
    motor_parcial(monkeypatch, frozenset({"caviar"}))
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.run is not None
    assert desfecho.run.status == LabRun.Status.OK, desfecho.run.error
    pontos = _pontos_de_retreino(_decada(asset))
    assert _caviar(desfecho.run) == {"0.0500": (0, pontos), "0.0100": (0, pontos)}


def test_o_motor_recebe_a_serie_da_decada_e_os_nove(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = ativo()
    serie_rala(asset)
    motor = motor_parcial(monkeypatch)
    run_lab(asset, origin=LabRun.Origin.COMMAND)
    decada = _decada(asset)
    (chamada,) = motor.chamadas
    assert chamada.model_names == list(MODELS)
    assert chamada.start == decada.series[0].date.isoformat()
    assert chamada.end == decada.series[-1].date.isoformat()
    assert chamada.alphas == list(config.ALPHAS)


# --- o registry (D-66) ---------------------------------------------------------------------


def _espioes(
    monkeypatch: pytest.MonkeyPatch, sem: frozenset[str] = frozenset()
) -> list[str]:
    """Troca o `_REGISTRY` por um vazio e as cargas por espioes que o preenchem."""
    original = dict(model_registry._REGISTRY)
    vazio: dict[str, Any] = {}
    monkeypatch.setattr(model_registry, "_REGISTRY", vazio)
    ordem: list[str] = []

    def carga_modelos() -> None:
        ordem.append("modelos")
        vazio.update({k: v for k, v in original.items() if k not in sem})

    def carga_backtests() -> None:
        ordem.append("backtests")

    monkeypatch.setattr("apps.risk.lab.load_all_model_modules", carga_modelos)
    monkeypatch.setattr("apps.risk.lab.load_all_backtest_modules", carga_backtests)
    return ordem


def test_run_lab_carrega_o_registry_antes_de_calcular(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = ativo()
    serie_rala(asset)
    ordem = _espioes(monkeypatch)
    motor_parcial(monkeypatch, ajuste=lambda _runs: ordem.append("motor"))
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert ordem == ["modelos", "backtests", "motor"]
    assert desfecho.run is not None
    assert desfecho.run.status == LabRun.Status.OK, desfecho.run.error


def test_modelo_ausente_do_registry_grava_failed_sem_calcular(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset = ativo()
    serie_rala(asset)
    motor = motor_parcial(monkeypatch)
    ordem = _espioes(monkeypatch, sem=frozenset({"lstm"}))
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert ordem == ["modelos", "backtests"]
    assert motor.chamadas == []
    assert desfecho.run is not None
    run = LabRun.objects.get(pk=desfecho.run.pk)
    assert run.status == LabRun.Status.FAILED
    assert "lstm" in run.error
    assert LabResult.objects.filter(run=run).count() == 0


# --- o devido ------------------------------------------------------------------------------


def _grava(ident: LabIdentity, status: str, asset: Asset) -> LabRun:
    ultimo = valid_bars(asset)[-1]
    return LabRun.objects.create(
        asset=asset,
        calculated_at=timezone.now() + timedelta(seconds=LabRun.objects.count()),
        finished_at=timezone.now(),
        status=status,
        origin=LabRun.Origin.COMMAND,
        library_versions=ident.library_versions,
        as_of_date=ultimo.date,
        price_count=1,
        train_count=252,
        test_count=1,
        year_count=1,
        price_run=ultimo.run,
        price_fingerprint="f" * 64,
        requested_models=list(MODELS),
        **{k: v for k, v in ident.fields().items() if k != "asset_id"},
    )


def test_devido_com_o_ativo_ativo_e_a_decada_completa_e_suficiente() -> None:
    asset = ativo()
    serie_rala(asset)
    devido = lab_due(asset)
    assert devido is not None
    ident, decada = devido
    assert ident == identity_for(asset, decada)
    assert ident.asset_id == asset.pk
    assert ident.engine_version == version("ruvor-engine")
    assert ident.seed == config.DEFAULT_SEED
    assert ident.train_window_days == config.TRAIN_WINDOW_DAYS
    assert ident.first_price_date == decada.first_price_date
    assert ident.decade_end == decada.end_date
    assert ident.library_versions == library_versions()


def test_inativo_nao_e_devido() -> None:
    asset = ativo(status=Asset.Status.INACTIVE)
    serie_rala(asset)
    assert lab_due(asset) is None


def test_sem_pregao_nao_e_devido() -> None:
    assert lab_due(ativo()) is None


def test_decada_incompleta_nao_e_devida() -> None:
    asset = ativo()
    serie_rala(asset, 700)  # 3495 dias: a decada pede 3652
    decada = _decada(asset)
    assert not decada.complete and decada.sufficient
    assert lab_due(asset) is None


def test_decada_curta_nao_e_devida() -> None:
    asset = ativo()
    serie_rala(asset, 400, passo=10)  # 3990 dias, completa, ~366 na decada
    decada = _decada(asset)
    assert decada.complete and not decada.sufficient
    assert lab_due(asset) is None


def test_ok_gravado_da_identidade_tira_o_devido() -> None:
    asset = ativo()
    serie_rala(asset)
    devido = lab_due(asset)
    assert devido is not None
    _grava(devido[0], LabRun.Status.OK, asset)
    assert lab_due(asset) is None


@pytest.mark.parametrize("status", [LabRun.Status.PARTIAL, LabRun.Status.FAILED])
def test_partial_e_failed_gravados_nao_tiram_o_devido(status: str) -> None:
    asset = ativo()
    serie_rala(asset)
    devido = lab_due(asset)
    assert devido is not None
    _grava(devido[0], status, asset)
    assert lab_due(asset) == devido


def test_ok_de_outra_versao_do_motor_nao_tira_o_devido() -> None:
    asset = ativo()
    serie_rala(asset)
    devido = lab_due(asset)
    assert devido is not None
    _grava(replace(devido[0], engine_version="0.0.1"), LabRun.Status.OK, asset)
    assert lab_due(asset) == devido


@pytest.mark.parametrize(
    ("montagem", "tipo"),
    [
        ("inativo", LabOutcome.INACTIVE),
        ("sem_preco", LabOutcome.NO_PRICES),
        ("incompleta", LabOutcome.INCOMPLETE),
        ("curta", LabOutcome.SHORT),
        ("ok", LabOutcome.ALREADY),
    ],
)
def test_run_lab_pula_sem_gravar_e_diz_o_motivo(
    monkeypatch: pytest.MonkeyPatch, montagem: str, tipo: str
) -> None:
    motor = motor_parcial(monkeypatch)
    asset = ativo(status=Asset.Status.INACTIVE if montagem == "inativo" else "active")
    if montagem in ("inativo", "ok"):
        serie_rala(asset)
    elif montagem == "incompleta":
        serie_rala(asset, 700)
    elif montagem == "curta":
        serie_rala(asset, 400, passo=10)
    if montagem == "ok":
        devido = lab_due(asset)
        assert devido is not None
        _grava(devido[0], LabRun.Status.OK, asset)
    antes = LabRun.objects.count()
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.kind == tipo
    assert desfecho.skipped
    assert desfecho.run is None
    assert LabRun.objects.count() == antes
    assert motor.chamadas == []
    if tipo == LabOutcome.INCOMPLETE:
        assert desfecho.decade is not None
        assert desfecho.decade.end_date == date(2025, 1, 5)
