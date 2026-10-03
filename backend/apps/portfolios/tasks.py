"""As tarefas do risco da carteira (M2.2a, RF-14): a abertura, uma por modelo, e o fecho. So no
`worker`.

Molde de `apps/risk/tasks.py`: cada tarefa e uma funcao com sublinhado, registrada com
`app.task(name=...)(funcao)`; os nomes de registro sao explicitos e sao contrato -- a web enfileira
a abertura pelo nome (D-89). Cada uma recebe `organization_id` e roda dentro de
`organization_scope(organization_id)`; nenhuma chama `.unscoped`.

**A trava da execucao** (`lock_run`, `pg_advisory_xact_lock(7104, run_id)`): toda escrita sobre a
execucao ou os resultados dela acontece numa transacao, **depois** de pegar a trava e de **reler**
a linha por uma leitura simples -- sem `select_for_update`, que com o esquema no `db_table` o
PostgreSQL recusa. Fechada pelo caminho de outro, a escrita e descartada (D-150, item 3).

- `abrir_risco_carteira` confere o registry (D-66) -- modelo pedido fora dele fecha a execucao
  `failed` **e so depois do commit** levanta `ModelsMissing` --, escreve `engine_version` e, fora
  da transacao, enfileira o `chord` das tarefas por modelo na ordem da D-73, com o fecho de corpo.
  Reentregue (`engine_version` ja escrito), nao enfileira de novo;
- `calcular_modelo_carteira` **nunca levanta** (D-70): reconstroi a serie da janela da execucao e,
  com o hash igual, calcula; com o hash diferente, o par `"serie mudou"`; com excecao, o par do
  erro. Os tres caminhos terminam em `_write`;
- `fechar_risco_carteira` le o banco e escreve `status` e `finished_at` pela regra de
  `status_for`, so sobre execucao `running`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from importlib.metadata import version
from typing import Any

from celery import chord
from django.db import transaction
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, ModelRunResult, run_experiment
from engine.models import get_model, list_models, load_all_model_modules
from engine.models.base import ModelCategory

from apps.accounts.tenancy import organization_scope
from apps.portfolios import series
from apps.portfolios.compute import failed_rows, row
from apps.portfolios.locks import lock_run
from apps.portfolios.models import PortfolioRiskResult, PortfolioRiskRun
from apps.portfolios.provider import PortfolioSeriesProvider
from apps.risk import config as risk_config
from apps.risk.compute import ModelsMissing, status_for
from apps.risk.models import RiskRun
from config.celery import app

logger = logging.getLogger(__name__)

SERIES_CHANGED = "serie mudou"

#: a ordem de custo do cabecalho do `chord` (D-73): o que termina em segundos vai primeiro
_RANK = {
    ModelCategory.TRADITIONAL: 0,
    ModelCategory.GARCH: 1,
    ModelCategory.ML: 2,
}


def _enqueue(signature: Any) -> None:
    """Enfileira. E o ponto que os testes substituem: nenhum deles fala com o Redis."""
    signature.apply_async()


def _after_run_lock() -> None:
    """Ponto de desvio dos testes concorrentes (V-16a), entre a trava e a releitura da escrita
    da tarefa por modelo. Nao faz nada; e chamado pelo nome global deste modulo."""


def _after_close_lock() -> None:
    """Ponto de desvio dos testes concorrentes (V-16b), entre a trava e a releitura do fecho.
    Nao faz nada; e chamado pelo nome global deste modulo."""


def _close_failed(run: PortfolioRiskRun) -> None:
    run.status = RiskRun.Status.FAILED
    run.finished_at = timezone.now()
    run.save(update_fields=["status", "finished_at"])


def _write(
    run_id: int,
    model_name: str,
    rows: Callable[[PortfolioRiskRun], list[PortfolioRiskResult]],
) -> None:
    """A escrita dos dois resultados do modelo, sob a trava e so em execucao `running`."""
    with transaction.atomic():
        lock_run(run_id)
        _after_run_lock()
        run = PortfolioRiskRun.objects.get(pk=run_id)  # releitura simples
        if run.status != RiskRun.Status.RUNNING:
            logger.info(
                "carteira run=%d modelo=%s: execucao ja fechada; descartado",
                run_id,
                model_name,
            )
            return
        if run.results.filter(model_name=model_name).exists():
            return  # reentrega que chegou ao mesmo tempo
        PortfolioRiskResult.objects.bulk_create(rows(run))


def _abrir_risco_carteira(run_id: int, organization_id: int) -> None:
    load_all_model_modules()
    load_all_backtest_modules()
    with organization_scope(organization_id):
        missing: list[str] = []
        with transaction.atomic():
            lock_run(run_id)
            run = PortfolioRiskRun.objects.get(pk=run_id)
            if run.status != RiskRun.Status.RUNNING or run.engine_version:
                return  # fechada, ou abertura reentregue: ja enfileirou
            missing = [m for m in run.requested_models if m not in list_models()]
            if missing:
                _close_failed(run)
            else:
                run.engine_version = version("ruvor-engine")
                run.save(update_fields=["engine_version"])
        if missing:
            raise ModelsMissing(missing)  # depois do commit: o `failed` fica gravado
        by_cost = sorted(
            run.requested_models, key=lambda name: _RANK[get_model(name).category]
        )
        # Montado sem aplicar: `chord(...)(corpo)` ja enfileiraria
        group = chord(
            [calcular_modelo_carteira.si(run_id, organization_id, n) for n in by_cost],
            fechar_risco_carteira.s(run_id, organization_id),
        )
        try:
            _enqueue(group)  # fora do atomic: a linha ja esta commitada
        except Exception:
            with transaction.atomic():
                lock_run(run_id)
                run = PortfolioRiskRun.objects.get(pk=run_id)
                if run.status == RiskRun.Status.RUNNING:
                    _close_failed(run)
            raise


def _calcular_modelo_carteira(
    run_id: int, organization_id: int, model_name: str
) -> None:
    with organization_scope(organization_id):
        try:
            run = PortfolioRiskRun.objects.select_related("version__portfolio").get(
                pk=run_id
            )
        except Exception:
            logger.exception("carteira run=%s nao encontrada; nada a gravar", run_id)
            return
        # os tres caminhos -- o resultado bom, o par de "serie mudou" e o par da excecao --
        # terminam em `_write`; nenhum grava por outro lugar
        failure: str | None = None
        computed: list[ModelRunResult] = []
        try:
            # Repeticao do Celery nao calcula de novo
            if run.results.filter(model_name=model_name).exists():
                return
            load_all_model_modules()
            load_all_backtest_modules()
            s = series.build(run.version, first=run.first_date, last=run.as_of_date)
            if s.sha256 != run.series_sha256:
                failure = SERIES_CHANGED
            else:
                portfolio = run.version.portfolio
                experiment = ExperimentConfig(
                    ticker=f"carteira:{portfolio.public_id}:v{run.version.number}",
                    start=run.first_date.isoformat(),
                    end=run.as_of_date.isoformat(),
                    model_names=[model_name],
                    backtest_names=list(risk_config.BACKTESTS),
                    alphas=list(risk_config.ALPHAS),
                    train_window_days=risk_config.TRAIN_WINDOW_DAYS,
                    seed=risk_config.DEFAULT_SEED,
                )
                computed = run_experiment(experiment, PortfolioSeriesProvider(s)).runs
        except Exception as exc:
            logger.exception("carteira run=%d modelo=%s: falhou", run_id, model_name)
            failure = f"{type(exc).__name__}: {exc}"

        def rows(locked: PortfolioRiskRun) -> list[PortfolioRiskResult]:
            if failure is not None:
                return failed_rows(locked, model_name, failure)
            return [row(locked, model_run) for model_run in computed]

        try:
            _write(run_id, model_name, rows)
        except Exception:
            logger.exception(
                "carteira run=%d modelo=%s: a escrita falhou", run_id, model_name
            )


def _fechar_risco_carteira(
    _resultados: object, run_id: int, organization_id: int
) -> None:
    """O corpo do `chord`: le o banco e escreve estado e fim. `_resultados` e ignorado."""
    with organization_scope(organization_id), transaction.atomic():
        lock_run(run_id)
        _after_close_lock()
        run = PortfolioRiskRun.objects.get(pk=run_id)
        if run.status != RiskRun.Status.RUNNING:
            logger.info("carteira run=%d: ja fechada; o fecho nao escreve", run_id)
            return
        results = run.results.all()
        written = results.count()
        with_error = results.exclude(error="").count()
        run.status = status_for(
            len(run.requested_models) * len(risk_config.ALPHAS), written, with_error
        )
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at"])


abrir_risco_carteira = app.task(name="apps.portfolios.tasks.abrir_risco_carteira")(
    _abrir_risco_carteira
)
calcular_modelo_carteira = app.task(
    name="apps.portfolios.tasks.calcular_modelo_carteira"
)(_calcular_modelo_carteira)
fechar_risco_carteira = app.task(name="apps.portfolios.tasks.fechar_risco_carteira")(
    _fechar_risco_carteira
)
