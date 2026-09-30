"""A varredura das execucoes presas (M1.5c, D-149): fecha pela regra do fecho a `risk_run`
que ficou `running` alem do prazo.

**Presa e a `running` velha** (RF-01): `calculated_at` anterior a `now - older_than`. A
listagem e avaliada numa lista antes do laco, e uma excecao nela propaga (RF-03): sem a
lista, nao ha o que relatar.

**Cada execucao e fechada sob a trava por ativo**, a mesma da abertura, do fecho do `chord`
e da escrita da tarefa por modelo, e a linha e **relida depois da trava**: entre a listagem
e a trava, outro caminho pode te-la fechado. Fechada, entra no relatorio como `ja fechada`,
com o status gravado -- inclusive com `dry_run`, que sem a releitura diria `fecharia`. A
contagem sai de `count_results`, sob a trava, para toda execucao relida; o `close_run`
conta de novo sob a mesma trava, e os numeros batem.

**A regra e a do fecho** (RF-02): `close_run` escreve o status e o fim so se a linha ainda
esta `running` (D-150) e, quando escreveu, `close_linked` fecha os pedidos sob demanda
ligados. **A falha de uma execucao nao para as outras** (RF-03): vai para o log com o id,
entra em `failed`, e o laco segue.

`close_run`, `count_results` e `_list_stale` sao chamados pelo nome global **deste** modulo,
e `_after_stale_listing` e o ponto de desvio entre a listagem e a trava: e aqui que os
testes os substituem. Este modulo nao importa o motor, mas `apps.risk.compute` importa: a
varredura so roda no `worker`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction

from apps.api.ondemand import close_linked, lock_asset
from apps.risk.compute import close_run, count_results, status_for
from apps.risk.models import RiskRun

logger = logging.getLogger(__name__)

NO_STALE = "nenhuma execução presa"


@dataclass(frozen=True)
class StaleRun:
    """Uma execucao listada como presa e o que a varredura fez com ela."""

    run_id: int
    ticker: str
    calculated_at: datetime
    written: int
    expected: int
    status: (
        str  # o escrito; com dry_run, o que escreveria; com already_closed, o gravado
    )
    already_closed: bool


@dataclass(frozen=True)
class StaleReport:
    """O relatorio da varredura: uma linha por execucao listada e o total."""

    runs: list[StaleRun]
    failed: list[tuple[int, str]]  # (run_id, "Tipo: mensagem")
    dry_run: bool

    def render(self) -> str:
        if not self.runs and not self.failed:
            return NO_STALE
        lines: list[str] = []
        for r in self.runs:
            head = f"{r.ticker:<12} run={r.run_id} {r.calculated_at:%Y-%m-%d %H:%M}"
            if r.already_closed:
                lines.append(f"{head} ja fechada ({r.status})")
            elif self.dry_run:
                lines.append(f"{head} {r.written}/{r.expected} fecharia {r.status}")
            else:
                lines.append(f"{head} {r.written}/{r.expected} {r.status}")
        for run_id, error in self.failed:
            lines.append(f"FALHOU run={run_id}: {error}")
        closed = sum(1 for r in self.runs if not r.already_closed)
        already = sum(1 for r in self.runs if r.already_closed)
        verb = "fechariam" if self.dry_run else "fechadas"
        lines.append(
            f"total: {closed} {verb}, {already} ja fechadas, {len(self.failed)} falharam"
        )
        return "\n".join(lines)


def _list_stale(now: datetime, older_than: timedelta) -> list[RiskRun]:
    """As presas, avaliadas numa lista: `running` com `calculated_at < now - older_than`."""
    return list(
        RiskRun.objects.filter(
            status=RiskRun.Status.RUNNING, calculated_at__lt=now - older_than
        )
        .select_related("asset")
        .order_by("calculated_at")
    )


def _after_stale_listing() -> None:
    """Ponto de desvio: depois da listagem, antes da trava de cada execucao. Nao faz nada; e
    chamado pelo nome global deste modulo."""


def _close_one(listed: RiskRun, now: datetime, *, dry_run: bool) -> StaleRun:
    """Fecha uma execucao listada, sob a trava por ativo, relendo a linha depois dela."""
    with transaction.atomic():
        lock_asset(listed.asset_id)
        run = RiskRun.objects.get(pk=listed.pk)
        expected, written, with_error = count_results(run)

        def entry(status: str, already_closed: bool) -> StaleRun:
            return StaleRun(
                run_id=listed.pk,
                ticker=listed.asset.ticker,
                calculated_at=listed.calculated_at,
                written=written,
                expected=expected,
                status=str(status),
                already_closed=already_closed,
            )

        if run.status != RiskRun.Status.RUNNING:
            return entry(run.status, True)
        if dry_run:
            return entry(status_for(expected, written, with_error), False)
        status = close_run(run, now)
        if status is None:
            return entry(run.status, True)
        close_linked(run, now)
        return entry(status, False)


def close_stale_runs(
    now: datetime, older_than: timedelta, *, dry_run: bool = False
) -> StaleReport:
    """Fecha pela regra toda execucao `running` com `calculated_at < now - older_than`
    (RF-01 a RF-03). Com `dry_run`, so relata o que escreveria. Levanta so se a listagem
    falhar; a falha de uma execucao entra em `failed`, e as outras seguem."""
    listed = _list_stale(now, older_than)
    runs: list[StaleRun] = []
    failed: list[tuple[int, str]] = []
    for run in listed:
        _after_stale_listing()
        try:
            runs.append(_close_one(run, now, dry_run=dry_run))
        except Exception as exc:
            logger.exception("execucao %d: a varredura nao a fechou", run.pk)
            failed.append((run.pk, f"{type(exc).__name__}: {exc}"))
    return StaleReport(runs=runs, failed=failed, dry_run=dry_run)
