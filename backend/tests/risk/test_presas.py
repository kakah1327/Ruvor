"""A execucao presa (M1.5c): V-05, V-06, V-07 e V-15.

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

from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.compute import _bars, close_run, open_run
from apps.risk.models import RiskResult, RiskRun
from apps.risk.tasks import _compute_asset_model, _fechar_execucao

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
