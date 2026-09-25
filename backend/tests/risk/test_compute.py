"""`run_compute_risk` contra o banco: os nove modelos, o piso, a transacao e o veredito.

Cobre V-09 a V-14c, V-19 e V-20.

**O motor roda de verdade aqui.** O V-20 pede os **nove** modelos, redes incluidas:
dezoito linhas so saem de nove modelos x dois niveis, e trocar o `run_experiment` por um
dible que devolvesse dezoito resultados sinteticos provaria que `write_risk` grava o que
recebeu -- nao que os nove foram pedidos. Os demais criterios escolhem o conjunto mais
barato que ainda os prova: o V-19 e o V-13 nao precisam de rede, e o V-14c precisa de
**uma** so.

As series sao sinteticas e diarias, porque o piso do RF-10b e contado em pregoes: 503 e o
minimo, 502 e o caso que tem de ser pulado. Os precos saem de log-retornos
`default_rng(...).normal(0, 0.01)` acumulados a partir de 100, e o `log_return` de cada
linha e calculado **aqui**, a partir dos `adj_close` ja arredondados -- nenhum numero
deste arquivo vem do codigo sob teste.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest
from engine.backtesting import load_all_backtest_modules
from engine.backtesting.base import BacktestResult
from engine.experiments.runner import (
    ExperimentConfig,
    ExperimentResult,
    ModelRunResult,
    run_experiment,
)
from engine.models import get_model, list_models, load_all_model_modules
from engine.models.base import VaRModel

import apps.risk.compute as compute_module
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.compute import (
    MODELS,
    AssetResult,
    InvalidTickers,
    ModelsMissing,
    RiskFailed,
    RiskReport,
    close_run,
    open_run,
    run_compute_risk,
    write_failed,
    write_results,
    write_risk,
)
from apps.risk.models import RiskResult, RiskRun
from apps.risk.provider import SilverPriceProvider

pytestmark = pytest.mark.django_db

Q6 = Decimal("0.000001")
Q10 = Decimal("0.0000000001")

# Relogios fixos: `(asset, calculated_at)` e unico, entao duas execucoes no mesmo instante
# colidiriam. `FIM_1` e o `finished_at` da primeira execucao.
INICIO_1 = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
FIM_1 = datetime(2026, 9, 23, 12, 41, tzinfo=UTC)
INICIO_2 = datetime(2026, 9, 23, 18, 30, tzinfo=UTC)
FIM_2 = datetime(2026, 9, 23, 19, 11, tzinfo=UTC)

ULTIMO_PREGAO = date(2026, 9, 18)

# Os conjuntos de modelos, por custo. Os dois primeiros nao treinam rede nenhuma.
BARATOS = ["parametric", "historical"]
NAO_NEURAIS = [
    "parametric",
    "historical",
    "monte_carlo",
    "garch_1_1",
    "egarch",
    "caviar",
]
UM_NEURAL = ["lstm"]


def relogio(*instantes: datetime) -> Callable[[], datetime]:
    """Um `now()` que devolve os instantes na ordem, repetindo o ultimo."""
    restantes = list(instantes)

    def agora() -> datetime:
        return restantes.pop(0) if len(restantes) > 1 else restantes[0]

    return agora


def dias_uteis(quantidade: int, fim: date = ULTIMO_PREGAO) -> list[date]:
    """`quantidade` dias uteis consecutivos terminando em `fim`, em ordem crescente."""
    datas: list[date] = []
    dia = fim
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    return sorted(datas)


def precos(quantidade: int, *, semente: int = 7) -> list[Decimal]:
    """Precos com log-retornos normais de desvio 1%, a partir de 100."""
    rng = np.random.default_rng(semente)
    nivel = 100.0
    valores = [Decimal("100.000000")]
    for retorno in rng.normal(0, 0.01, quantidade - 1):
        nivel *= math.exp(float(retorno))
        valores.append(Decimal(str(nivel)).quantize(Q6))
    return valores


def collection_run() -> CollectionRun:
    return CollectionRun.objects.create(source="teste", started_at=INICIO_1)


def cria_ativo(ticker: str, *, status: str = Asset.Status.ACTIVE) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=INICIO_1,
        updated_at=INICIO_1,
    )


def cria_serie(
    asset: Asset,
    quantidade: int,
    *,
    semente: int = 7,
    run: CollectionRun | None = None,
    run_da_ultima: CollectionRun | None = None,
) -> list[Price]:
    """`quantidade` pregoes do ativo. `run_da_ultima` desloca so a linha de maior data."""
    datas = dias_uteis(quantidade)
    valores = precos(quantidade, semente=semente)
    coleta = run or collection_run()
    linhas = []
    anterior: Decimal | None = None
    for i, (dia, adj) in enumerate(zip(datas, valores, strict=True)):
        log_return = (
            None
            if anterior is None
            else Decimal(str(math.log(float(adj) / float(anterior)))).quantize(Q10)
        )
        anterior = adj
        ultima = i == quantidade - 1
        linhas.append(
            Price(
                asset=asset,
                date=dia,
                open=adj,
                high=adj,
                low=adj,
                close=adj,
                adj_close=adj,
                volume=1000,
                log_return=log_return,
                run=run_da_ultima if (ultima and run_da_ultima) else coleta,
                updated_at=INICIO_1,
            )
        )
    return Price.objects.bulk_create(linhas)


def com_serie(ticker: str, quantidade: int = config.MIN_SESSIONS) -> Asset:
    asset = cria_ativo(ticker)
    cria_serie(asset, quantidade)
    return asset


def resultado(report: RiskReport, ticker: str) -> AssetResult:
    return next(r for r in report.results if r.ticker == ticker)


# --- V-20: os nove modelos, dezoito resultados e a janela de 252 ------------------------


def test_v20_os_nove_modelos_dao_dezoito_resultados_com_a_janela_de_252() -> None:
    """V-20 e V-14b: os nove sao pedidos de verdade, e o manifesto de cada um nao e vazio.

    Os dois criterios andam juntos **na mesma execucao** de proposito: treinar as tres
    redes custa ~1 min, e reexecuta-las so para reler a coluna `hyperparameters` dobraria
    o custo sem provar nada a mais.
    """
    com_serie("AAA3")

    report = run_compute_risk(["AAA3"], now=relogio(INICIO_1, FIM_1))

    run = RiskRun.objects.get()
    assert run.train_window_days == config.TRAIN_WINDOW_DAYS == 252
    assert run.price_count == config.MIN_SESSIONS
    assert run.train_count == 252
    # P precos dao P-1 retornos; o que sobra depois do treino e o teste.
    assert run.test_count == config.MIN_SESSIONS - 1 - 252 == 250

    results = list(run.results.all())
    assert len(results) == 18
    assert {r.model_name for r in results} == set(MODELS)
    assert sorted({str(r.alpha) for r in results}) == ["0.0100", "0.0500"]
    assert resultado(report, "AAA3").results == 18

    # V-14b: `hyperparameters` nao nasce vazio. Os pares vem da lista fechada da spec; os
    # dois `{}` sao os que o codigo do motor de fato nao tem parametro configuravel.
    por_modelo = {r.model_name: r.hyperparameters for r in results}
    assert por_modelo["monte_carlo"] == {"n_simulations": 100000, "random_state": 42}
    assert por_modelo["caviar"] == {"refit_frequency_days": 252, "n_restarts": 10}
    assert por_modelo["garch_1_1"] == {
        "dist": "normal",
        "refit_frequency_days": 252,
        "vol": "GARCH",
        "p": 1,
        "q": 1,
    }
    for neural in ("garchnet", "lstm", "gru"):
        assert set(por_modelo[neural]) == {
            "window",
            "refit_frequency_days",
            "grid",
            "learning_rate",
            "batch_size",
            "search_epochs",
            "refit_epochs",
            "patience",
            "val_fraction",
        }
    assert por_modelo["parametric"] == {}
    assert por_modelo["historical"] == {}
    # e a categoria vem do registry, nao de uma tabela paralela
    assert {r.model_name: r.model_category for r in results}["egarch"] == "garch"


def test_o_registry_e_carregado_antes_de_ser_consultado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sem as duas chamadas, `list_models()` sai vazia e toda execucao levanta
    `ModelsMissing` com os nove. Aqui os carregadores sao espionados, nao desligados: o
    registry ja esta populado no processo, e o que se prova e que o caminho os chama."""
    load_all_model_modules()  # populado de verdade antes de os carregadores virarem espioes
    load_all_backtest_modules()
    chamadas: list[str] = []
    monkeypatch.setattr(
        "apps.risk.compute.load_all_model_modules",
        lambda: chamadas.append("modelos"),
    )
    monkeypatch.setattr(
        "apps.risk.compute.load_all_backtest_modules",
        lambda: chamadas.append("backtests"),
    )

    run_compute_risk([], models=BARATOS, now=relogio(INICIO_1))

    assert chamadas == ["modelos", "backtests"]


def test_a_lista_de_nove_e_a_mesma_que_o_registry_completo_oferece() -> None:
    """O padrao e literal (RF-17); este teste impede que ele envelheca calado."""
    load_all_model_modules()
    assert sorted(MODELS) == list_models()
    assert len(MODELS) == 9


# --- V-19: o piso de 503 pregoes --------------------------------------------------------


def test_v19_com_502_pregoes_o_ativo_e_pulado_e_nao_grava_linha_nenhuma() -> None:
    com_serie("AAA3", 502)

    report = run_compute_risk(
        ["AAA3"], models=NAO_NEURAIS, now=relogio(INICIO_1, FIM_1)
    )

    linha = resultado(report, "AAA3")
    assert linha.skipped is True
    assert linha.reason == "serie curta (minimo 503)"
    assert linha.price_count == 502
    assert RiskRun.objects.count() == 0
    assert RiskResult.objects.count() == 0


def test_v19_com_503_pregoes_o_ativo_e_calculado_e_a_basileia_roda() -> None:
    com_serie("AAA3", 503)

    report = run_compute_risk(
        ["AAA3"], models=NAO_NEURAIS, now=relogio(INICIO_1, FIM_1)
    )

    assert resultado(report, "AAA3").skipped is False
    run = RiskRun.objects.get()
    results = list(run.results.all())
    assert len(results) == len(NAO_NEURAIS) * 2
    # A Basileia exige 250 observacoes de teste e levanta abaixo disso: zona preenchida em
    # todos os resultados e a prova de que o piso esta no lugar certo.
    assert all(r.error == "" for r in results)
    assert all(r.basel_zone in ("verde", "amarela", "vermelha") for r in results)


def test_ativo_sem_preco_nenhum_cai_no_piso_e_e_pulado() -> None:
    cria_ativo("XPTO3")

    report = run_compute_risk(["XPTO3"], models=BARATOS, now=relogio(INICIO_1))

    linha = resultado(report, "XPTO3")
    assert (linha.skipped, linha.price_count, linha.as_of_date) == (True, 0, None)
    assert RiskRun.objects.count() == 0


def test_o_piso_conta_a_serie_depois_da_limpeza_nao_a_do_banco() -> None:
    """504 linhas no banco, duas com `adj_close` zerado: 502 chegam ao motor, e pula."""
    asset = cria_ativo("AAA3")
    linhas = cria_serie(asset, 504)
    for linha in linhas[10:12]:
        linha.adj_close = Decimal("0.000000")
        linha.save(update_fields=["adj_close"])

    report = run_compute_risk(
        ["AAA3"], models=NAO_NEURAIS, now=relogio(INICIO_1, FIM_1)
    )

    assert Price.objects.filter(asset=asset).count() == 504
    linha_relatorio = resultado(report, "AAA3")
    assert linha_relatorio.skipped is True
    assert linha_relatorio.price_count == 502
    assert RiskRun.objects.count() == 0


# --- V-14: o manifesto -------------------------------------------------------------------


def test_v14_o_manifesto_esta_completo_e_o_price_run_e_o_maior_da_janela() -> None:
    """V-14, com **coletas divergentes**.

    A linha de maior data vem de uma coleta **anterior** a mais recente que tocou a
    janela. Sem isso "o maior `run`" e "o `run` da linha de maior data" seriam o mesmo
    numero e o criterio passaria vazio.
    """
    antiga = collection_run()
    recente = collection_run()
    assert antiga.pk < recente.pk
    asset = cria_ativo("AAA3")
    cria_serie(asset, 503, run=recente, run_da_ultima=antiga)

    run_compute_risk(["AAA3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    run = RiskRun.objects.get()
    assert run.asset_id == asset.pk
    assert run.calculated_at == INICIO_1
    assert run.finished_at == FIM_1
    assert run.engine_version == "0.2.0"
    assert run.seed == config.DEFAULT_SEED == 42
    assert run.train_window_days == 252
    assert run.as_of_date == ULTIMO_PREGAO
    assert run.first_price_date == dias_uteis(503)[0]
    assert run.price_count == 503
    assert run.train_count == 252
    assert run.test_count == 250
    assert run.requested_by_id is None
    # a coleta da linha de maior data e a `antiga`; o manifesto guarda a `recente`
    ultima = Price.objects.filter(asset=asset).order_by("-date").first()
    assert ultima is not None and ultima.run_id == antiga.pk
    assert run.price_run_id == recente.pk


def test_v14_nenhuma_coluna_nao_anulavel_do_manifesto_fica_sem_valor() -> None:
    com_serie("AAA3")

    run_compute_risk(["AAA3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    run = RiskRun.objects.get()
    obrigatorias = (
        "asset_id",
        "calculated_at",
        "engine_version",
        "seed",
        "train_window_days",
        "as_of_date",
        "first_price_date",
        "price_count",
        "train_count",
        "test_count",
        "price_run_id",
    )
    vazias = [c for c in obrigatorias if getattr(run, c) is None]
    assert vazias == []
    assert run.finished_at is not None  # a execucao terminou


# --- V-14c: a semente e a que foi usada --------------------------------------------------


def test_v14c_sementes_diferentes_gravam_valores_diferentes_e_mudam_o_var() -> None:
    """V-14c: a cadeia `--seed` -> `configure` -> `apply` inteira, com **um** neural."""
    com_serie("AAA3")

    run_compute_risk(["AAA3"], seed=7, models=UM_NEURAL, now=relogio(INICIO_1, FIM_1))
    run_compute_risk(["AAA3"], seed=99, models=UM_NEURAL, now=relogio(INICIO_2, FIM_2))

    primeira, segunda = RiskRun.objects.order_by("calculated_at")
    assert (primeira.seed, segunda.seed) == (7, 99)
    var_1 = {(r.model_name, str(r.alpha)): r.var_latest for r in primeira.results.all()}
    var_2 = {(r.model_name, str(r.alpha)): r.var_latest for r in segunda.results.all()}
    assert set(var_1) == set(var_2) and len(var_1) == 2
    assert all(v is not None for v in var_1.values())
    assert var_1 != var_2, "a semente nao chegou ao modelo: o VaR nao mudou"


# --- V-09: recalcular nao altera a execucao anterior -------------------------------------


def test_v09_duas_execucoes_dao_duas_linhas_e_a_primeira_fica_intacta() -> None:
    com_serie("AAA3")

    run_compute_risk(["AAA3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))
    antes = _campos(RiskRun.objects.get())
    resultados_antes = _resultados(RiskRun.objects.get())

    run_compute_risk(["AAA3"], seed=99, models=BARATOS, now=relogio(INICIO_2, FIM_2))

    assert RiskRun.objects.count() == 2
    assert RiskResult.objects.count() == 8
    primeira = RiskRun.objects.get(calculated_at=INICIO_1)
    assert _campos(primeira) == antes
    assert _resultados(primeira) == resultados_antes
    assert RiskRun.objects.get(calculated_at=INICIO_2).seed == 99


def _campos(run: RiskRun) -> dict[str, object]:
    return {f.name: getattr(run, f.attname) for f in RiskRun._meta.fields}


def _resultados(run: RiskRun) -> list[dict[str, object]]:
    return [
        {
            f.name: getattr(r, f.attname)
            for f in RiskResult._meta.fields
            if f.name != "id"
        }
        for r in run.results.order_by("model_name", "alpha")
    ]


def test_o_calculated_at_e_o_mesmo_para_os_dois_ativos_da_execucao() -> None:
    """Contrato de `run_compute_risk`: `calculated_at` e o `now()` de **uma** chamada, e e
    o que faz "uma execucao" ser identificavel em `gold.risk_run`.

    Sem esta comparacao ENTRE ativos, mover o `now()` para dentro do laco passaria a suite
    inteira — e uma execucao multi-ativo deixaria de ser agrupavel. O relogio devolve
    `INICIO_1` na primeira chamada e `FIM_1` nas seguintes: com o `now()` no lugar certo,
    os dois ativos nascem em `INICIO_1`.
    """
    com_serie("AAA3")
    com_serie("BBB3")

    run_compute_risk(["AAA3", "BBB3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    runs = list(RiskRun.objects.order_by("asset__ticker"))
    assert [r.asset.ticker for r in runs] == ["AAA3", "BBB3"]
    assert {r.calculated_at for r in runs} == {INICIO_1}


# --- V-10: uma transacao por ativo -------------------------------------------------------


def test_v10_escrita_que_levanta_no_segundo_ativo_reverte_so_ele(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for ticker in ("AAA3", "BBB3", "CCC3"):
        com_serie(ticker)
    vistos: list[str] = []

    def fake_write(
        asset: Asset,
        calculated_at: datetime,
        finished_at: datetime,
        seed: int,
        bars: list[Price],
        result: ExperimentResult,
    ) -> RiskRun:
        vistos.append(asset.ticker)
        run = write_risk(asset, calculated_at, finished_at, seed, bars, result)
        if asset.ticker == "BBB3":
            # grava a execucao e os resultados e so entao levanta: sem isso nao haveria o
            # que reverter, e o teste passaria verde com a transacao no lugar errado.
            raise RuntimeError("gravacao quebrou depois da execucao e dos resultados")
        return run

    monkeypatch.setattr("apps.risk.compute.write_risk", fake_write)
    assert compute_module.write_risk is fake_write

    with pytest.raises(RiskFailed) as info:
        run_compute_risk(
            ["AAA3", "BBB3", "CCC3"],
            models=BARATOS,
            now=relogio(INICIO_1, FIM_1),
        )

    report = info.value.report
    assert vistos == ["AAA3", "BBB3", "CCC3"]
    assert resultado(report, "BBB3").error == (
        "RuntimeError: gravacao quebrou depois da execucao e dos resultados"
    )
    assert resultado(report, "AAA3").error is None
    assert resultado(report, "CCC3").error is None
    assert set(RiskRun.objects.values_list("asset__ticker", flat=True)) == {
        "AAA3",
        "CCC3",
    }
    assert RiskResult.objects.count() == 8


# --- V-11 e V-12: falha de um modelo -----------------------------------------------------


def test_v11_falha_de_um_modelo_nao_derruba_os_outros(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A falha e injetada no `get_model` **do runner**, nao no de `compute`.

    E o que reproduz o isolamento real: o modelo nao ajusta, e ainda assim a linha dele
    guarda `model_category` e `hyperparameters`, que saem do registry.
    """
    original = get_model

    def quebrado(nome: str) -> type[VaRModel]:
        if nome == "historical":
            raise RuntimeError("modelo quebrado de proposito")
        return original(nome)

    monkeypatch.setattr("engine.experiments.runner.get_model", quebrado)
    com_serie("AAA3")

    run_compute_risk(["AAA3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    results = {(r.model_name, str(r.alpha)): r for r in RiskResult.objects.all()}
    assert len(results) == 4
    for alpha in ("0.0500", "0.0100"):
        falho = results[("historical", alpha)]
        assert falho.error == "modelo quebrado de proposito"
        assert falho.model_category == "traditional"
        # V-12: `error` preenchido => numeros nulos e veredito nulo
        assert falho.var_latest is None
        assert falho.var_mean is None
        assert falho.violations is None
        assert falho.expected_violations is None
        assert falho.kupiec_passed is None
        assert falho.kupiec_p_value is None
        assert falho.christoffersen_passed is None
        assert falho.christoffersen_p_value is None
        assert falho.dq_passed is None
        assert falho.dq_p_value is None
        assert falho.basel_zone is None
        assert falho.adequate is None

        intacto = results[("parametric", alpha)]
        assert intacto.error == ""
        assert intacto.var_latest is not None
        assert intacto.adequate is not None


def test_o_relatorio_conta_os_resultados_falhos_do_ativo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = get_model

    def quebrado(nome: str) -> type[VaRModel]:
        if nome == "historical":
            raise RuntimeError("modelo quebrado de proposito")
        return original(nome)

    monkeypatch.setattr("engine.experiments.runner.get_model", quebrado)
    com_serie("AAA3")

    report = run_compute_risk(["AAA3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    linha = resultado(report, "AAA3")
    assert (linha.results, linha.failed, linha.error) == (4, 2, None)


# --- RF-08: o sincrono grava o estado ------------------------------------------------------


def test_o_sincrono_grava_ok_numa_execucao_limpa() -> None:
    """O guarda que o `CharField` sem padrao nao da: esquecer o `status` grava `""`."""
    com_serie("AAA3")

    run_compute_risk(["AAA3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    run = RiskRun.objects.get()
    assert (run.status, run.requested_models) == (RiskRun.Status.OK, BARATOS)


def test_o_sincrono_grava_partial_quando_um_dos_modelos_falha(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Molde do V-11: a falha no `get_model` do runner, para um dos dois modelos."""
    original = get_model

    def quebrado(nome: str) -> type[VaRModel]:
        if nome == "historical":
            raise RuntimeError("modelo quebrado de proposito")
        return original(nome)

    monkeypatch.setattr("engine.experiments.runner.get_model", quebrado)
    com_serie("AAA3")

    run_compute_risk(["AAA3"], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    run = RiskRun.objects.get()
    assert run.results.exclude(error="").count() == 2
    assert (run.status, run.requested_models) == (RiskRun.Status.PARTIAL, BARATOS)


# --- M1.5: os pedacos que as tarefas usam -------------------------------------------------


def _abre(models: list[str]) -> tuple[RiskRun, list[Price]]:
    """Uma execucao aberta sobre `AAA3`, com o registry carregado (nao ha `run_compute_risk`
    no caminho) e as linhas que o motor vera."""
    load_all_model_modules()
    load_all_backtest_modules()
    asset = com_serie("AAA3")
    bars = list(Price.objects.filter(asset=asset).order_by("date"))
    return open_run(asset, INICIO_1, 42, bars, models), bars


def _calcula(run: RiskRun, bars: list[Price], models: list[str]) -> ExperimentResult:
    """O motor de verdade, com os modelos pedidos, sobre a janela da execucao."""
    return run_experiment(
        ExperimentConfig(
            ticker=run.asset.ticker,
            start=bars[0].date.isoformat(),
            end=bars[-1].date.isoformat(),
            model_names=models,
            backtest_names=list(config.BACKTESTS),
            alphas=list(config.ALPHAS),
            train_window_days=config.TRAIN_WINDOW_DAYS,
            seed=run.seed,
        ),
        SilverPriceProvider(),
    )


def test_open_run_cria_running_sem_finished_at_e_com_o_manifesto() -> None:
    run, bars = _abre(BARATOS)

    run.refresh_from_db()
    assert run.status == RiskRun.Status.RUNNING
    assert run.finished_at is None
    assert run.requested_models == BARATOS
    assert run.results.count() == 0
    # o manifesto e o mesmo que o sincrono monta
    assert run.calculated_at == INICIO_1
    assert run.engine_version == "0.2.0"
    assert run.seed == 42
    assert (run.train_window_days, run.train_count, run.test_count) == (252, 252, 250)
    assert (run.first_price_date, run.as_of_date) == (bars[0].date, bars[-1].date)
    assert run.price_count == 503
    assert run.price_run_id == max(b.run_id for b in bars)
    assert run.requested_by_id is None


def test_write_failed_grava_as_duas_linhas_com_numeros_nulos_e_o_registry() -> None:
    run, _ = _abre(["historical"])

    write_failed(run, "historical", "RuntimeError: quebrou de proposito")

    linhas = {str(r.alpha): r for r in RiskResult.objects.filter(run=run)}
    assert sorted(linhas) == ["0.0100", "0.0500"]
    for linha in linhas.values():
        assert linha.model_name == "historical"
        assert linha.error == "RuntimeError: quebrou de proposito"
        assert linha.model_category == "traditional"
        assert linha.hyperparameters == get_model("historical")().hyperparameters
        assert linha.var_latest is None
        assert linha.var_mean is None
        assert linha.violations is None
        assert linha.expected_violations is None
        assert linha.kupiec_passed is None
        assert linha.kupiec_p_value is None
        assert linha.christoffersen_passed is None
        assert linha.christoffersen_p_value is None
        assert linha.dq_passed is None
        assert linha.dq_p_value is None
        assert linha.basel_zone is None
        assert linha.adequate is None


def test_close_run_escreve_ok_e_o_instante_quando_tudo_foi_gravado() -> None:
    run, bars = _abre(BARATOS)
    write_results(run, _calcula(run, bars, BARATOS))

    assert close_run(run, FIM_1) == RiskRun.Status.OK

    run.refresh_from_db()
    assert (run.status, run.finished_at) == (RiskRun.Status.OK, FIM_1)
    assert run.results.count() == 4
    assert run.results.exclude(error="").count() == 0


def test_close_run_escreve_partial_com_um_modelo_falho() -> None:
    run, bars = _abre(BARATOS)
    write_results(run, _calcula(run, bars, ["parametric"]))
    write_failed(run, "historical", "RuntimeError: quebrou de proposito")

    assert close_run(run, FIM_1) == RiskRun.Status.PARTIAL

    run.refresh_from_db()
    assert (run.status, run.finished_at) == (RiskRun.Status.PARTIAL, FIM_1)


def test_close_run_escreve_partial_quando_falta_modelo_pedido() -> None:
    """Relativo ao que foi **pedido**: dois pedidos, um so gravado, nenhum erro."""
    run, bars = _abre(BARATOS)
    write_results(run, _calcula(run, bars, ["parametric"]))

    assert close_run(run, FIM_1) == RiskRun.Status.PARTIAL


def test_close_run_escreve_failed_sem_nada_gravado_e_com_tudo_falho() -> None:
    vazio, _ = _abre(BARATOS)
    assert close_run(vazio, FIM_1) == RiskRun.Status.FAILED
    vazio.refresh_from_db()
    assert (vazio.status, vazio.finished_at) == (RiskRun.Status.FAILED, FIM_1)

    asset = vazio.asset
    bars = list(Price.objects.filter(asset=asset).order_by("date"))
    falho = open_run(asset, INICIO_2, 42, bars, BARATOS)
    for nome in BARATOS:
        write_failed(falho, nome, "RuntimeError: quebrou de proposito")
    assert close_run(falho, FIM_2) == RiskRun.Status.FAILED
    falho.refresh_from_db()
    assert (falho.status, falho.finished_at) == (RiskRun.Status.FAILED, FIM_2)


def test_close_run_com_um_modelo_pedido_espera_um_por_nivel() -> None:
    """Um modelo so pedido e uma execucao completa: o esperado e um por nivel, nao nove."""
    run, bars = _abre(["parametric"])
    write_results(run, _calcula(run, bars, ["parametric"]))

    assert close_run(run, FIM_1) == RiskRun.Status.OK


# --- V-13: o veredito e exatamente Kupiec E Christoffersen -------------------------------


def backtest(nome: str, passou: bool) -> BacktestResult:
    """Um `BacktestResult` de fachada, com os `details` que a coluna correspondente le."""
    details: dict[str, object] = {}
    if nome == "kupiec":
        details = {"violations": 12, "expected": 12.5, "n_obs": 250}
    if nome == "basileia":
        details = {"zone": "verde" if passou else "vermelha"}
    return BacktestResult(
        test_name=nome, statistic=1.0, p_value=0.5, passed=passou, details=details
    )


def resultado_do_modelo(
    modelo: str,
    alpha: float,
    kupiec: bool,
    christoffersen: bool,
    dq: bool,
    basileia: bool,
) -> ModelRunResult:
    return ModelRunResult(
        model_name=modelo,
        alpha=alpha,
        backtests=[
            backtest("kupiec", kupiec),
            backtest("christoffersen", christoffersen),
            backtest("dq", dq),
            backtest("basileia", basileia),
        ],
        estimate=None,
    )


def test_v13_o_veredito_e_o_e_logico_dos_dois_e_ignora_dq_e_basileia() -> None:
    """Os quatro cruzamentos, com DQ e Basileia **discordando** do veredito.

    O `ExperimentResult` e montado a mao: e o unico jeito de forcar as quatro combinacoes
    de Kupiec x Christoffersen, que nenhuma serie produz sob encomenda. Como nao ha
    `run_compute_risk` no caminho, o registry e carregado aqui: `write_risk` le a
    categoria e os hiperparametros de cada modelo por `get_model`.
    """
    load_all_model_modules()
    asset = cria_ativo("AAA3")
    bars = cria_serie(asset, 503)
    # (modelo, alpha, kupiec, christoffersen) -> (dq, basileia) sempre contrarios ao par
    cruzamentos = [
        ("parametric", 0.05, True, True),
        ("parametric", 0.01, True, False),
        ("historical", 0.05, False, True),
        ("historical", 0.01, False, False),
    ]
    runs = [
        resultado_do_modelo(
            modelo,
            alpha,
            kupiec,
            christoffersen,
            dq=not (kupiec and christoffersen),
            basileia=not (kupiec and christoffersen),
        )
        for modelo, alpha, kupiec, christoffersen in cruzamentos
    ]
    experiment = ExperimentConfig(
        ticker="AAA3",
        start=bars[0].date.isoformat(),
        end=bars[-1].date.isoformat(),
        model_names=["parametric", "historical"],
        backtest_names=list(config.BACKTESTS),
    )

    write_risk(asset, INICIO_1, FIM_1, 42, bars, ExperimentResult(experiment, runs))

    veredito = {
        (r.model_name, str(r.alpha)): (
            r.adequate,
            r.kupiec_passed,
            r.christoffersen_passed,
            r.dq_passed,
            r.basel_zone,
        )
        for r in RiskResult.objects.all()
    }
    assert veredito[("parametric", "0.0500")] == (True, True, True, False, "vermelha")
    assert veredito[("parametric", "0.0100")] == (False, True, False, True, "verde")
    assert veredito[("historical", "0.0500")] == (False, False, True, True, "verde")
    assert veredito[("historical", "0.0100")] == (False, False, False, True, "verde")


def test_as_violacoes_gravadas_sao_as_do_kupiec() -> None:
    load_all_model_modules()  # `write_risk` consulta o registry, e aqui nao ha runner
    asset = cria_ativo("AAA3")
    bars = cria_serie(asset, 503)
    modelo = resultado_do_modelo("parametric", 0.05, True, True, True, True)
    # a Basileia conta outra janela e traz outro par: o que vai para a coluna e o do Kupiec
    modelo.backtests[3].details["violations"] = 999
    modelo.backtests[3].details["expected"] = 999.0
    experiment = ExperimentConfig(
        ticker="AAA3",
        start=bars[0].date.isoformat(),
        end=bars[-1].date.isoformat(),
        model_names=["parametric"],
        backtest_names=list(config.BACKTESTS),
    )

    write_risk(asset, INICIO_1, FIM_1, 42, bars, ExperimentResult(experiment, [modelo]))

    linha = RiskResult.objects.get()
    assert linha.violations == 12
    assert linha.expected_violations == Decimal("12.500000")


# --- RF-17 e RF-18: o que aborta antes de escrever ----------------------------------------


def test_modelo_fora_do_registry_falha_alto_e_nao_grava_nada() -> None:
    com_serie("AAA3")

    with pytest.raises(ModelsMissing) as info:
        run_compute_risk(["AAA3"], models=["parametric", "inexistente"])

    assert info.value.models == ["inexistente"]
    assert RiskRun.objects.count() == 0


def test_v16_ticker_inexistente_aborta_antes_de_qualquer_escrita() -> None:
    com_serie("AAA3")

    with pytest.raises(InvalidTickers) as info:
        run_compute_risk(["AAA3", "ZZZZ9"], models=BARATOS)

    assert info.value.tickers == ["ZZZZ9"]
    assert RiskRun.objects.count() == 0
    assert RiskResult.objects.count() == 0


def test_v16_ticker_inativo_tambem_aborta_e_nao_escreve() -> None:
    com_serie("AAA3")
    inativo = cria_ativo("BBB3", status=Asset.Status.INACTIVE)
    cria_serie(inativo, 503)

    with pytest.raises(InvalidTickers) as info:
        run_compute_risk(["AAA3", "BBB3"], models=BARATOS)

    assert info.value.tickers == ["BBB3"]
    assert RiskRun.objects.count() == 0


def test_v17_sem_argumentos_processa_ativo_pula_inativo_e_ignora_sem_preco() -> None:
    com_serie("AAA3")
    inativo = cria_ativo("BBB3", status=Asset.Status.INACTIVE)
    cria_serie(inativo, 503)
    cria_ativo("CCC3")  # sem preco: nem candidato

    report = run_compute_risk([], models=BARATOS, now=relogio(INICIO_1, FIM_1))

    assert [r.ticker for r in report.results] == ["AAA3", "BBB3"]
    assert resultado(report, "BBB3").reason == "inativo"
    assert set(RiskRun.objects.values_list("asset__ticker", flat=True)) == {"AAA3"}


def test_sem_argumentos_e_sem_candidato_pede_tickers() -> None:
    cria_ativo("AAA3")

    report = run_compute_risk([], models=BARATOS, now=relogio(INICIO_1))

    assert report.results == []
    assert report.render() == "nenhum ativo ativo com preco; informe tickers"


# --- o relatorio --------------------------------------------------------------------------


def test_o_relatorio_tem_o_formato_do_plano() -> None:
    results = [
        AssetResult("PETR4", 2489, date(2026, 9, 18), 18, 7, 0, 41.2, None, False),
        AssetResult("BAZZ4", 0, None, 0, 0, 0, None, None, True, "inativo"),
        AssetResult(
            "XPTO3",
            480,
            date(2026, 9, 18),
            0,
            0,
            0,
            None,
            None,
            True,
            "serie curta (minimo 503)",
        ),
    ]

    assert RiskReport(results, 164.8).render().splitlines() == [
        "PETR4           2489 pregoes  ate 2026-09-18  18 resultados, 7 adequados, "
        "0 falhos  41.2s",
        "BAZZ4              0 pregoes  -               pulado: inativo",
        "XPTO3            480 pregoes  ate 2026-09-18  pulado: serie curta (minimo 503)",
        "risco: 3 ativos, 1 ok, 0 falhos, 2 pulados, 164.8s",
    ]


def test_o_resumo_conta_os_pulados_no_total_e_os_falhos_a_parte() -> None:
    results = [
        AssetResult("AAA3", 503, date(2026, 9, 18), 4, 2, 0, 1.0, None, False),
        AssetResult(
            "BBB3", 503, date(2026, 9, 18), 0, 0, 0, 1.0, "RuntimeError: x", False
        ),
        AssetResult("CCC3", 0, None, 0, 0, 0, None, None, True, "inativo"),
    ]

    linhas = RiskReport(results, 3.0).render().splitlines()

    assert linhas[1].endswith("FALHOU (RuntimeError: x)")
    assert linhas[-1] == "risco: 3 ativos, 1 ok, 1 falhos, 1 pulados, 3.0s"
