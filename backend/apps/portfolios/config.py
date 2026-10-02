"""Constantes e limites da carteira (M2.2a, RF-04, RF-13, RF-14), num modulo so.

Django puro: a `web` cria a execucao e nao tem o motor. Por isso `PORTFOLIO_MODELS` e uma
**copia** da tupla `MODELS` de `apps/risk/compute.py`, na mesma ordem -- aquele modulo importa o
motor no topo. O teste de paridade, no `worker`, compara as duas (V-22).

As duas variaveis sao lidas na **chamada**, nao na importacao: o `override_settings` dos testes
vale.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings

PORTFOLIO_MODELS: tuple[str, ...] = (
    "caviar",
    "egarch",
    "garch_1_1",
    "garchnet",
    "gru",
    "historical",
    "lstm",
    "monte_carlo",
    "parametric",
)

# As classes de trava consultiva, na faixa da `apps/api/ondemand.py` (7101 e 7102).
LOCK_CLASS_REQUESTS = 7103  # pg_advisory_xact_lock(7103, 0): os pedidos de risco
LOCK_CLASS_RUN = 7104  # pg_advisory_xact_lock(7104, run_id): a execucao


def compute_max() -> int:
    """Quantas execucoes de carteira `running`, em todas as organizacoes, antes do 429."""
    value: int = settings.RUVOR_PORTFOLIO_COMPUTE_MAX
    return value


def timeout() -> timedelta:
    """O prazo depois do qual uma execucao `running` deixa de segurar o pedido."""
    value: timedelta = settings.RUVOR_PORTFOLIO_TIMEOUT
    return value
