"""As tarefas de risco do caminho assincrono: abertura, uma por (ativo, modelo), e o fecho.

Molde de `config/tasks.py`: cada tarefa e uma funcao com sublinhado, registrada com
`app.task(name=...)(funcao)` -- sob mypy estrito, `@app.task` reprova com
untyped-decorator. Os nomes de registro sao explicitos, e sao contrato.

Quem chama quem:

- `abrir_execucao` cria a `risk_run` **no worker** (RF-03), `running`, e entrega ao
  `_enqueue` um `chord` de uma `compute_asset_model` por modelo com `fechar_execucao` de
  corpo. E a unica que pode levantar: sem linha, nao ha onde gravar `error`;
- `compute_asset_model` grava os dois `risk_result` do modelo em transacao propria (RF-02)
  e **nunca levanta** (RF-06): se uma tarefa do grupo levantasse, o corpo do `chord` nao
  rodaria e a execucao ficaria `running` para sempre;
- `fechar_execucao` ignora o que o grupo devolveu e le o banco (RF-05).

**O registry e carregado nas duas primeiras**, pelos nomes importados aqui: o filho do
*prefork* nasce sem ele, e o `compute_risk` sincrono so o tinha porque passa por
`run_compute_risk`. `run_experiment`, `open_run`, `write_results`, `write_failed`,
`close_run` e `_enqueue` sao chamados pelo nome global **deste** modulo -- e onde os testes
os substituem.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from celery import chord
from django.db import transaction
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, run_experiment
from engine.models import load_all_model_modules

from apps.assets.models import Asset
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
from config.celery import app

logger = logging.getLogger(__name__)


class SeriesChanged(Exception):
    """A serie da janela da execucao nao e mais a que a abertura mediu.

    A linha da `risk_run` e a fonte de verdade: calcular sobre outra serie gravaria numeros
    que o manifesto nao descreve, sem erro nenhum.
    """


def _enqueue(signature: Any) -> None:
    """Enfileira. E o ponto que os testes substituem: nenhum deles fala com o Redis."""
    signature.apply_async()


def _abrir_execucao(
    ticker: str, calculated_at_iso: str, seed: int, models: list[str]
) -> int | None:
    """Abre a execucao do ativo e enfileira o grupo; devolve o `run_id`.

    Serie abaixo de `MIN_SESSIONS` e pulo silencioso, como no sincrono: devolve `None` e
    nao cria linha.
    """
    load_all_model_modules()
    load_all_backtest_modules()
    asset = Asset.objects.get(ticker=ticker)
    bars = _bars(asset)
    if len(bars) < config.MIN_SESSIONS:
        logger.info(
            "%s pulado: serie curta (%d pregoes, minimo %d)",
            ticker,
            len(bars),
            config.MIN_SESSIONS,
        )
        return None
    run = open_run(asset, datetime.fromisoformat(calculated_at_iso), seed, bars, models)
    # Montado sem aplicar: `chord(...)(corpo)` ja enfileiraria, e nenhum duplo capturaria
    # nada. O cabecalho e imutavel (`.si`), porque nao ha o que receber; o corpo (`.s`)
    # recebe a lista de resultados do cabecalho como primeiro argumento.
    _enqueue(
        chord(
            [compute_asset_model.si(run.id, model_name) for model_name in models],
            fechar_execucao.s(run.id),
        )
    )
    return run.id


def _compute_asset_model(run_id: int, model_name: str) -> None:
    """Calcula um modelo nos dois niveis e grava os dois resultados. Nunca levanta.

    Qualquer falha depois de achar a execucao vira o par de erro do modelo, pelo
    `write_failed` -- numeros nulos, `error` preenchido --, e a tarefa termina normalmente.
    """
    try:
        run = RiskRun.objects.select_related("asset").get(pk=run_id)
    except Exception:
        logger.exception("execucao %s nao encontrada; nada a gravar", run_id)
        return
    try:
        # Repeticao do Celery nao duplica linha nem estoura a unicidade.
        if RiskResult.objects.filter(run=run, model_name=model_name).exists():
            return
        load_all_model_modules()
        load_all_backtest_modules()
        # A janela da linha, nao a serie de hoje: pregao novo depois do `as_of_date` nao
        # entra, e serie reconformada no meio (D-53) e acusada pela contagem.
        bars = [
            bar
            for bar in _bars(run.asset)
            if run.first_price_date <= bar.date <= run.as_of_date
        ]
        if len(bars) != run.price_count:
            raise SeriesChanged(
                f"serie mudou desde a abertura: {len(bars)} pregoes, "
                f"esperados {run.price_count}"
            )
        result = run_experiment(
            ExperimentConfig(
                ticker=run.asset.ticker,
                start=run.first_price_date.isoformat(),
                end=run.as_of_date.isoformat(),
                model_names=[model_name],
                backtest_names=list(config.BACKTESTS),
                alphas=list(config.ALPHAS),
                train_window_days=run.train_window_days,
                seed=run.seed,
            ),
            SilverPriceProvider(),
        )
        with transaction.atomic():  # os dois niveis do modelo entram juntos (RF-02)
            write_results(run, result)
    except Exception as exc:
        try:
            with transaction.atomic():
                write_failed(run, model_name, f"{type(exc).__name__}: {exc}")
        except Exception:
            logger.exception(
                "execucao %s, modelo %s: nem o erro pode ser gravado",
                run_id,
                model_name,
            )


def _fechar_execucao(_resultados: object, run_id: int) -> None:
    """O corpo do `chord`: le o banco e escreve estado e fim. `_resultados` e ignorado."""
    close_run(RiskRun.objects.get(pk=run_id), timezone.now())


# Registro sem a sintaxe de decorador, como em `config/tasks.py`.
abrir_execucao = app.task(name="apps.risk.tasks.abrir_execucao")(_abrir_execucao)
compute_asset_model = app.task(name="apps.risk.tasks.compute_asset_model")(
    _compute_asset_model
)
fechar_execucao = app.task(name="apps.risk.tasks.fechar_execucao")(_fechar_execucao)
