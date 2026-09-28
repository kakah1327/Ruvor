"""O bloqueio de entrada por (e-mail, IP) (M2.1a, RF-22b, D-106).

Cinco falhas do mesmo par numa janela de quinze minutos, contada da primeira falha,
bloqueiam o par por quinze minutos, contados da quinta. A chave e o par, e nao o e-mail
sozinho, para que ninguem trave, de outro endereco, a conta alheia.

O contador mora no cache do Django -- o Redis, num banco proprio (RF-22). Cache nao e
transacional: quem chama nao o poe dentro de `atomic`.
"""

from __future__ import annotations

import math
import time

from django.core.cache import cache

MAX_FAILURES = 5
WINDOW_SECONDS = 900
BLOCK_SECONDS = 900


def _falhas(email: str, ip: str | None) -> str:
    return f"login-falhas:{email}:{ip or '-'}"


def _bloqueio(email: str, ip: str | None) -> str:
    return f"login-bloqueio:{email}:{ip or '-'}"


def blocked_for(email: str, ip: str | None) -> int:
    """Segundos que faltam para o par sair do bloqueio; 0 quando esta livre."""
    fim = cache.get(_bloqueio(email, ip))
    if fim is None:
        return 0
    return max(0, math.ceil(float(fim) - time.time()))


def register_failure(email: str, ip: str | None) -> None:
    chave = _falhas(email, ip)
    cache.add(chave, 0, WINDOW_SECONDS)
    try:
        falhas = cache.incr(chave)
    except ValueError:
        # a chave venceu entre o `add` e o `incr`: e a primeira falha de uma janela nova
        cache.set(chave, 1, WINDOW_SECONDS)
        falhas = 1
    if falhas >= MAX_FAILURES:
        cache.set(_bloqueio(email, ip), time.time() + BLOCK_SECONDS, BLOCK_SECONDS)
        cache.delete(chave)


def clear(email: str, ip: str | None) -> None:
    cache.delete(_falhas(email, ip))
