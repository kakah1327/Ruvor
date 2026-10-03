"""M2.2a, T6: a tarefa por modelo e o fecho ao mesmo tempo (RF-14; V-16, as duas corridas).

No molde de `tests/risk/test_concorrencia.py`: `transaction=True`, com `TRANSACIONAL` e
`banco_limpo`; o registry carregado **antes** das threads; o `run_experiment` trocado por um duplo
rapido que devolve um resultado aprovado em cada nivel. As esperas do lado que a mutacao precisa
sao de 5 s; as que so existem para estourar no caso correto, de 2 s.

- **(a) a tarefa trava primeiro**: ela para em `_after_run_lock`, com a trava da execucao na mao,
  sinaliza `tarefa_travou` e espera `fecho_terminou` (5 s). O fecho so parte depois e bloqueia na
  trava; a espera da tarefa estoura, ela grava os 2 resultados e solta; o fecho rele, conta 2 de
  18 e fecha `partial`. Sem a trava no fecho, ele fecha `failed` com 0 no meio, e a tarefa, ao
  reler, descarta.
- **(b) o fecho trava primeiro**: ele para em `_after_close_lock`, sinaliza `fecho_travou` e
  espera `tarefa_terminou` (2 s). A tarefa so parte depois e bloqueia na trava; a espera do fecho
  estoura, ele fecha `failed` com 0 e solta; a tarefa rele, acha fechada e descarta. Se a tarefa
  relesse antes da trava, veria `running` e gravaria sobre a execucao fechada.

Cada thread chama `connections.close_all()` no `finally`; o teste faz `join(timeout=30)`.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

import pandas as pd
import pytest
from django.db import connections
from engine.backtesting import load_all_backtest_modules
from engine.backtesting.base import BacktestResult
from engine.experiments.runner import ExperimentConfig, ExperimentResult, ModelRunResult
from engine.models import load_all_model_modules
from engine.models.base import VaREstimate

from apps.portfolios.models import PortfolioRiskResult, PortfolioRiskRun
from apps.portfolios.tasks import _calcular_modelo_carteira, _fechar_risco_carteira
from apps.risk.models import RiskRun
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)
from tests.portfolios.dados import (
    carteira,
    execucao_da_serie,
    org_e_pessoas,
    serie_longa,
)

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]

ESPERA_DO_LADO_DA_MUTACAO = 5
ESPERA_QUE_ESTOURA = 2
JOIN = 30


def _motor_rapido(config: ExperimentConfig, provider: object) -> ExperimentResult:
    def aprovado(nome: str) -> BacktestResult:
        return BacktestResult(
            test_name=nome,
            statistic=0.1,
            p_value=0.5,
            passed=True,
            details={"violations": 3, "expected": 2.5} if nome == "kupiec" else {},
        )

    return ExperimentResult(
        config=config,
        runs=[
            ModelRunResult(
                model_name=config.model_names[0],
                alpha=alpha,
                backtests=[aprovado(n) for n in config.backtest_names],
                estimate=VaREstimate(
                    var_series=pd.Series([0.02, 0.021]),
                    alpha=alpha,
                    horizon=1,
                    model_name=config.model_names[0],
                ),
            )
            for alpha in config.alphas
        ],
    )


@pytest.fixture(autouse=True)
def motor(monkeypatch: pytest.MonkeyPatch) -> None:
    load_all_model_modules()  # antes das threads
    load_all_backtest_modules()
    monkeypatch.setattr("apps.portfolios.tasks.run_experiment", _motor_rapido)


def _execucao() -> tuple[PortfolioRiskRun, int]:
    serie_longa("PETR4")
    serie_longa("VALE3")
    pessoas = org_e_pessoas()
    portfolio = carteira(pessoas.admin, {"PETR4": "60", "VALE3": "40"})
    return execucao_da_serie(portfolio, pessoas.admin), pessoas.acme.pk


def _parte(
    nome: str, alvo: Callable[[], object], erros: list[BaseException]
) -> threading.Thread:
    def corre() -> None:
        try:
            alvo()
        except BaseException as exc:
            erros.append(exc)
        finally:
            connections.close_all()

    thread = threading.Thread(target=corre, name=nome, daemon=True)
    thread.start()
    return thread


def _junta(*threads: threading.Thread) -> None:
    for thread in threads:
        thread.join(timeout=JOIN)
    assert not any(thread.is_alive() for thread in threads)


def test_v16a_o_fecho_espera_a_tarefa_que_travou_e_fecha_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run, org = _execucao()
    tarefa_travou = threading.Event()
    fecho_terminou = threading.Event()
    esperas: list[bool] = []

    def segura_a_tarefa() -> None:
        tarefa_travou.set()
        esperas.append(fecho_terminou.wait(ESPERA_DO_LADO_DA_MUTACAO))

    monkeypatch.setattr("apps.portfolios.tasks._after_run_lock", segura_a_tarefa)

    def fecha() -> None:
        try:
            _fechar_risco_carteira([None], run.pk, org)
        finally:
            fecho_terminou.set()

    erros: list[BaseException] = []
    tarefa = _parte(
        "tarefa", lambda: _calcular_modelo_carteira(run.pk, org, "historical"), erros
    )
    assert tarefa_travou.wait(ESPERA_DO_LADO_DA_MUTACAO)
    fecho = _parte("fecho", fecha, erros)
    _junta(tarefa, fecho)

    assert erros == []
    assert esperas == [False]  # o fecho nao terminou enquanto a tarefa segurava a trava
    linha = PortfolioRiskRun.unscoped.get(pk=run.pk)
    assert linha.status == RiskRun.Status.PARTIAL
    assert PortfolioRiskResult.unscoped.filter(run=run).count() == 2


def test_v16b_a_tarefa_espera_o_fecho_que_travou_e_descarta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run, org = _execucao()
    fecho_travou = threading.Event()
    tarefa_terminou = threading.Event()

    def segura_o_fecho() -> None:
        fecho_travou.set()
        tarefa_terminou.wait(ESPERA_QUE_ESTOURA)

    monkeypatch.setattr("apps.portfolios.tasks._after_close_lock", segura_o_fecho)

    def calcula() -> None:
        try:
            _calcular_modelo_carteira(run.pk, org, "historical")
        finally:
            tarefa_terminou.set()

    erros: list[BaseException] = []
    fecho: Any = _parte(
        "fecho", lambda: _fechar_risco_carteira([None], run.pk, org), erros
    )
    assert fecho_travou.wait(ESPERA_DO_LADO_DA_MUTACAO)
    tarefa = _parte("tarefa", calcula, erros)
    _junta(fecho, tarefa)

    assert erros == []
    linha = PortfolioRiskRun.unscoped.get(pk=run.pk)
    assert linha.status == RiskRun.Status.FAILED
    assert PortfolioRiskResult.unscoped.filter(run=run).count() == 0
