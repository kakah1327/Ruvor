"""As travas consultivas da carteira (M2.2a, RF-13, RF-14), na forma de dois inteiros de
`apps/api/ondemand.py`. Django puro: a web e o `worker` usam as duas.

Ambas sao `pg_advisory_xact_lock`: soltam sozinhas no fim da transacao, e fora de uma levantam --
uma trava que nao segura nada nao pode passar em silencio.
"""

from __future__ import annotations

from django.db import connection

from apps.portfolios import config as portfolio_config


def _xact_lock(lock_class: int, lock_id: int) -> None:
    if not connection.in_atomic_block:
        raise RuntimeError("trava xact fora de transacao")
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s, %s)", [lock_class, lock_id])


def lock_requests() -> None:
    """A trava dos pedidos de risco de carteira (RF-13): serializa os `POST`."""
    _xact_lock(portfolio_config.LOCK_CLASS_REQUESTS, 0)


def lock_run(run_id: int) -> None:
    """A trava da execucao (RF-14): serializa a abertura, a escrita por modelo e o fecho."""
    _xact_lock(portfolio_config.LOCK_CLASS_RUN, run_id)
