"""O estado da execucao: a regra do fecho, a copia dela na migration, e o V-10c.

O V-10c nao usa `MigrationExecutor`: migrar para tras e para a frente dentro do teste nao
funciona neste repositorio (o `flush` do `transaction=True` nao restaura a organizacao
`ruvor` para os testes que rodam depois, e sem ele a FK adiavel da `pending trigger
events` ao alterar a tabela). Por isso ele se divide em tres partes:

- **(a) a funcao**: o `backfill` da `0002`, chamado com o registro de apps corrente sobre
  execucoes gravadas com `status` e `requested_models` sujos;
- **(b) a forma**: a lista `operations` da `0002` roda o `backfill` depois dos dois
  `AddField` -- e o que pega a migration sem o `RunPython`, em que o valor do `AddField`
  valeria para todo mundo;
- **(c) o dado real**: as oito linhas do banco, medidas na execucao real.

**As tarefas** (V-02 a V-06, idempotencia, serie mudou, registry) sao exercidas chamando as
**funcoes com sublinhado**, nunca a tarefa registrada, `.delay` ou `.apply_async`: o
`_enqueue` e substituido em todo teste deste arquivo por um duplo que guarda o que recebeu,
e o Redis dos testes aponta para um host que nao existe.

**Onde as substituicoes miram.** `apps/risk/tasks.py` importa pelo nome, e chama pelo nome
global **dele**, `run_experiment`, `write_results`, `load_all_model_modules` e
`load_all_backtest_modules` -- entao e em `apps.risk.tasks.*` que os duplos entram (o
`enqueue_compute` tambem chama o `_enqueue` pelo nome global deste modulo). Mirar
`apps.risk.compute.run_experiment` nao teria efeito nenhum na tarefa, e o V-05b aprovaria
vazio. O `get_model` quebrado do V-05 e o do **runner** (`engine.experiments.runner`), molde
do V-11 do M1.4: e a falha que nasce dentro do `run_experiment`.
"""

from __future__ import annotations

import importlib
import math
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import ModuleType
from typing import Any

import numpy as np
import pytest
from celery import chord
from django.apps import apps as django_apps
from django.db import migrations
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentResult, run_experiment
from engine.models import get_model, load_all_model_modules
from engine.models.base import VaRModel

from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.compute import MODELS, run_compute_risk, status_for, write_results
from apps.risk.models import RiskResult, RiskRun
from apps.risk.tasks import (
    _abrir_execucao,
    _compute_asset_model,
    _fechar_execucao,
    _recalcular_cobertos,
    enqueue_compute,
)

MIGRATION = "apps.risk.migrations.0002_risk_run_status_e_modelos"

INICIO = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def migration_module() -> ModuleType:
    return importlib.import_module(MIGRATION)


# --- a regra do fecho, e a copia dela na migration ----------------------------------------

CASOS = [
    ((18, 18, 0), "ok"),
    ((18, 18, 18), "failed"),
    ((18, 0, 0), "failed"),
    ((18, 12, 0), "partial"),
    ((18, 18, 2), "partial"),
    ((2, 2, 0), "ok"),
]


def _regras() -> list[tuple[str, Callable[[int, int, int], str]]]:
    return [
        ("compute", status_for),
        ("migration", migration_module().status_for),
    ]


@pytest.mark.parametrize(("argumentos", "esperado"), CASOS)
@pytest.mark.parametrize("origem", ["compute", "migration"])
def test_a_regra_do_fecho_e_a_copia_dela_dao_o_mesmo(
    origem: str, argumentos: tuple[int, int, int], esperado: str
) -> None:
    regra = dict(_regras())[origem]
    assert regra(*argumentos) == esperado


def test_a_lista_da_migration_e_a_de_compute() -> None:
    """A `0002` copia os nove porque nao pode importar o motor; a copia nao envelhece."""
    assert migration_module().MODELS == list(MODELS)


# --- V-10c (a): o backfill deriva do dado --------------------------------------------------


def _ativo(ticker: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=INICIO,
        updated_at=INICIO,
    )


def _execucao_suja(ticker: str, coleta: CollectionRun, modelos: list[str]) -> RiskRun:
    """Uma execucao com o estado sujo -- `running` e `[]` -- e dois resultados limpos por
    modelo, gravados na ordem **inversa** da pedida: a ordem de `MODELS` tem de vir do
    `backfill`, nao da ordem de insercao."""
    run = RiskRun.objects.create(
        asset=_ativo(ticker),
        calculated_at=INICIO,
        finished_at=INICIO,
        engine_version="0.2.0",
        seed=42,
        train_window_days=252,
        as_of_date=date(2026, 9, 18),
        first_price_date=date(2024, 9, 18),
        price_count=503,
        train_count=252,
        test_count=250,
        price_run=coleta,
        requested_by=None,
        status=RiskRun.Status.RUNNING,
        requested_models=[],
    )
    RiskResult.objects.bulk_create(
        [
            RiskResult(
                run=run,
                model_name=modelo,
                model_category="traditional",
                alpha=Decimal(alpha),
                hyperparameters={},
            )
            for modelo in reversed(modelos)
            for alpha in ("0.0500", "0.0100")
        ]
    )
    return run


@pytest.mark.django_db
def test_v10c_a_o_backfill_deriva_estado_e_modelos_de_cada_execucao() -> None:
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    completa = _execucao_suja("AAA3", coleta, list(MODELS))
    so_garch = _execucao_suja("BBB3", coleta, ["garch_1_1"])

    migration_module().backfill(django_apps, None)

    completa.refresh_from_db()
    so_garch.refresh_from_db()
    assert (completa.status, completa.requested_models) == ("ok", list(MODELS))
    assert (so_garch.status, so_garch.requested_models) == ("ok", ["garch_1_1"])


# --- V-10c (b): a migration roda o backfill -----------------------------------------------


def test_v10c_b_a_migration_adiciona_as_duas_colunas_e_roda_o_backfill() -> None:
    modulo = migration_module()
    operacoes = modulo.Migration.operations

    assert [type(op) for op in operacoes] == [
        migrations.AddField,
        migrations.AddField,
        migrations.RunPython,
    ]
    status, modelos, backfill = operacoes
    assert (status.model_name, status.name) == ("riskrun", "status")
    assert (modelos.model_name, modelos.name) == ("riskrun", "requested_models")
    assert backfill.code is modulo.backfill


# --- as tarefas: o duplo da fila e a serie -------------------------------------------------

BARATOS = ["parametric", "historical"]
ULTIMO_PREGAO = date(2026, 9, 18)  # sexta-feira
SABADO_NA_JANELA = date(2026, 9, 12)
SEGUNDA_DEPOIS = date(2026, 9, 21)


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """O duplo do `_enqueue`, em todo teste deste arquivo: guarda o que recebeu e nao fala
    com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.risk.tasks._enqueue", recebidos.append)
    return recebidos


def _serie(ticker: str, quantidade: int = config.MIN_SESSIONS) -> Asset:
    """`quantidade` pregoes em dias uteis terminando em `ULTIMO_PREGAO`, com log-retornos
    normais de desvio 1% a partir de 100."""
    asset = _ativo(ticker)
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    datas: list[date] = []
    dia = ULTIMO_PREGAO
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    nivel = 100.0
    retornos = np.random.default_rng(7).normal(0, 0.01, quantidade)
    linhas = []
    for dia, retorno in zip(sorted(datas), retornos, strict=True):
        nivel *= math.exp(float(retorno))
        valor = Decimal(str(nivel)).quantize(Decimal("0.000001"))
        linhas.append(_preco(asset, dia, valor, coleta))
    Price.objects.bulk_create(linhas)
    return asset


def _preco(asset: Asset, dia: date, valor: Decimal, coleta: CollectionRun) -> Price:
    return Price(
        asset=asset,
        date=dia,
        open=valor,
        high=valor,
        low=valor,
        close=valor,
        adj_close=valor,
        volume=1000,
        log_return=None,
        run=coleta,
        updated_at=INICIO,
    )


def _abre(models: list[str], ticker: str = "AAA3") -> RiskRun:
    """Uma execucao aberta pela tarefa de abertura, sobre uma serie de 503 pregoes."""
    _serie(ticker)
    run_id = _abrir_execucao(ticker, INICIO.isoformat(), 42, models)
    assert run_id is not None
    return RiskRun.objects.get(pk=run_id)


def _linhas(run: RiskRun) -> dict[tuple[str, str], RiskResult]:
    return {(r.model_name, str(r.alpha)): r for r in RiskResult.objects.filter(run=run)}


def _par_de_erro(run: RiskRun, model_name: str, error: str) -> None:
    """As duas linhas do modelo sao o par do `write_failed`: `error` igual, numeros nulos."""
    linhas = [r for (nome, _), r in _linhas(run).items() if nome == model_name]
    assert sorted(str(r.alpha) for r in linhas) == ["0.0100", "0.0500"]
    for linha in linhas:
        assert linha.error == error
        assert linha.model_category == get_model(model_name).category.value
        assert linha.var_latest is None
        assert linha.var_mean is None
        assert linha.violations is None
        assert linha.kupiec_passed is None
        assert linha.christoffersen_passed is None
        assert linha.dq_passed is None
        assert linha.basel_zone is None
        assert linha.adequate is None


def _limpas(run: RiskRun, model_name: str) -> None:
    linhas = [r for (nome, _), r in _linhas(run).items() if nome == model_name]
    assert len(linhas) == 2
    for linha in linhas:
        assert linha.error == ""
        assert linha.var_latest is not None


# --- V-02: a abertura enfileira, nao executa -----------------------------------------------


@pytest.mark.django_db
def test_v02_a_abertura_enfileira_um_chord_de_nove_e_nao_executa_nenhum(
    fila: list[Any],
) -> None:
    """Os nove numa ordem que nao e a de `MODELS`: a ordem do cabecalho tem de ser a pedida.

    Zero `risk_result` no mesmo teste e o que separa "enfileirou nove" de "executou nove em
    linha" -- a contagem sozinha passaria com o atalho errado.
    """
    _serie("AAA3")
    pedidos = list(reversed(MODELS))

    run_id = _abrir_execucao("AAA3", INICIO.isoformat(), 42, pedidos)

    assert run_id is not None
    assert len(fila) == 1
    grupo = fila[0]
    assert isinstance(grupo, chord)
    assert [(s.task, s.args) for s in grupo.tasks] == [
        ("apps.risk.tasks.compute_asset_model", (run_id, nome)) for nome in pedidos
    ]
    assert (grupo.body.task, grupo.body.args) == (
        "apps.risk.tasks.fechar_execucao",
        (run_id,),
    )
    # O corpo RECEBE a lista de resultados do cabecalho como primeiro argumento. Com `.si()`
    # ele seria chamado so com `run_id`, levantaria `TypeError`, e toda execucao ficaria
    # presa em `running` -- e `task` e `args` sao iguais nas duas formas.
    assert grupo.body.immutable is False
    assert RiskResult.objects.count() == 0
    run = RiskRun.objects.get(pk=run_id)
    assert (run.status, run.finished_at, run.requested_models) == (
        RiskRun.Status.RUNNING,
        None,
        pedidos,
    )
    assert run.calculated_at == INICIO


@pytest.mark.django_db
def test_serie_curta_na_abertura_devolve_none_sem_linha_e_sem_fila(
    fila: list[Any],
) -> None:
    _serie("AAA3", config.MIN_SESSIONS - 1)

    assert _abrir_execucao("AAA3", INICIO.isoformat(), 42, BARATOS) is None
    assert RiskRun.objects.count() == 0
    assert fila == []


# --- V-03: transacao por tarefa ------------------------------------------------------------


@pytest.mark.django_db
def test_v03_a_a_falha_de_escrita_de_um_modelo_nao_apaga_o_outro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _abre(BARATOS)
    _compute_asset_model(run.id, "parametric")

    def quebra(run: RiskRun, result: ExperimentResult) -> None:
        raise RuntimeError("escrita quebrada de proposito")

    monkeypatch.setattr("apps.risk.tasks.write_results", quebra)
    _compute_asset_model(run.id, "historical")

    assert len(_linhas(run)) == 4
    _limpas(run, "parametric")
    _par_de_erro(run, "historical", "RuntimeError: escrita quebrada de proposito")


@pytest.mark.django_db
def test_v03_b_a_escrita_da_tarefa_e_tudo_ou_nada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A escrita grava a primeira linha do par e levanta. Com a transacao da tarefa, a
    linha boa volta atras e o par de erro entra; sem ela, a linha boa sobrevive e o
    `write_failed` colide com a unicidade `(run, model_name, alpha)`."""
    run = _abre(BARATOS)

    def meia(run: RiskRun, result: ExperimentResult) -> None:
        write_results(run, ExperimentResult(result.config, result.runs[:1]))
        raise RuntimeError("meia escrita")

    monkeypatch.setattr("apps.risk.tasks.write_results", meia)
    _compute_asset_model(run.id, "parametric")

    assert len(_linhas(run)) == 2
    _par_de_erro(run, "parametric", "RuntimeError: meia escrita")


# --- V-04 e V-06: o parcial e visivel, e sem fecho fica `running` --------------------------


@pytest.mark.django_db
def test_v04_tres_de_nove_dao_seis_resultados_visiveis_e_running() -> None:
    run = _abre(list(MODELS))

    for nome in ("parametric", "historical", "monte_carlo"):
        _compute_asset_model(run.id, nome)

    run.refresh_from_db()
    assert run.results.count() == 6
    assert (run.status, run.finished_at) == (RiskRun.Status.RUNNING, None)


@pytest.mark.django_db
def test_v06_sem_o_fecho_a_execucao_fica_running_e_sem_fim() -> None:
    run = _abre(BARATOS)

    for nome in BARATOS:
        _compute_asset_model(run.id, nome)

    run.refresh_from_db()
    assert run.results.count() == 4
    assert (run.status, run.finished_at) == (RiskRun.Status.RUNNING, None)


# --- V-05 e V-05c: os tres fechos, relativos ao pedido --------------------------------------


@pytest.mark.django_db
def test_v05_ok_quando_os_dois_pedidos_gravam_limpos() -> None:
    run = _abre(BARATOS)
    for nome in BARATOS:
        _compute_asset_model(run.id, nome)

    _fechar_execucao([None, None], run.id)

    run.refresh_from_db()
    assert run.status == RiskRun.Status.OK
    assert run.finished_at is not None


@pytest.mark.django_db
def test_v05_partial_quando_um_dos_dois_falha_no_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = get_model

    def quebrado(nome: str) -> type[VaRModel]:
        if nome == "historical":
            raise RuntimeError("modelo quebrado de proposito")
        return original(nome)

    monkeypatch.setattr("engine.experiments.runner.get_model", quebrado)
    run = _abre(BARATOS)
    for nome in BARATOS:
        _compute_asset_model(run.id, nome)

    _fechar_execucao([None, None], run.id)

    run.refresh_from_db()
    assert run.results.exclude(error="").count() == 2
    assert run.status == RiskRun.Status.PARTIAL
    assert run.finished_at is not None


@pytest.mark.django_db
def test_v05_failed_quando_nenhuma_tarefa_rodou() -> None:
    run = _abre(BARATOS)

    _fechar_execucao([], run.id)

    run.refresh_from_db()
    assert run.status == RiskRun.Status.FAILED
    assert run.finished_at is not None


@pytest.mark.django_db
def test_v05c_um_modelo_pedido_e_gravado_limpo_fecha_ok() -> None:
    run = _abre(["garch_1_1"])
    _compute_asset_model(run.id, "garch_1_1")

    _fechar_execucao([None], run.id)

    run.refresh_from_db()
    _limpas(run, "garch_1_1")
    assert run.status == RiskRun.Status.OK
    assert run.finished_at is not None


# --- V-05b: a tarefa nunca levanta, e grava o par de erro ----------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("onde", ["run_experiment", "write_results"])
def test_v05b_falha_que_escapa_do_motor_ou_da_escrita_vira_o_par_de_erro(
    onde: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O erro tem de **escapar** do `run_experiment`: o que nasce dentro dele o runner ja
    isola, e a tarefa terminaria mesmo sem `try` nenhum."""

    def levanta(*args: object, **kwargs: object) -> None:
        raise ValueError("falha injetada de proposito")

    monkeypatch.setattr(f"apps.risk.tasks.{onde}", levanta)
    run = _abre(BARATOS)

    _compute_asset_model(run.id, "parametric")  # retorna: a excecao nao escapa

    assert len(_linhas(run)) == 2
    _par_de_erro(run, "parametric", "ValueError: falha injetada de proposito")


# --- idempotencia e serie mudou ------------------------------------------------------------


@pytest.mark.django_db
def test_a_mesma_tarefa_duas_vezes_grava_duas_linhas_e_nao_levanta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _abre(BARATOS)
    # A unicidade `(run, model_name, alpha)` sozinha ja impediria a linha duplicada; o que
    # so o atalho de idempotencia garante e que a repeticao NAO recalcula o modelo.
    chamadas: list[object] = []
    original = run_experiment

    def contando(*args: Any, **kwargs: Any) -> Any:
        chamadas.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr("apps.risk.tasks.run_experiment", contando)

    _compute_asset_model(run.id, "parametric")
    _compute_asset_model(run.id, "parametric")

    assert len(chamadas) == 1
    assert len(_linhas(run)) == 2
    _limpas(run, "parametric")


@pytest.mark.django_db
def test_pregao_novo_dentro_da_janela_vira_series_changed() -> None:
    run = _abre(BARATOS)
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    _preco(run.asset, SABADO_NA_JANELA, Decimal("100.000000"), coleta).save()

    _compute_asset_model(run.id, "parametric")

    _par_de_erro(
        run,
        "parametric",
        "SeriesChanged: serie mudou desde a abertura: 504 pregoes, esperados 503",
    )


@pytest.mark.django_db
def test_pregao_novo_depois_do_as_of_date_nao_entra_e_a_tarefa_calcula() -> None:
    run = _abre(BARATOS)
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    _preco(run.asset, SEGUNDA_DEPOIS, Decimal("100.000000"), coleta).save()

    _compute_asset_model(run.id, "parametric")

    _limpas(run, "parametric")


# --- o registry nas tarefas ----------------------------------------------------------------


@pytest.mark.django_db
def test_as_duas_tarefas_carregam_o_registry_antes_do_motor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Molde de `test_o_registry_e_carregado_antes_de_ser_consultado`, do M1.4: o registry
    e global de processo e ja esta populado, entao so espioes enxergam a omissao."""
    load_all_model_modules()  # populado de verdade antes de os carregadores virarem espioes
    load_all_backtest_modules()
    chamadas: list[str] = []
    monkeypatch.setattr(
        "apps.risk.tasks.load_all_model_modules",
        lambda: chamadas.append("modelos"),
    )
    monkeypatch.setattr(
        "apps.risk.tasks.load_all_backtest_modules",
        lambda: chamadas.append("backtests"),
    )

    def motor(*args: Any, **kwargs: Any) -> ExperimentResult:
        chamadas.append("motor")
        return run_experiment(*args, **kwargs)

    monkeypatch.setattr("apps.risk.tasks.run_experiment", motor)
    _serie("AAA3")

    run_id = _abrir_execucao("AAA3", INICIO.isoformat(), 42, ["parametric"])
    assert chamadas == ["modelos", "backtests"]

    chamadas.clear()
    assert run_id is not None
    _compute_asset_model(run_id, "parametric")
    assert chamadas == ["modelos", "backtests", "motor"]


# --- o leque: `enqueue_compute` e `recalcular_cobertos` ------------------------------------

DEPOIS = datetime(2026, 9, 23, 18, 30, tzinfo=UTC)
MAIS_DEPOIS = datetime(2026, 9, 23, 19, 11, tzinfo=UTC)


def _relogio(*instantes: datetime) -> Callable[[], datetime]:
    """Um `now()` que devolve os instantes na ordem, repetindo o ultimo."""
    restantes = list(instantes)

    def agora() -> datetime:
        return restantes.pop(0) if len(restantes) > 1 else restantes[0]

    return agora


def _aberturas(fila: list[Any]) -> list[tuple[Any, ...]]:
    """Os argumentos das aberturas enfileiradas; reprova se houver outra coisa na fila."""
    assert {s.task for s in fila} <= {"apps.risk.tasks.abrir_execucao"}
    return [tuple(s.args) for s in fila]


def _com_preco(ticker: str, status: str = Asset.Status.ACTIVE) -> Asset:
    """Um ativo com um preco so: candidato do ramo sem argumentos, sem serie para o piso."""
    asset = _ativo(ticker)
    Asset.objects.filter(pk=asset.pk).update(status=status)
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    _preco(asset, ULTIMO_PREGAO, Decimal("100.000000"), coleta).save()
    return asset


@pytest.mark.django_db
def test_enqueue_compute_produz_o_calculated_at_uma_vez_para_todos_os_ativos(
    fila: list[Any],
) -> None:
    """O relogio devolve um instante diferente a cada chamada: com o `now()` no lugar
    certo, os dois ativos recebem o primeiro. E quem enfileira nao cria `risk_run`."""
    _serie("AAA3")
    _serie("BBB3")

    report = enqueue_compute(["BBB3", "AAA3"], now=_relogio(DEPOIS, MAIS_DEPOIS))

    assert _aberturas(fila) == [
        ("AAA3", DEPOIS.isoformat(), config.DEFAULT_SEED, list(MODELS)),
        ("BBB3", DEPOIS.isoformat(), config.DEFAULT_SEED, list(MODELS)),
    ]
    assert (report.enqueued, report.skipped) == (["AAA3", "BBB3"], [])
    assert RiskRun.objects.count() == 0


@pytest.mark.django_db
def test_enqueue_compute_usa_o_instante_recebido_e_nao_chama_o_relogio(
    fila: list[Any],
) -> None:
    _serie("AAA3")

    def relogio_proibido() -> datetime:
        raise AssertionError("o instante recebido nao pode ser trocado pelo relogio")

    enqueue_compute(
        ["AAA3"],
        seed=7,
        models=["parametric"],
        calculated_at=DEPOIS,
        now=relogio_proibido,
    )

    assert _aberturas(fila) == [("AAA3", DEPOIS.isoformat(), 7, ["parametric"])]


@pytest.mark.django_db
def test_recalcular_cobertos_abre_um_por_ativo_ativo_com_preco_no_mesmo_instante(
    fila: list[Any],
) -> None:
    """Sem tickers: os ativos com preco. O inativo e pulado, o sem preco nem e candidato."""
    _com_preco("BBB3")
    _com_preco("AAA3")
    _com_preco("CCC3", Asset.Status.INACTIVE)
    _ativo("DDD3")  # sem preco

    _recalcular_cobertos()

    aberturas = _aberturas(fila)
    assert [a[0] for a in aberturas] == ["AAA3", "BBB3"]
    assert len({a[1] for a in aberturas}) == 1
    assert {(a[2], tuple(a[3])) for a in aberturas} == {
        (config.DEFAULT_SEED, tuple(MODELS))
    }
    assert RiskRun.objects.count() == 0


@pytest.mark.django_db
def test_recalcular_cobertos_repassa_o_instante_recebido(fila: list[Any]) -> None:
    _com_preco("AAA3")
    _com_preco("BBB3")

    _recalcular_cobertos(DEPOIS.isoformat())

    assert [a[1] for a in _aberturas(fila)] == [DEPOIS.isoformat()] * 2


# --- V-07: os dois caminhos gravam o mesmo -------------------------------------------------


def _manifesto(run: RiskRun) -> dict[str, object]:
    fora = {"id", "calculated_at", "finished_at"}
    return {
        f.name: getattr(run, f.attname)
        for f in RiskRun._meta.fields
        if f.name not in fora
    }


def _resultados(run: RiskRun) -> list[dict[str, object]]:
    return [
        {
            f.name: getattr(r, f.attname)
            for f in RiskResult._meta.fields
            if f.name not in {"id", "run"}
        }
        for r in run.results.order_by("model_name", "alpha")
    ]


@pytest.mark.django_db
def test_v07_sincrono_e_assincrono_gravam_o_mesmo_com_os_nove(fila: list[Any]) -> None:
    """Os nove modelos de verdade, redes incluidas, pelos dois caminhos sobre a mesma serie.

    O assincrono segue o que foi **enfileirado**: a abertura sai da fila do
    `enqueue_compute`, e as nove tarefas e o fecho saem do `chord` que a abertura entregou
    ao `_enqueue`. Separar os nove em nove `run_experiment` nao pode mudar numero nenhum --
    nem nas redes, em que a semeadura por `_fit_for_alpha` e o que deveria garantir isso.
    So `calculated_at` e `finished_at` podem diferir.
    """
    _serie("AAA3")

    run_compute_risk(["AAA3"], now=_relogio(INICIO, DEPOIS))
    sincrona = RiskRun.objects.get()

    enqueue_compute(["AAA3"], now=_relogio(MAIS_DEPOIS))
    (abertura,) = _aberturas(fila)
    fila.clear()
    run_id = _abrir_execucao(*abertura)
    assert run_id is not None
    (grupo,) = fila
    for tarefa in grupo.tasks:
        _compute_asset_model(*tarefa.args)
    _fechar_execucao([None] * len(grupo.tasks), *grupo.body.args)
    assincrona = RiskRun.objects.get(pk=run_id)

    assert assincrona.pk != sincrona.pk
    assert sincrona.status == RiskRun.Status.OK
    assert _manifesto(assincrona) == _manifesto(sincrona)
    resultados_sincronos = _resultados(sincrona)
    assert len(resultados_sincronos) == 18
    assert _resultados(assincrona) == resultados_sincronos
    assert assincrona.finished_at is not None
