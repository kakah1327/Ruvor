"""O dominio do pedido de calculo sob demanda (RF-15 a RF-19 do M1.6a).

Importavel pela `web` e pelo `worker`: so modelos, `django.db` e a aplicacao Celery (para o
`send_task`). **Nao importa o motor** (RF-10), nem `apps.risk.tasks` nem `apps.assets.tasks`
-- o V-10 confere.

**As travas** sao `pg_advisory_xact_lock` na forma de dois inteiros, `(classe, id)` (RF-17):
uma classe para a trava global do `POST` (id 0) e outra para a trava por ativo do RF-24 (id
do ativo), para que os espacos nao se misturem. A trava `xact` fora de transacao se solta no
fim da propria consulta e vira enfeite; por isso as duas funcoes quebram alto fora de
`transaction.atomic`.

**Os motivos** sao lista fechada:

| Desfecho | `status` | `reason` |
|---|---|---|
| a `risk_run` ligada fechou `ok`/`partial` | `done` | `calculado` |
| serie curta depois da coleta | `done` | `serie curta (N pregoes, minimo 503)` |
| a coleta falhou | `failed` | `falhou na coleta` (+ `error`) |
| as metricas falharam | `failed` | `falhou nas metricas` |
| a abertura falhou (inclui registry incompleto) | `failed` | `falhou na abertura` |
| a `risk_run` ligada fechou `failed` | `failed` | `a execucao falhou` |
| o broker recusou | `failed` | `o broker recusou o pedido` |
| venceu o prazo | `expired` | `expirado (N min)` |

**`expired` e final, e "expirado" quer dizer gravado ou vencido pelo relogio** (RF-15): todo
ponto que fecha um pedido passa por `close_request` ou `close_linked`, que gravam `expired`
no lugar do desfecho quando o prazo venceu. As duas so escrevem sobre pedido ainda gravado
aberto -- um pedido ja fechado nao muda.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone

from apps.api.models import ComputeRequest
from apps.risk.models import RiskRun
from config.celery import app

LOCK_CLASS_ON_DEMAND = 7101  # pg_advisory_xact_lock(7101, 0): a trava global do POST
LOCK_CLASS_ASSET = 7102  # pg_advisory_xact_lock(7102, asset_id): a trava por ativo

logger = logging.getLogger(__name__)

OPEN_STATUSES = (ComputeRequest.Status.QUEUED, ComputeRequest.Status.RUNNING)

REASON_CALCULATED = "calculado"
REASON_COLLECT_FAILED = "falhou na coleta"
REASON_METRICS_FAILED = "falhou nas metricas"
REASON_OPENING_FAILED = "falhou na abertura"
REASON_RUN_FAILED = "a execucao falhou"
REASON_BROKER_REFUSED = "o broker recusou o pedido"


def _xact_lock(lock_class: int, lock_id: int) -> None:
    if not connection.in_atomic_block:
        raise RuntimeError("trava xact fora de transacao")
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s, %s)", [lock_class, lock_id])


def lock_on_demand() -> None:
    """A trava global do pedido sob demanda (RF-17): serializa os `POST`."""
    _xact_lock(LOCK_CLASS_ON_DEMAND, 0)


def lock_asset(asset_id: int) -> None:
    """A trava por ativo (RF-24): serializa a abertura e o fecho do mesmo ativo."""
    _xact_lock(LOCK_CLASS_ASSET, asset_id)


def timeout() -> timedelta:
    """O prazo do RF-18, `RUVOR_ON_DEMAND_TIMEOUT_MIN`."""
    prazo: timedelta = settings.RUVOR_ON_DEMAND_TIMEOUT
    return prazo


def expired_reason() -> str:
    """O motivo do pedido expirado: `expirado (N min)`, com o prazo em minutos."""
    return f"expirado ({int(timeout().total_seconds() // 60)} min)"


def is_expired(req: ComputeRequest, now: datetime) -> bool:
    """O pedido esta gravado aberto e foi feito ha mais do que o prazo."""
    return req.status in OPEN_STATUSES and now - req.requested_at > timeout()


def effective_status(req: ComputeRequest, now: datetime) -> str:
    """O estado que o `GET` devolve: `expired` para o aberto vencido, sem gravar (RF-18)."""
    if is_expired(req, now):
        return ComputeRequest.Status.EXPIRED.value
    return str(req.status)


def expire_stale(now: datetime) -> int:
    """Grava `expired` em todo pedido aberto vencido; devolve quantos."""
    return ComputeRequest.objects.filter(
        status__in=OPEN_STATUSES, requested_at__lt=now - timeout()
    ).update(
        status=ComputeRequest.Status.EXPIRED,
        reason=expired_reason(),
        error="",
        finished_at=now,
    )


def close_request(
    req: ComputeRequest, status: str, reason: str, error: str, now: datetime
) -> None:
    """Fecha o pedido com o desfecho dado -- ou `expired`, se venceu pelo relogio (RF-15).

    So escreve se o pedido ainda esta gravado aberto: `expired` e final, e o `POST` pode ter
    expirado o pedido entre a leitura de quem fecha e aqui. O objeto recebido fica com o
    que foi gravado.
    """
    if is_expired(req, now):
        status, reason, error = ComputeRequest.Status.EXPIRED, expired_reason(), ""
    written = ComputeRequest.objects.filter(pk=req.pk, status__in=OPEN_STATUSES).update(
        status=status, reason=reason, error=error, finished_at=now
    )
    if written:
        req.status, req.reason, req.error, req.finished_at = status, reason, error, now


def close_linked(run: RiskRun, now: datetime) -> int:
    """Fecha todo pedido aberto ligado a `run`, pelo `status` dela (RF-15); devolve quantos.

    `ok`/`partial` -> `done` "calculado"; `failed` -> `failed` "a execucao falhou"; o
    vencido pelo relogio -> `expired`. Chamado so dentro do fecho, com a execucao ja
    fechada: execucao ainda `running` e erro de quem chama.
    """
    if run.status in (RiskRun.Status.OK, RiskRun.Status.PARTIAL):
        status, reason, error = ComputeRequest.Status.DONE, REASON_CALCULATED, ""
    elif run.status == RiskRun.Status.FAILED:
        status, reason = ComputeRequest.Status.FAILED, REASON_RUN_FAILED
        error = f"risk_run {run.pk} fechou failed"
    else:
        raise ValueError(f"close_linked sobre risk_run {run.pk} em {run.status!r}")

    linked = ComputeRequest.objects.filter(risk_run=run, status__in=OPEN_STATUSES)
    expired = linked.filter(requested_at__lt=now - timeout()).update(
        status=ComputeRequest.Status.EXPIRED,
        reason=expired_reason(),
        error="",
        finished_at=now,
    )
    closed = linked.update(status=status, reason=reason, error=error, finished_at=now)
    return expired + closed


def enqueue_chain(request_id: int) -> None:
    """Enfileira a cadeia do pedido pelo nome registrado (RF-19): a `web` nunca importa um
    `tasks.py` que importe o motor. E o ponto que os testes substituem por duplo.

    Se o broker recusar, o pedido fecha `failed` "o broker recusou o pedido", com o erro --
    ou `expired`, se ja venceu (RF-15). Roda no `on_commit` do `POST`, fora da transacao
    dele: a escrita do fecho e em autocommit.
    """
    try:
        # o nome literal: o V-18 o le do codigo por `ast` e o confere no registro do `worker`
        app.send_task("apps.assets.tasks.calcular_sob_demanda", args=[request_id])
    except Exception as exc:
        logger.exception("o broker recusou o pedido %d", request_id)
        req = ComputeRequest.objects.filter(pk=request_id).first()
        if req is not None:
            close_request(
                req,
                ComputeRequest.Status.FAILED,
                REASON_BROKER_REFUSED,
                str(exc),
                timezone.now(),
            )
