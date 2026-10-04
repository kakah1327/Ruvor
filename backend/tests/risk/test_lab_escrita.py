"""A gravacao do laboratorio (M2.4, RF-04 a RF-08, RF-10): o V-06 (a gravacao) e a corrida
`ok` x `partial` do V-09, Tarefa 3.

O motor e o de troca de `tests/risk/lab_de_teste.py`: os nove modelos sinteticos, sem rede
nenhuma; o que se prova aqui e o que a escrita faz com o que recebeu.

**A corrida** e `transaction=True` (`TRANSACIONAL` e `banco_limpo`), com duas threads chamando
`write_lab` da mesma identidade -- cada uma na sua conexao. O ponto de desvio `_after_lab_lock`
e trocado por um que, so na thread do `ok`, avisa que ela tem a trava e espera a outra partir
(e mais meio segundo, para ela chegar a trava -- ou a uma conferencia feita antes dela). Com a
conferencia sob a trava, a outra espera o commit do `ok` e nao grava; com a conferencia antes da
trava, ou sem conferencia, grava depois do `ok`. Cada thread fecha a conexao no `finally`, e o
teste reprova se alguma ficou viva.
"""

from __future__ import annotations

import math
import threading
import time
from datetime import timedelta
from decimal import Decimal
from importlib.metadata import version
from typing import Any

import pytest
from django.db import connections
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ModelRunResult
from engine.models import load_all_model_modules

from apps.assets.models import CollectionRun
from apps.risk import config
from apps.risk.compute import MODELS
from apps.risk.decade import decade_of, valid_bars
from apps.risk.lab import LabOutcome, lab_due, run_lab, write_lab
from apps.risk.models import LabResult, LabRun, LabYear
from apps.risk.snapshots import price_fingerprint
from tests.api.migracao import TRANSACIONAL, banco_limpo  # noqa: F401
from tests.risk.lab_de_teste import agora_fixo, ativo, motor_parcial, serie_rala

DB = pytest.mark.django_db
INICIO = timezone.now().replace(microsecond=0)
FIM = INICIO + timedelta(seconds=7)


@pytest.fixture(autouse=True)
def registry() -> None:
    load_all_model_modules()
    load_all_backtest_modules()


# --- V-06: a gravacao -----------------------------------------------------------------------


@DB
def test_o_manifesto_e_os_dezoito_resultados(monkeypatch: pytest.MonkeyPatch) -> None:
    motor_parcial(monkeypatch)
    asset = ativo()
    # o maior `run` cai num pregao do meio da decada, nao no ultimo
    comum = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    tardia = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    assert tardia.pk > comum.pk
    serie_rala(asset, comum=comum, coletas={300: tardia})
    decada = decade_of(valid_bars(asset))
    assert decada is not None

    desfecho = run_lab(
        asset, origin=LabRun.Origin.RISK_CLOSE, now=agora_fixo(INICIO, FIM)
    )
    assert desfecho.kind == LabOutcome.WRITTEN
    assert desfecho.run is not None
    run = LabRun.objects.get(pk=desfecho.run.pk)
    serie = decada.series
    teste = len(serie) - 1 - config.TRAIN_WINDOW_DAYS
    assert run.status == LabRun.Status.OK
    assert run.origin == LabRun.Origin.RISK_CLOSE
    assert run.error == ""
    assert (run.calculated_at, run.finished_at) == (INICIO, FIM)
    assert run.engine_version == version("ruvor-engine")
    assert run.seed == config.DEFAULT_SEED
    assert run.train_window_days == config.TRAIN_WINDOW_DAYS
    assert run.first_price_date == serie[0].date
    assert run.decade_end == decada.end_date
    assert run.as_of_date == serie[-1].date
    assert run.as_of_date <= run.decade_end
    assert run.price_count == len(serie)
    assert run.train_count == config.TRAIN_WINDOW_DAYS
    assert run.test_count == teste
    assert run.year_count == math.ceil(teste / 252)
    assert run.price_run_id == tardia.pk
    assert run.price_fingerprint == price_fingerprint(serie, len(serie) - 1)
    inteira = valid_bars(asset)
    assert run.price_fingerprint != price_fingerprint(inteira, len(inteira) - 1)
    assert run.requested_models == list(MODELS)
    assert len(run.library_versions_hash) == 64
    assert set(run.library_versions) == {
        "tensorflow",
        "keras",
        "numpy",
        "scipy",
        "pandas",
        "arch",
    }

    resultados = list(LabResult.objects.filter(run=run))
    assert len(resultados) == 18
    assert {(r.model_name, r.alpha) for r in resultados} == {
        (m, a) for m in MODELS for a in (Decimal("0.0500"), Decimal("0.0100"))
    }
    for r in resultados:
        assert r.error == ""
        assert r.test_count == teste
        assert r.violations is not None
        assert r.expected_violations is not None
        assert r.kupiec_p_value is not None and r.christoffersen_p_value is not None
        assert r.dq_passed is not None and r.dq_p_value is not None  # o DQ na decada
        assert r.adequate is (r.kupiec_passed and r.christoffersen_passed)
        assert r.hyperparameters is not None
        anos = list(r.years.order_by("index"))
        assert [a.index for a in anos] == list(range(run.year_count))
        assert sum(a.test_count for a in anos) == teste


@DB
def test_nenhuma_coluna_de_basileia_e_o_dq_so_na_decada() -> None:
    resultado = {f.name for f in LabResult._meta.get_fields()}
    ano = {f.name for f in LabYear._meta.get_fields()}
    assert not {"basel_zone", "var_latest", "var_mean"} & resultado
    assert {"dq_passed", "dq_p_value"} <= resultado
    assert not {"dq_passed", "dq_p_value", "basel_zone"} & ano


@DB
def test_o_modelo_com_erro_grava_numeros_nulos_e_adequate_nulo_sem_anos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def quebra(runs: list[ModelRunResult]) -> None:
        for i, run in enumerate(runs):
            if (run.model_name, run.alpha) == ("parametric", 0.05):
                runs[i] = ModelRunResult(
                    model_name="parametric", alpha=0.05, error="boom"
                )

    motor_parcial(monkeypatch, ajuste=quebra)
    asset = ativo()
    serie_rala(asset)
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.run is not None
    run = LabRun.objects.get(pk=desfecho.run.pk)
    assert run.status == LabRun.Status.PARTIAL
    falho = LabResult.objects.get(
        run=run, model_name="parametric", alpha=Decimal("0.0500")
    )
    assert falho.error == "boom"
    for campo in (
        "test_count",
        "violations",
        "expected_violations",
        "kupiec_passed",
        "kupiec_p_value",
        "christoffersen_passed",
        "christoffersen_p_value",
        "dq_passed",
        "dq_p_value",
        "adequate",
        "reused_snapshots",
        "trained_snapshots",
    ):
        assert getattr(falho, campo) is None, campo
    assert falho.years.count() == 0
    # o outro nivel do mesmo modelo segue inteiro
    par = LabResult.objects.get(
        run=run, model_name="parametric", alpha=Decimal("0.0100")
    )
    assert par.error == "" and par.adequate is not None and par.years.count() > 0
    assert LabResult.objects.filter(run=run).count() == 18


@DB
def test_os_caros_sem_erro_contam_os_retratos_e_os_baratos_nao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    motor_parcial(monkeypatch)
    asset = ativo()
    serie_rala(asset)
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.run is not None
    for r in LabResult.objects.filter(run=desfecho.run):
        if r.model_name in ("caviar", "garchnet", "gru", "lstm"):
            assert (r.reused_snapshots, r.trained_snapshots) == (0, 0)
        else:
            assert (r.reused_snapshots, r.trained_snapshots) == (None, None)


@DB
def test_a_excecao_antes_dos_resultados_grava_failed_com_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("serie ilegivel")

    monkeypatch.setattr("apps.risk.compute.run_experiment", explode)
    asset = ativo()
    serie_rala(asset)
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.run is not None
    run = LabRun.objects.get(pk=desfecho.run.pk)
    assert run.status == LabRun.Status.FAILED
    assert run.error == "ValueError: serie ilegivel"
    assert LabResult.objects.filter(run=run).count() == 0


@DB
def test_a_falha_na_escrita_dos_anos_nao_deixa_execucao_nem_resultado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    motor_parcial(monkeypatch)
    asset = ativo()
    serie_rala(asset)

    def falha(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("falha forcada nos anos")

    monkeypatch.setattr(LabYear.objects, "bulk_create", falha)
    with pytest.raises(RuntimeError, match="falha forcada nos anos"):
        run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert LabRun.objects.count() == 0
    assert LabResult.objects.count() == 0
    assert LabYear.objects.count() == 0


@DB
def test_com_ok_gravado_a_escrita_nao_grava_nem_partial_nem_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A conferencia sob a trava, sem corrida: o `ok` ja esta la quando a escrita chega."""
    asset = ativo()
    serie_rala(asset)
    devido = lab_due(asset)
    assert devido is not None
    ident, decada = devido
    gravado = write_lab(
        ident,
        decada,
        origin=LabRun.Origin.COMMAND,
        calculated_at=INICIO,
        finished_at=FIM,
        status=LabRun.Status.OK,
        error="",
        results=[],
        years={},
    )
    assert gravado is not None
    for status in (LabRun.Status.PARTIAL, LabRun.Status.FAILED, LabRun.Status.OK):
        assert (
            write_lab(
                ident,
                decada,
                origin=LabRun.Origin.COMMAND,
                calculated_at=FIM,
                finished_at=FIM,
                status=status,
                error="x",
                results=[],
                years={},
            )
            is None
        )
    assert list(LabRun.objects.values_list("status", flat=True)) == ["ok"]


@DB
def test_o_integrity_error_da_identidade_vira_ja_calculado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dois `ok` que passassem a conferencia: o indice do banco decide, e `run_lab` nao levanta."""
    motor_parcial(monkeypatch)
    asset = ativo()
    serie_rala(asset)
    devido = lab_due(asset)
    assert devido is not None
    ident, decada = devido
    # a conferencia "nao ve" o `ok`, e o banco o recusa
    real = LabRun.objects.filter

    def cego(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("status") == LabRun.Status.OK:
            return real(pk=-1)
        return real(*args, **kwargs)

    write_lab(
        ident,
        decada,
        origin=LabRun.Origin.COMMAND,
        calculated_at=INICIO,
        finished_at=FIM,
        status=LabRun.Status.OK,
        error="",
        results=[],
        years={},
    )
    monkeypatch.setattr(LabRun.objects, "filter", cego)
    desfecho = run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert desfecho.kind == LabOutcome.ALREADY
    assert desfecho.run is None
    assert LabRun.objects.count() == 1


# --- V-09: a corrida `ok` x `partial`, a metade da escrita ----------------------------------

ESPERA = 5
JOIN = 30


def _corrida(
    monkeypatch: pytest.MonkeyPatch, segundo_status: str
) -> tuple[list[Any], list[BaseException]]:
    asset = ativo()
    serie_rala(asset)
    devido = lab_due(asset)
    assert devido is not None
    ident, decada = devido

    ok_tem_trava = threading.Event()
    segundo_partiu = threading.Event()
    devolvidos: dict[str, Any] = {}
    erros: list[BaseException] = []

    def desvio() -> None:
        if threading.current_thread().name == "ok":
            ok_tem_trava.set()
            assert segundo_partiu.wait(ESPERA)
            time.sleep(0.5)  # a outra chega a trava, ou a uma conferencia antes dela

    def grava(status: str) -> None:
        try:
            if threading.current_thread().name != "ok":
                segundo_partiu.set()
            devolvidos[threading.current_thread().name] = write_lab(
                ident,
                decada,
                origin=LabRun.Origin.COMMAND,
                calculated_at=INICIO if status == "ok" else FIM,
                finished_at=FIM,
                status=status,
                error="",
                results=[],
                years={},
            )
        except BaseException as exc:  # registrado e conferido depois do join
            erros.append(exc)
        finally:
            connections.close_all()

    monkeypatch.setattr("apps.risk.lab._after_lab_lock", desvio)
    primeira = threading.Thread(target=grava, args=(LabRun.Status.OK,), name="ok")
    primeira.start()
    assert ok_tem_trava.wait(ESPERA)
    segunda = threading.Thread(target=grava, args=(segundo_status,), name="segundo")
    segunda.start()
    for thread in (primeira, segunda):
        thread.join(JOIN)
        assert not thread.is_alive()
    return [devolvidos.get("ok"), devolvidos.get("segundo")], erros


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_v09_o_partial_que_termina_depois_do_ok_nao_grava(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (ok, segundo), erros = _corrida(monkeypatch, LabRun.Status.PARTIAL)
    assert erros == []
    assert ok is not None
    assert segundo is None
    assert list(LabRun.objects.values_list("status", flat=True)) == ["ok"]


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_v09_dois_ok_terminam_com_um(monkeypatch: pytest.MonkeyPatch) -> None:
    (ok, segundo), erros = _corrida(monkeypatch, LabRun.Status.OK)
    assert erros == []
    assert ok is not None
    assert segundo is None
    assert list(LabRun.objects.values_list("status", flat=True)) == ["ok"]
