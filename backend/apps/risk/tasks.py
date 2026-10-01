"""As tarefas de risco do caminho assincrono: abertura, uma por (ativo, modelo), e o fecho.

Molde de `config/tasks.py`: cada tarefa e uma funcao com sublinhado, registrada com
`app.task(name=...)(funcao)` -- a funcao com sublinhado e o ponto que os testes
chamam e substituem; os tipos vem do `celery-types` (D-134). Os nomes de registro sao
explicitos, e sao contrato.

Quem chama quem:

- `abrir_execucao` cria a `risk_run` **no worker** (RF-03), `running`, sob a trava por
  ativo (RF-24 do M1.6a) -- e pula o ativo que ja tem `running` recente --, e entrega ao
  `_enqueue`, **depois do commit**, um `chord` de uma `compute_asset_model` por modelo com
  `fechar_execucao` de corpo. E a unica que pode levantar: sem linha, nao ha onde gravar
  `error`;
- `compute_asset_model` grava os dois `risk_result` do modelo em transacao propria (RF-02)
  e **nunca levanta** (RF-06): se uma tarefa do grupo levantasse, o corpo do `chord` nao
  rodaria e a execucao ficaria `running` para sempre;
- `fechar_execucao` ignora o que o grupo devolveu e le o banco (RF-05), sob a mesma trava,
  e fecha os pedidos sob demanda ligados a execucao;
- `recalcular_cobertos` e o leque: uma `abrir_execucao` por ativo ativo com preco, pelo
  mesmo `enqueue_compute` que o `compute_risk --async` usa.

**Quem enfileira nao cria `risk_run`** (RF-03): `enqueue_compute` confere o registry,
resolve os ativos e produz o `calculated_at` **uma vez**, que viaja em ISO a todas as
aberturas -- se cada abertura chamasse `now()`, dois ativos do mesmo comando nasceriam em
instantes diferentes.

**O registry e carregado nas duas primeiras**, pelos nomes importados aqui: o filho do
*prefork* nasce sem ele, e o `compute_risk` sincrono so o tinha porque passa por
`run_compute_risk`. `run_models`, `open_run`, `write_results`, `write_failed`, `close_run`
e `_enqueue` sao chamados pelo nome global **deste** modulo -- e onde os testes os
substituem. O motor e chamado por `compute.run_models`, o mesmo ponto de entrada do
sincrono (M1.5b): quem quer substituir o `run_experiment` mira
`apps.risk.compute.run_experiment`, que e o nome que `run_models` chama.

**O `--full` viaja na `risk_run`** (RF-08): `enqueue_compute` e `abrir_execucao` recebem
`full`, a abertura o grava em `full_recompute`, e `compute_asset_model` o le da linha -- a
assinatura dela e a do fecho nao mudam. A tarefa por (ativo, modelo) monta a identidade dos
retratos (`SnapshotKey`) a partir da linha, e registra uma linha de log com os retratos
reaproveitados e treinados por nivel e a duracao.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, TypedDict, overload

from celery import chord
from django.db import transaction
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.models import get_model, list_models, load_all_model_modules
from engine.models.base import ModelCategory

from apps.api.models import ComputeRequest
from apps.api.ondemand import (
    OPEN_STATUSES,
    close_linked,
    close_request,
    lock_asset,
    timeout,
)
from apps.assets.models import Asset
from apps.risk import config
from apps.risk.compute import (
    MODELS,
    NO_CANDIDATES,
    SKIPPED_INACTIVE,
    ModelsMissing,
    SnapshotCounts,
    _bars,
    _resolve,
    close_run,
    open_run,
    run_models,
    write_failed,
    write_results,
)
from apps.risk.models import RiskResult, RiskRun
from apps.risk.snapshots import SnapshotKey, library_versions
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


@dataclass(frozen=True)
class AsyncReport:
    """O que o `--async` enfileirou: os tickers, nunca `run_id`, que ainda nao existe.

    `enqueued` sao os ativos com abertura enfileirada; `skipped`, os inativos do ramo sem
    argumentos. Serie curta nao aparece aqui: quem mede o piso e a abertura, no worker.
    """

    enqueued: list[str]
    skipped: list[str]

    def render(self) -> str:
        lines = [f"{ticker:<12} enfileirado" for ticker in self.enqueued]
        lines.extend(
            f"{ticker:<12} pulado: {SKIPPED_INACTIVE}" for ticker in self.skipped
        )
        if not self.enqueued:
            # Nada enfileirado: a mesma saida do sincrono, sem a linha de resumo.
            lines.append(NO_CANDIDATES)
            return "\n".join(lines)
        total = len(self.enqueued) + len(self.skipped)
        lines.append(
            f"risco assincrono: {total} ativos, {len(self.enqueued)} enfileirados, "
            f"{len(self.skipped)} pulados; acompanhe em gold.risk_run"
        )
        return "\n".join(lines)


def _missing_models(requested: list[str]) -> list[str]:
    """Os modelos pedidos que o registry nao oferece, com o registry carregado antes.

    O que o `enqueue_compute` e a cadeia sob demanda conferem antes de abrir qualquer coisa:
    registry incompleto e erro (D-66), nunca silencio.
    """
    load_all_model_modules()
    load_all_backtest_modules()
    return [m for m in requested if m not in list_models()]


def enqueue_compute(
    tickers: list[str],
    *,
    seed: int | None = None,
    models: list[str] | None = None,
    calculated_at: datetime | None = None,
    now: Callable[[], datetime] = timezone.now,
    full: bool = False,
) -> AsyncReport:
    """Enfileira uma abertura por ativo ativo; nao cria `risk_run` (RF-03).

    O que o `compute_risk --async` e o `recalcular_cobertos` compartilham. `ModelsMissing`
    e `InvalidTickers` levantam **antes** de enfileirar qualquer coisa, como no sincrono.
    `calculated_at` e o recebido ou o `now()` de **uma** chamada, o mesmo para todas as
    aberturas. `full` vai a cada abertura, que o grava na `risk_run` (RF-08).
    """
    requested = list(MODELS) if models is None else list(models)
    missing = _missing_models(requested)
    if missing:
        raise ModelsMissing(missing)  # antes de enfileirar (RF-17)

    assets, skipped = _resolve(tickers)  # InvalidTickers antes de enfileirar
    effective_seed = config.DEFAULT_SEED if seed is None else seed
    instant = now() if calculated_at is None else calculated_at
    for asset in assets:
        _enqueue(
            abrir_execucao.s(
                asset.ticker, instant.isoformat(), effective_seed, requested, full=full
            )
        )
    return AsyncReport([a.ticker for a in assets], [a.ticker for a in skipped])


#: a ordem de custo do cabecalho do `chord` (D-73): o que termina em segundos vai primeiro
_COST_RANK = {
    ModelCategory.TRADITIONAL: 0,
    ModelCategory.GARCH: 1,
    ModelCategory.ML: 2,
}


class OpeningResult(TypedDict):
    """O que a abertura devolve quando recebe `request_id` (RF-20): serializavel em JSON,
    porque a abertura tambem e tarefa enfileirada, com resultado gravado no Redis.

    `sessions` e quantos pregoes a serie tinha depois do criterio do `clean_prices` -- o
    `N` do motivo da serie curta --, e so vem preenchido em `short_series`.
    """

    outcome: Literal["opened", "short_series", "already_running", "request_closed"]
    run_id: int | None
    sessions: int | None


def _after_read_running() -> None:
    """Ponto de desvio dos testes concorrentes, entre a leitura da `running` e a criacao da
    execucao. Nao faz nada; e chamado pelo nome global deste modulo."""


def _after_close_lock() -> None:
    """Ponto de desvio dos testes concorrentes, entre a trava do fecho e o `close_run`. Nao
    faz nada; e chamado pelo nome global deste modulo."""


def _short_series_reason(sessions: int) -> str:
    """O motivo do pedido que fechou por serie curta, da lista fechada de `ondemand`."""
    return f"serie curta ({sessions} pregoes, minimo {config.MIN_SESSIONS})"


@overload
def _abrir_execucao(
    ticker: str,
    calculated_at_iso: str,
    seed: int,
    models: list[str],
    full: bool = ...,
    request_id: None = ...,
) -> int | None: ...
@overload
def _abrir_execucao(
    ticker: str,
    calculated_at_iso: str,
    seed: int,
    models: list[str],
    full: bool = ...,
    *,
    request_id: int,
) -> OpeningResult: ...
def _abrir_execucao(
    ticker: str,
    calculated_at_iso: str,
    seed: int,
    models: list[str],
    full: bool = False,
    request_id: int | None = None,
) -> int | OpeningResult | None:
    """Abre a execucao do ativo e enfileira o grupo depois do commit; devolve o `run_id`.

    Serie abaixo de `MIN_SESSIONS` e pulo silencioso, como no sincrono: devolve `None` e
    nao cria linha. `full` e gravado em `full_recompute`, de onde as tarefas o leem.

    **A transacao e literal na ordem** (RF-20, RF-24): a trava por ativo; com `request_id`,
    o pedido relido sob `select_for_update` -- ja fechado, sai `request_closed`; a `running`
    recente do ativo -- ha, pula, e com `request_id` liga o pedido a ela; a serie -- curta,
    sai, e com `request_id` fecha o pedido `done` com o motivo (ou `expired`, se venceu);
    senao cria a execucao e liga o pedido. O `chord` so e enfileirado **depois do commit**:
    antes, uma tarefa por modelo poderia rodar sem a `risk_run` visivel para a conexao dela,
    e um fecho rapido nao veria o pedido ligado.

    O prazo da `running` e contado de `timezone.now()`, nao do `calculated_at` recebido: a
    rotina passa um instante que pode ter minutos. A `running` e procurada pelo **estado
    gravado**: um pedido vencido e ainda gravado aberto passa, e quem o grava `expired` e o
    fecho.

    Sem `request_id` o retorno e o de sempre, `int | None`; com ele, um `OpeningResult`.
    """
    load_all_model_modules()
    load_all_backtest_modules()
    asset = Asset.objects.get(ticker=ticker)
    with transaction.atomic():
        lock_asset(asset.id)
        req: ComputeRequest | None = None
        if request_id is not None:
            req = ComputeRequest.objects.select_for_update().get(pk=request_id)
            if req.status not in OPEN_STATUSES:
                logger.info(
                    "%s pedido %d ja fechado (%s): nada aberto",
                    ticker,
                    request_id,
                    req.status,
                )
                return OpeningResult(
                    outcome="request_closed", run_id=None, sessions=None
                )
        running = (
            RiskRun.objects.filter(
                asset=asset,
                status=RiskRun.Status.RUNNING,
                calculated_at__gte=timezone.now() - timeout(),
            )
            .order_by("-calculated_at")
            .first()
        )
        _after_read_running()
        if running is not None:
            logger.info("%s pulado: em calculo (run=%d)", ticker, running.id)
            if req is None:
                return None
            req.risk_run = running
            req.save(update_fields=["risk_run"])
            return OpeningResult(
                outcome="already_running", run_id=running.id, sessions=None
            )
        bars = _bars(asset)
        if len(bars) < config.MIN_SESSIONS:
            logger.info(
                "%s pulado: serie curta (%d pregoes, minimo %d)",
                ticker,
                len(bars),
                config.MIN_SESSIONS,
            )
            if req is None:
                return None
            close_request(
                req,
                ComputeRequest.Status.DONE,
                _short_series_reason(len(bars)),
                "",
                timezone.now(),
            )
            return OpeningResult(
                outcome="short_series", run_id=None, sessions=len(bars)
            )
        run = open_run(
            asset,
            datetime.fromisoformat(calculated_at_iso),
            seed,
            bars,
            models,
            full=full,
            # a execucao e de quem abriu o pedido; no `already_running` acima ela continua
            # de quem chegou primeiro (M2.1a, RF-26)
            requested_by_id=req.requested_by_id if req is not None else None,
        )
        if req is not None:
            req.risk_run = run
            req.save(update_fields=["risk_run"])
        # O cabecalho sai por custo, nao na ordem pedida (D-73): com a fila por ordem de
        # chegada e duas vagas no worker, as redes na frente seguravam os modelos baratos
        # por minutos. `sorted` e estavel, entao dentro da categoria vale a ordem pedida --
        # e o `requested_models`, gravado acima, continua na ordem pedida.
        by_cost = sorted(models, key=lambda name: _COST_RANK[get_model(name).category])
        # Montado sem aplicar: `chord(...)(corpo)` ja enfileiraria, e nenhum duplo
        # capturaria nada. O cabecalho e imutavel (`.si`), porque nao ha o que receber; o
        # corpo (`.s`) recebe a lista de resultados do cabecalho como primeiro argumento.
        group = chord(
            [compute_asset_model.si(run.id, model_name) for model_name in by_cost],
            fechar_execucao.s(run.id),
        )
        # `_enqueue` e resolvido na hora do commit, pelo nome global: e onde os testes
        # poem o duplo.
        transaction.on_commit(lambda: _enqueue(group))
    if request_id is None:
        return run.id
    return OpeningResult(outcome="opened", run_id=run.id, sessions=None)


def _compute_asset_model(run_id: int, model_name: str) -> None:
    """Calcula um modelo nos dois niveis e grava os dois resultados. Nunca levanta.

    Qualquer falha depois de achar a execucao vira o par de erro do modelo, pelo
    `write_failed` -- numeros nulos, `error` preenchido --, e a tarefa termina normalmente.

    `full` sai de `run.full_recompute`, e a identidade dos retratos, da linha. Cada tarefa
    que calcula -- ou grava o par de erro -- registra uma linha em `info` com os retratos
    `reaproveitados/treinados` por nivel (`-/-` nos baratos e no que falhou) e a duracao da
    tarefa inteira.
    """
    started = time.monotonic()
    try:
        run = RiskRun.objects.select_related("asset").get(pk=run_id)
    except Exception:
        logger.exception("execucao %s nao encontrada; nada a gravar", run_id)
        return
    logged: SnapshotCounts = {}
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
        # A identidade vem da linha -- a janela, o primeiro pregao, a semente e a versao
        # do motor que o manifesto declara --, e as versoes de biblioteca, do que calcula.
        key = SnapshotKey(
            asset=run.asset,
            seed=run.seed,
            engine_version=run.engine_version,
            train_window_days=run.train_window_days,
            first_price_date=run.first_price_date,
            library_versions=library_versions(),
        )
        result, counts = run_models(key, bars, [model_name], full=run.full_recompute)
        with transaction.atomic():  # os dois niveis do modelo entram juntos (RF-02)
            write_results(run, result, counts)
        # o que o log mostra e o que foi gravado: so os niveis caros sem erro
        logged = {
            (r.model_name, r.alpha): counts[(r.model_name, r.alpha)]
            for r in result.runs
            if not r.error and (r.model_name, r.alpha) in counts
        }
    except Exception as exc:
        logged = {}
        try:
            with transaction.atomic():
                write_failed(run, model_name, f"{type(exc).__name__}: {exc}")
        except Exception:
            logger.exception(
                "execucao %s, modelo %s: nem o erro pode ser gravado",
                run_id,
                model_name,
            )
    logger.info(
        "risco %s run=%d modelo=%s alpha=0.05 %s/%s alpha=0.01 %s/%s %.2fs",
        run.asset.ticker,
        run.id,
        model_name,
        *_pair(logged, model_name, 0.05),
        *_pair(logged, model_name, 0.01),
        time.monotonic() - started,
    )


def _pair(counts: SnapshotCounts, model_name: str, alpha: float) -> tuple[str, str]:
    """`reaproveitados/treinados` de um nivel para o log; `-/-` quando nao se aplica."""
    pair = counts.get((model_name, alpha))
    return ("-", "-") if pair is None else (str(pair[0]), str(pair[1]))


def _fechar_execucao(_resultados: object, run_id: int) -> None:
    """O corpo do `chord`: le o banco e escreve estado e fim. `_resultados` e ignorado.

    **Em transacao, literal na ordem** (RF-20): a execucao relida dentro do `atomic`, a
    trava por ativo, a execucao relida de novo -- o estado depois da trava --, o
    `close_run` e o `close_linked`, que fecha todo pedido aberto ligado a ela. Fora de
    transacao a trava `xact` se soltaria no fim da propria consulta, e uma abertura poderia
    ligar um pedido a esta execucao depois de o fecho passar sem ve-lo.
    """
    with transaction.atomic():
        run = RiskRun.objects.select_related("asset").get(pk=run_id)
        lock_asset(run.asset_id)
        _after_close_lock()
        run.refresh_from_db()
        now = timezone.now()
        close_run(run, now)
        close_linked(run, now)


def _recalcular_cobertos(calculated_at_iso: str | None = None) -> None:
    """O leque: uma abertura por ativo **ativo com preco**, todas no mesmo instante.

    Sem tickers, e o ramo "os ativos com preco" do `_resolve`. Sem `calculated_at_iso`,
    `enqueue_compute` faz o `now()` uma vez.
    """
    calculated_at = (
        None if calculated_at_iso is None else datetime.fromisoformat(calculated_at_iso)
    )
    report = enqueue_compute([], calculated_at=calculated_at)
    logger.info("%s", report.render())


# Registro sem a sintaxe de decorador, como em `config/tasks.py`.
abrir_execucao = app.task(name="apps.risk.tasks.abrir_execucao")(_abrir_execucao)
compute_asset_model = app.task(name="apps.risk.tasks.compute_asset_model")(
    _compute_asset_model
)
fechar_execucao = app.task(name="apps.risk.tasks.fechar_execucao")(_fechar_execucao)
recalcular_cobertos = app.task(name="apps.risk.tasks.recalcular_cobertos")(
    _recalcular_cobertos
)
