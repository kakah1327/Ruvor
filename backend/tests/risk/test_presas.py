"""A execucao presa (M1.5c): V-01 a V-07, V-11 e V-15.

**O V-05 e o V-06 semeiam a execucao direto no banco**, sem o motor: o que eles medem e o
`close_run` condicional (D-150) e o fecho que respeita quem fechou antes (RF-09) -- a regra do
fecho so conta linhas, e dois resultados sem erro de dois modelos pedidos bastam para `partial`.

**O V-15 roda em subprocesso** porque as settings sao avaliadas uma vez por processo: trocar a
variavel de ambiente dentro da sessao do pytest nao reavaliaria `RUVOR_RISK_STALE_AFTER` nem a
validacao dele. O ambiente do subprocesso e sempre uma **copia** do deste; o padrao e medido com
`RUVOR_RISK_STALE_AFTER_MIN` removida da copia, porque o conteiner a recebe do compose.

**O V-07 fecha a execucao durante o calculo**, de dentro do `run_models` substituido, antes de
ele devolver ou levantar: a tarefa ja leu a linha `running` no comeco, entao so a releitura
depois da trava, em `_write_if_running`, a ve fechada (RF-10, D-150). A execucao e aberta por
`open_run` sobre uma serie de `MIN_SESSIONS` pregoes, para a tarefa passar da conferencia da
janela (`SeriesChanged`) e chegar ao `run_models`. Os duplos entram em `apps.risk.tasks.*`, o
nome global que a tarefa chama.

**Os V-01 a V-04b chamam `close_stale_runs` com o relogio controlado**: `now` fixo (`AGORA`) e o
prazo de seis horas passados a funcao, sem ler a configuracao. As execucoes sao abertas por
`open_run` com os dois modelos baratos e `calculated_at` relativo a `AGORA`, e os resultados
limpos sao os do motor de verdade, gravados por `write_results`, no molde de
`tests/risk/test_compute.py` (`_abre`, `_calcula`). **A spec escreve 18 e 6 para os nove
modelos; aqui sao 4 e 2**, porque a regra e relativa ao pedido -- o V-01b a prova com um modelo
so. A unicidade `risk_run_asset_calculated_at` barra duas execucoes do mesmo ativo no mesmo
instante: cada presa do mesmo ativo nasce a `AGORA - 7 h - i s`. O V-03 usa um ativo por
cenario, porque `compute_request_one_open_per_asset` so deixa um pedido aberto por ativo. Os
duplos entram em `apps.risk.stale.*`, o nome global que a varredura chama; o V-04b fecha a
execucao entre a listagem e a trava, pelo `_after_stale_listing`, e e o caso que so a releitura
depois da trava pega com `dry_run`.

**O V-11 substitui `apps.risk.tasks.close_stale_runs`**, o nome global que a tarefa
`_fechar_presas` chama, por um que levanta: a tarefa termina normalmente e so registra no log
(RF-06), para que a corrente da `rotina_diaria` siga para a coleta. Nenhum teste enfileira a
rotina de verdade -- a corrente e conferida em `tests/risk/test_beat.py` (V-10).
"""

from __future__ import annotations

import logging
import math
import os
import random
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, ExperimentResult, run_experiment
from engine.models import load_all_model_modules
from pytest_django import Settings

from apps.api.models import ComputeRequest
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.compute import (
    _bars,
    close_run,
    open_run,
    write_failed,
    write_results,
)
from apps.risk.models import RiskResult, RiskRun
from apps.risk.provider import SilverPriceProvider
from apps.risk.stale import StaleReport, close_stale_runs
from apps.risk.tasks import _compute_asset_model, _fechar_execucao, _fechar_presas

# O diretorio de `backend/`, onde `config` e `apps` sao importaveis.
_BACKEND_DIR = Path(__file__).resolve().parents[2]

_SCRIPT = """
import django

django.setup()

from django.conf import settings

print(settings.RUVOR_RISK_STALE_AFTER.total_seconds())
"""


def _settings_em_subprocesso(
    stale_after_min: str | None, on_demand_timeout_min: str
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings_test",
        "RUVOR_ON_DEMAND_TIMEOUT_MIN": on_demand_timeout_min,
    }
    if stale_after_min is None:
        env.pop("RUVOR_RISK_STALE_AFTER_MIN", None)
    else:
        env["RUVOR_RISK_STALE_AFTER_MIN"] = stale_after_min
    return subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


# --- V-15: o prazo e configuracao, e nao pode ser menor que o do pedido sob demanda ---------


def test_prazo_padrao_e_de_seis_horas_sem_a_variavel() -> None:
    proc = _settings_em_subprocesso(None, "30")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "21600.0"


def test_prazo_menor_que_o_do_pedido_sob_demanda_derruba_a_carga() -> None:
    proc = _settings_em_subprocesso("20", "30")
    assert proc.returncode != 0
    assert "RUVOR_RISK_STALE_AFTER_MIN" in proc.stderr
    assert "RUVOR_ON_DEMAND_TIMEOUT_MIN" in proc.stderr


def test_prazo_igual_ao_do_pedido_sob_demanda_e_aceito() -> None:
    proc = _settings_em_subprocesso("30", "30")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "1800.0"


# --- os dados de V-05 e V-06 ---------------------------------------------------------------

BARATOS = ["parametric", "historical"]
INICIO = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
FIM_A = datetime(2026, 9, 23, 12, 41, tzinfo=UTC)
FIM_B = datetime(2026, 9, 23, 18, 30, tzinfo=UTC)


def _ativo(ticker: str) -> Asset:
    agora = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )


def _execucao(status: str, finished_at: datetime | None) -> RiskRun:
    """Uma execucao de `AAA3` semeada direto no banco, sem resultado nenhum."""
    coleta = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    return RiskRun.objects.create(
        asset=_ativo("AAA3"),
        calculated_at=INICIO,
        finished_at=finished_at,
        engine_version="0.3.0",
        seed=42,
        train_window_days=252,
        as_of_date=date(2026, 9, 18),
        first_price_date=date(2024, 9, 18),
        price_count=503,
        train_count=252,
        test_count=250,
        price_run=coleta,
        requested_by=None,
        status=status,
        requested_models=list(BARATOS),
        full_recompute=False,
    )


def _resultado(run: RiskRun, model_name: str, alpha: str) -> RiskResult:
    """Um resultado sem erro; os numeros nao importam a regra do fecho, que so conta."""
    return RiskResult.objects.create(
        run=run,
        model_name=model_name,
        model_category="traditional",
        alpha=Decimal(alpha),
        hyperparameters={},
    )


def _desatualiza(run: RiskRun) -> None:
    """O objeto em memoria passa a achar que a linha esta `running`: o `close_run` nao pode
    decidir por ele, e tem de deixa-lo com o que esta gravado. Em funcao propria para o `mypy`
    nao estreitar `run.status` no teste."""
    run.status = RiskRun.Status.RUNNING
    run.finished_at = None


# --- V-05: `close_run` so escreve sobre execucao em `running` ------------------------------


@pytest.mark.django_db
def test_v05_close_run_sobre_linha_ja_ok_devolve_none_e_nao_escreve() -> None:
    run = _execucao(RiskRun.Status.OK, FIM_A)
    _desatualiza(run)

    assert close_run(run, FIM_B) is None

    relida = RiskRun.objects.get(pk=run.pk)
    assert (relida.status, relida.finished_at) == (RiskRun.Status.OK, FIM_A)
    assert (run.status, run.finished_at) == (RiskRun.Status.OK, FIM_A)


# --- V-06: o fecho atrasado nao sobrescreve e nao fecha pedido -----------------------------


@pytest.mark.django_db
def test_v06_o_fecho_atrasado_nao_sobrescreve_nem_chama_close_linked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _execucao(RiskRun.Status.RUNNING, None)
    _resultado(run, "parametric", "0.0100")
    _resultado(run, "parametric", "0.0500")
    assert close_run(run, FIM_A) == RiskRun.Status.PARTIAL

    chamadas: list[RiskRun] = []

    def espiao(execucao: RiskRun, now: datetime) -> int:
        chamadas.append(execucao)
        return 0

    monkeypatch.setattr("apps.risk.tasks.close_linked", espiao)

    _fechar_execucao([], run.pk)

    relida = RiskRun.objects.get(pk=run.pk)
    assert (relida.status, relida.finished_at) == (RiskRun.Status.PARTIAL, FIM_A)
    assert chamadas == []


# --- V-07: a escrita tardia da tarefa por modelo e descartada ------------------------------

ULTIMO_PREGAO = date(2026, 9, 18)  # sexta-feira


def _serie(ticker: str, quantidade: int = config.MIN_SESSIONS) -> Asset:
    """`quantidade` pregoes em dias uteis terminando em `ULTIMO_PREGAO`, no molde do
    `_serie` de `tests/risk/test_tasks.py`; os numeros nao importam, o calculo e substituido."""
    asset = _ativo(ticker)
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    datas: list[date] = []
    dia = ULTIMO_PREGAO
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    sorteio = random.Random(7)
    nivel = 100.0
    linhas = []
    for dia in sorted(datas):
        nivel *= math.exp(sorteio.gauss(0, 0.01))
        valor = Decimal(str(nivel)).quantize(Decimal("0.000001"))
        linhas.append(
            Price(
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
        )
    Price.objects.bulk_create(linhas)
    return asset


def _aberta() -> RiskRun:
    """Uma execucao `running` aberta por `open_run` sobre `MIN_SESSIONS` pregoes."""
    asset = _serie("BBB3")
    return open_run(asset, INICIO, 42, _bars(asset), BARATOS, full=False)


def _fecha(run_id: int) -> None:
    """O que a varredura faria no meio do calculo: a linha passa a `failed`, com fim."""
    RiskRun.objects.filter(pk=run_id).update(
        status=RiskRun.Status.FAILED, finished_at=timezone.now()
    )


@pytest.mark.django_db
def test_v07_resultados_de_execucao_fechada_durante_o_calculo_sao_descartados(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="apps.risk.tasks")
    run = _aberta()

    def calcula_e_fecha(
        key: object, bars: Sequence[Price], models: Sequence[str], *, full: bool
    ) -> tuple[Any, dict[Any, Any]]:
        _fecha(run.pk)
        return cast(Any, object()), {}

    gravacoes: list[RiskRun] = []

    def espiao(execucao: RiskRun, result: object, counts: object) -> None:
        gravacoes.append(execucao)

    monkeypatch.setattr("apps.risk.tasks.run_models", calcula_e_fecha)
    monkeypatch.setattr("apps.risk.tasks.write_results", espiao)

    _compute_asset_model(run.pk, "parametric")  # nao levanta

    assert gravacoes == []
    assert RiskResult.objects.filter(run=run).count() == 0
    assert "modelo parametric descartado" in caplog.text
    assert RiskRun.objects.get(pk=run.pk).status == RiskRun.Status.FAILED


@pytest.mark.django_db
def test_v07_par_de_erro_de_execucao_fechada_durante_o_calculo_e_descartado(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="apps.risk.tasks")
    run = _aberta()

    def fecha_e_levanta(
        key: object, bars: Sequence[Price], models: Sequence[str], *, full: bool
    ) -> tuple[Any, dict[Any, Any]]:
        _fecha(run.pk)
        raise RuntimeError("o calculo falhou depois do fecho")

    falhas: list[str] = []

    def espiao(execucao: RiskRun, model_name: str, error: str) -> None:
        falhas.append(error)

    monkeypatch.setattr("apps.risk.tasks.run_models", fecha_e_levanta)
    monkeypatch.setattr("apps.risk.tasks.write_failed", espiao)

    _compute_asset_model(run.pk, "parametric")  # nao levanta

    assert falhas == []
    assert RiskResult.objects.filter(run=run).count() == 0
    assert "modelo parametric descartado" in caplog.text


# --- os dados de V-01 a V-04b: a varredura com o relogio controlado ------------------------

AGORA = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
PRAZO = timedelta(hours=6)


@pytest.fixture
def prazo_do_pedido(settings: Settings) -> None:
    """O prazo do pedido sob demanda, fixo em 30 min: o V-03 depende dele para `expired`."""
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)


def _presa(
    asset: Asset, calculated_at: datetime, models: Sequence[str] = BARATOS
) -> RiskRun:
    """Uma execucao `running` aberta por `open_run` em `calculated_at`, sem resultado."""
    return open_run(asset, calculated_at, 42, _bars(asset), models, full=False)


def _calcula(run: RiskRun, models: Sequence[str] = BARATOS) -> ExperimentResult:
    """O motor de verdade, com os modelos pedidos, sobre a janela da execucao -- o molde
    de `_calcula` em `tests/risk/test_compute.py`, com o registry carregado aqui."""
    load_all_model_modules()
    load_all_backtest_modules()
    bars = _bars(run.asset)
    result = run_experiment(
        ExperimentConfig(
            ticker=run.asset.ticker,
            start=bars[0].date.isoformat(),
            end=bars[-1].date.isoformat(),
            model_names=list(models),
            backtest_names=list(config.BACKTESTS),
            alphas=list(config.ALPHAS),
            train_window_days=config.TRAIN_WINDOW_DAYS,
            seed=run.seed,
        ),
        SilverPriceProvider(),
    )
    assert all(r.error is None for r in result.runs), [r.error for r in result.runs]
    return result


def _so(result: ExperimentResult, model_name: str) -> ExperimentResult:
    """O mesmo resultado, so com as linhas de um modelo."""
    return ExperimentResult(
        config=result.config,
        runs=[r for r in result.runs if r.model_name == model_name],
    )


def _estado(run: RiskRun) -> tuple[str, datetime | None]:
    relida = RiskRun.objects.get(pk=run.pk)
    return str(relida.status), relida.finished_at


def _resultados() -> list[Any]:
    return list(RiskResult.objects.order_by("pk").values())


def _linhas(report: StaleReport) -> list[str]:
    return report.render().splitlines()


# --- V-01: a presa fecha pela regra do fecho ----------------------------------------------


@pytest.mark.django_db
def test_v01_as_presas_fecham_pela_regra_sem_mexer_nos_resultados() -> None:
    asset = _serie("CCC3")
    cheia = _presa(asset, AGORA - timedelta(hours=7, seconds=1))
    metade = _presa(asset, AGORA - timedelta(hours=7, seconds=2))
    vazia = _presa(asset, AGORA - timedelta(hours=7, seconds=3))
    result = _calcula(cheia)
    write_results(cheia, result, {})
    write_results(metade, _so(result, "parametric"), {})
    antes = _resultados()
    assert len(antes) == 6

    report = close_stale_runs(AGORA, PRAZO)

    assert _estado(cheia) == (RiskRun.Status.OK, AGORA)
    assert _estado(metade) == (RiskRun.Status.PARTIAL, AGORA)
    assert _estado(vazia) == (RiskRun.Status.FAILED, AGORA)
    assert _resultados() == antes
    assert report.failed == []
    assert not report.dry_run
    # a listagem ordena por `calculated_at`: a mais velha primeiro
    assert [
        (r.run_id, r.written, r.expected, r.status, r.already_closed)
        for r in report.runs
    ] == [
        (vazia.pk, 0, 4, "failed", False),
        (metade.pk, 2, 4, "partial", False),
        (cheia.pk, 4, 4, "ok", False),
    ]
    assert _linhas(report) == [
        f"CCC3         run={vazia.pk} 2026-09-30 04:59 0/4 failed",
        f"CCC3         run={metade.pk} 2026-09-30 04:59 2/4 partial",
        f"CCC3         run={cheia.pk} 2026-09-30 04:59 4/4 ok",
        "total: 3 fechadas, 0 ja fechadas, 0 falharam",
    ]


@pytest.mark.django_db
def test_v01_o_par_de_erro_conta_como_gravado_com_erro() -> None:
    asset = _serie("CCC3")
    run = _presa(asset, AGORA - timedelta(hours=7))
    write_results(run, _so(_calcula(run), "parametric"), {})
    write_failed(run, "historical", "RuntimeError: falhou")

    report = close_stale_runs(AGORA, PRAZO)

    assert _estado(run) == (RiskRun.Status.PARTIAL, AGORA)
    assert [(r.written, r.expected, r.status) for r in report.runs] == [
        (4, 4, "partial")
    ]


@pytest.mark.django_db
def test_v01b_a_regra_e_relativa_ao_pedido_de_um_modelo_so() -> None:
    asset = _serie("CCC3")
    run = _presa(asset, AGORA - timedelta(hours=7), models=["garch_1_1"])
    write_results(run, _calcula(run, ["garch_1_1"]), {})
    assert RiskResult.objects.filter(run=run, error="").count() == 2

    report = close_stale_runs(AGORA, PRAZO)

    assert _estado(run) == (RiskRun.Status.OK, AGORA)
    assert [(r.written, r.expected, r.status) for r in report.runs] == [(2, 2, "ok")]


# --- V-02: presa e a `running` velha --------------------------------------------------------


@pytest.mark.django_db
def test_v02_so_a_running_alem_do_prazo_e_presa() -> None:
    asset = _serie("CCC3")
    recente = _presa(asset, AGORA - PRAZO + timedelta(seconds=1))
    velha = _presa(asset, AGORA - PRAZO - timedelta(seconds=1))
    fim_ok = AGORA - timedelta(days=3) + timedelta(minutes=40)
    fim_failed = AGORA - timedelta(days=4) + timedelta(minutes=40)
    ok = _presa(asset, AGORA - timedelta(days=3))
    falhou = _presa(asset, AGORA - timedelta(days=4))
    RiskRun.objects.filter(pk=ok.pk).update(
        status=RiskRun.Status.OK, finished_at=fim_ok
    )
    RiskRun.objects.filter(pk=falhou.pk).update(
        status=RiskRun.Status.FAILED, finished_at=fim_failed
    )

    report = close_stale_runs(AGORA, PRAZO)

    assert [r.run_id for r in report.runs] == [velha.pk]
    assert _estado(velha) == (RiskRun.Status.FAILED, AGORA)
    assert _estado(recente) == (RiskRun.Status.RUNNING, None)
    assert _estado(ok) == (RiskRun.Status.OK, fim_ok)
    assert _estado(falhou) == (RiskRun.Status.FAILED, fim_failed)


# --- V-03: os pedidos ligados fecham pelo status da presa -----------------------------------


def _pedido(asset: Asset, run: RiskRun, requested_at: datetime) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset,
        status=ComputeRequest.Status.RUNNING,
        requested_at=requested_at,
        risk_run=run,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("prazo_do_pedido")
def test_v03_os_pedidos_ligados_fecham_com_a_presa() -> None:
    calculado_asset = _serie("DDD3")
    vencido_asset = _serie("EEE3")
    falhou_asset = _serie("FFF3")
    calculado_run = _presa(calculado_asset, AGORA - timedelta(hours=7))
    vencido_run = _presa(vencido_asset, AGORA - timedelta(hours=7))
    falhou_run = _presa(falhou_asset, AGORA - timedelta(hours=7))
    result = _calcula(calculado_run)
    write_results(calculado_run, result, {})
    write_results(vencido_run, result, {})
    calculado = _pedido(calculado_asset, calculado_run, AGORA - timedelta(minutes=10))
    vencido = _pedido(vencido_asset, vencido_run, AGORA - timedelta(hours=2))
    falhou = _pedido(falhou_asset, falhou_run, AGORA - timedelta(minutes=10))

    report = close_stale_runs(AGORA, PRAZO)

    assert report.failed == []
    assert _estado(calculado_run) == (RiskRun.Status.OK, AGORA)
    assert _estado(vencido_run) == (RiskRun.Status.OK, AGORA)
    assert _estado(falhou_run) == (RiskRun.Status.FAILED, AGORA)
    calculado.refresh_from_db()
    vencido.refresh_from_db()
    falhou.refresh_from_db()
    assert (calculado.status, calculado.reason, calculado.finished_at) == (
        ComputeRequest.Status.DONE,
        "calculado",
        AGORA,
    )
    assert (vencido.status, vencido.reason, vencido.finished_at) == (
        ComputeRequest.Status.EXPIRED,
        "expirado (30 min)",
        AGORA,
    )
    assert (falhou.status, falhou.reason, falhou.finished_at) == (
        ComputeRequest.Status.FAILED,
        "a execucao falhou",
        AGORA,
    )


# --- V-04: a falha de uma nao para as outras; a da listagem sobe --------------------------


@pytest.mark.django_db
def test_v04_a_falha_de_uma_presa_nao_para_a_seguinte(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    asset = _serie("CCC3")
    primeira = _presa(asset, AGORA - timedelta(hours=8))
    segunda = _presa(asset, AGORA - timedelta(hours=7))
    chamadas: list[int] = []

    def levanta_na_primeira(run: RiskRun, finished_at: datetime) -> str | None:
        chamadas.append(run.pk)
        if len(chamadas) == 1:
            raise RuntimeError("fecho injetado")
        return close_run(run, finished_at)

    monkeypatch.setattr("apps.risk.stale.close_run", levanta_na_primeira)

    report = close_stale_runs(AGORA, PRAZO)  # nao levanta

    assert chamadas == [primeira.pk, segunda.pk]
    assert report.failed == [(primeira.pk, "RuntimeError: fecho injetado")]
    assert [(r.run_id, r.status) for r in report.runs] == [(segunda.pk, "failed")]
    assert _estado(primeira) == (RiskRun.Status.RUNNING, None)
    assert _estado(segunda) == (RiskRun.Status.FAILED, AGORA)
    assert f"execucao {primeira.pk}" in caplog.text
    assert _linhas(report) == [
        f"CCC3         run={segunda.pk} 2026-09-30 05:00 0/4 failed",
        f"FALHOU run={primeira.pk}: RuntimeError: fecho injetado",
        "total: 1 fechadas, 0 ja fechadas, 1 falharam",
    ]


@pytest.mark.django_db
def test_v04_a_falha_da_listagem_sobe(monkeypatch: pytest.MonkeyPatch) -> None:
    def levanta(now: datetime, older_than: timedelta) -> list[RiskRun]:
        raise RuntimeError("listagem injetada")

    monkeypatch.setattr("apps.risk.stale._list_stale", levanta)

    with pytest.raises(RuntimeError, match="listagem injetada"):
        close_stale_runs(AGORA, PRAZO)


# --- V-04b: fechada entre a listagem e a trava ----------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("dry_run", [False, True])
def test_v04b_fechada_entre_a_listagem_e_a_trava_entra_como_ja_fechada(
    monkeypatch: pytest.MonkeyPatch, dry_run: bool
) -> None:
    asset = _serie("CCC3")
    run = _presa(asset, AGORA - timedelta(hours=7))
    fim = AGORA - timedelta(minutes=5)

    def fecha_ok() -> None:
        RiskRun.objects.filter(pk=run.pk).update(
            status=RiskRun.Status.OK, finished_at=fim
        )

    monkeypatch.setattr("apps.risk.stale._after_stale_listing", fecha_ok)

    report = close_stale_runs(AGORA, PRAZO, dry_run=dry_run)

    assert report.failed == []
    assert [(r.run_id, r.status, r.already_closed) for r in report.runs] == [
        (run.pk, "ok", True)
    ]
    assert _estado(run) == (RiskRun.Status.OK, fim)
    verbo = "fechariam" if dry_run else "fechadas"
    assert _linhas(report) == [
        f"CCC3         run={run.pk} 2026-09-30 05:00 ja fechada (ok)",
        f"total: 0 {verbo}, 1 ja fechadas, 0 falharam",
    ]


# --- o `render`: sem presa, e o `dry_run` que nao escreve ----------------------------------


@pytest.mark.django_db
def test_render_sem_presa_e_a_linha_unica() -> None:
    report = close_stale_runs(AGORA, PRAZO)

    assert report.render() == "nenhuma execução presa"


@pytest.mark.django_db
def test_dry_run_diz_o_que_escreveria_e_nao_escreve() -> None:
    asset = _serie("CCC3")
    run = _presa(asset, AGORA - timedelta(hours=7))
    write_results(run, _so(_calcula(run), "parametric"), {})
    antes = _resultados()

    report = close_stale_runs(AGORA, PRAZO, dry_run=True)

    assert report.dry_run
    assert _estado(run) == (RiskRun.Status.RUNNING, None)
    assert _resultados() == antes
    assert _linhas(report) == [
        f"CCC3         run={run.pk} 2026-09-30 05:00 2/4 fecharia partial",
        "total: 1 fechariam, 0 ja fechadas, 0 falharam",
    ]


# --- V-11: a tarefa da varredura nunca levanta ----------------------------------------------


def test_v11_fechar_presas_nao_levanta_quando_a_varredura_falha(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def levanta(now: datetime, older_than: timedelta, **kwargs: Any) -> StaleReport:
        raise RuntimeError("varredura injetada")

    monkeypatch.setattr("apps.risk.tasks.close_stale_runs", levanta)

    assert _fechar_presas() is None  # type: ignore[func-returns-value]
    assert "varredura das execucoes presas falhou" in caplog.text


def test_fechar_presas_usa_o_prazo_da_configuracao_e_registra_o_relatorio(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    settings: Settings,
) -> None:
    caplog.set_level(logging.INFO, logger="apps.risk.tasks")
    settings.RUVOR_RISK_STALE_AFTER = timedelta(minutes=400)
    prazos: list[timedelta] = []

    def vazia(now: datetime, older_than: timedelta, **kwargs: Any) -> StaleReport:
        prazos.append(older_than)
        return StaleReport(runs=[], failed=[], dry_run=False)

    monkeypatch.setattr("apps.risk.tasks.close_stale_runs", vazia)

    _fechar_presas()

    assert prazos == [timedelta(minutes=400)]
    assert "presas: nenhuma execução presa" in caplog.text
