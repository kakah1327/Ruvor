"""As tarefas de coleta que o Beat agenda: o catalogo, os precos e a rotina diaria.

Molde de `config/tasks.py`: funcao com sublinhado, registrada com
`app.task(name=...)(funcao)` -- a funcao com sublinhado e o ponto que os testes
chamam e substituem; os tipos vem do `celery-types` (D-134). Os nomes de registro
sao contrato: sao eles que vao no `CELERY_BEAT_SCHEDULE`.

- `importar_ativos` e `importar_precos` sao cascas sobre os comandos de `manage.py`;
- `importar_precos` **captura o `CommandError`** e devolve o que aconteceu (RF-10): o
  `import_prices` levanta quando um ticker falha (D-54), e num encadeamento ingenuo um
  ticker ruim cancelaria o recalculo diario inteiro. Qualquer outra excecao propaga -- a
  corrente so nao segue se a ingestao nao chegou a rodar;
- `rotina_diaria` e o elo: o `beat_schedule` nao aceita `chain`, so nome de tarefa, entao
  a corrente presas -> preco -> metricas -> risco e montada aqui (D-69, RF-21 do M1.6a; o
  primeiro elo, `fechar_presas`, e do M1.5c, D-149). Todo elo depois do primeiro e
  **imutavel** (`.si()`): com `.s()`, o que o elo anterior devolveu chegaria como argumento
  posicional -- o `None` do `fechar_presas` no `importar_precos`, que nao recebe nenhum; o
  texto dele no `calcular_metricas`, idem; e no recalculo viraria `calculated_at_iso`, que o
  `datetime.fromisoformat` estouraria.

- `calcular_sob_demanda` e a cadeia de um pedido (RF-20 do M1.6a): o prazo, a coleta, as
  metricas e a abertura do risco, **chamadas como funcao, na mesma tarefa**, para que a
  falha de cada etapa feche o pedido `failed` com o motivo dela. O pedido so fecha `done`
  quando a `risk_run` fecha -- no fecho do M1.5, nao aqui --, salvo a serie curta, que a
  abertura fecha.

`call_command`, `_enqueue`, `run_import_prices`, `run_compute_metrics`, `_missing_models` e
`_abrir_execucao` sao chamados pelo nome global **deste** modulo -- e onde os testes os
substituem. O `_enqueue` e proprio, nao o de `apps.risk.tasks`.
"""

from __future__ import annotations

import logging
import time
from io import StringIO
from typing import Any

from celery import chain
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.analytics.compute import run_compute_metrics
from apps.analytics.tasks import calcular_metricas
from apps.api.models import ComputeRequest
from apps.api.ondemand import (
    OPEN_STATUSES,
    close_request,
    expired_reason,
    is_expired,
)

# Os motivos das tres etapas da cadeia, da lista fechada de `apps.api.ondemand` (RF-15). O
# `as` reexporta: os testes da cadeia os importam deste modulo.
from apps.api.ondemand import REASON_COLLECT_FAILED as REASON_COLLECT_FAILED
from apps.api.ondemand import REASON_METRICS_FAILED as REASON_METRICS_FAILED
from apps.api.ondemand import REASON_OPENING_FAILED as REASON_OPENING_FAILED
from apps.assets.prices import run_import_prices
from apps.assets.yahoo import YahooClient
from apps.risk.compute import MODELS, ModelsMissing
from apps.risk.config import DEFAULT_SEED
from apps.risk.tasks import (
    _abrir_execucao,
    _missing_models,
    fechar_presas,
    recalcular_cobertos,
)
from config.celery import app

logger = logging.getLogger(__name__)


def _enqueue(signature: Any) -> None:
    """Enfileira. E o ponto que os testes substituem: nenhum deles fala com o Redis."""
    signature.apply_async()


def _importar_ativos() -> str:
    """Roda o `import_assets` e devolve o que ele escreveu."""
    buf = StringIO()
    call_command("import_assets", stdout=buf)
    return buf.getvalue()


def _importar_precos() -> str:
    """Roda o `import_prices` e devolve o que ele escreveu; nunca levanta `CommandError`."""
    buf = StringIO()
    try:
        call_command("import_prices", stdout=buf)
    except CommandError as exc:
        return "FALHOU: " + str(exc)
    return buf.getvalue()


def _rotina_diaria() -> None:
    """Enfileira a corrente: as presas, os precos, as metricas e o recalculo dos cobertos."""
    _enqueue(
        chain(
            fechar_presas.si(),
            importar_precos.si(),
            calcular_metricas.si(),
            recalcular_cobertos.si(),
        )
    )


def _fail(req: ComputeRequest, reason: str, exc: Exception) -> None:
    """Fecha o pedido `failed` com o motivo da etapa -- ou `expired`, se venceu (RF-15)."""
    logger.exception("pedido %d: %s", req.pk, reason)
    close_request(
        req,
        ComputeRequest.Status.FAILED,
        reason,
        f"{type(exc).__name__}: {exc}",
        timezone.now(),
    )


def _calcular_sob_demanda(request_id: int) -> None:
    """A cadeia de um pedido (RF-20), literal na ordem: o prazo, a coleta, as metricas e a
    abertura do risco.

    O prazo e conferido **antes de coletar**: o pedido ja vencido e gravado `expired` e a
    cadeia para -- senao ela correria em paralelo com a de um pedido novo do mesmo ativo. A
    passagem a `running` e filtrada por `status=queued`: se o `POST` expirou o pedido no
    meio, nada muda e a cadeia para.

    Cada etapa que falha fecha o pedido `failed` com o motivo dela e o erro. A abertura e
    chamada **fora** de transacao propria, com o registry conferido antes (`ModelsMissing`
    fecha o pedido `failed`), o instante de agora, a semente padrao e os nove modelos. Com
    `opened` ou `already_running`, quem fecha o pedido e o fecho da execucao; com
    `short_series` ou `request_closed`, a abertura ja o fechou ou o achou fechado.
    """
    req = ComputeRequest.objects.select_related("asset").filter(pk=request_id).first()
    if req is None or req.status not in OPEN_STATUSES:
        logger.info("pedido %d ausente ou ja fechado: nada a fazer", request_id)
        return
    now = timezone.now()
    if is_expired(req, now):
        close_request(req, ComputeRequest.Status.EXPIRED, expired_reason(), "", now)
        logger.info("pedido %d vencido antes de comecar: %s", request_id, req.reason)
        return
    started = ComputeRequest.objects.filter(
        pk=request_id, status=ComputeRequest.Status.QUEUED
    ).update(status=ComputeRequest.Status.RUNNING)
    if started == 0:
        logger.info("pedido %d nao estava mais na fila: nada a fazer", request_id)
        return
    req.status = ComputeRequest.Status.RUNNING
    ticker = req.asset.ticker
    try:
        run_import_prices(YahooClient(timeout=30.0, sleep=time.sleep), [ticker])
    except Exception as exc:
        _fail(req, REASON_COLLECT_FAILED, exc)
        return
    try:
        run_compute_metrics([ticker])
    except Exception as exc:
        _fail(req, REASON_METRICS_FAILED, exc)
        return
    try:
        missing = _missing_models(list(MODELS))  # o mesmo que o `enqueue_compute`
        if missing:
            raise ModelsMissing(missing)
        out = _abrir_execucao(
            ticker,
            timezone.now().isoformat(),
            DEFAULT_SEED,
            list(MODELS),
            request_id=request_id,
        )
    except Exception as exc:
        _fail(req, REASON_OPENING_FAILED, exc)
        return
    logger.info(
        "pedido %d %s: %s (run=%s, pregoes=%s)",
        request_id,
        ticker,
        out["outcome"],
        out["run_id"],
        out["sessions"],
    )


# Registro sem a sintaxe de decorador, como em `config/tasks.py`.
importar_ativos = app.task(name="apps.assets.tasks.importar_ativos")(_importar_ativos)
importar_precos = app.task(name="apps.assets.tasks.importar_precos")(_importar_precos)
rotina_diaria = app.task(name="apps.assets.tasks.rotina_diaria")(_rotina_diaria)
calcular_sob_demanda = app.task(name="apps.assets.tasks.calcular_sob_demanda")(
    _calcular_sob_demanda
)
