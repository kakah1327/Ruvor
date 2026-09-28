"""A gravacao do evento de acesso (M2.1a, RF-23 e RF-24).

Quem chama grava o evento **dentro** da mesma transacao da mudanca que ele descreve; so
`login_failed` e `login_throttled`, que nao mudam nada, gravam sozinhos.
"""

from __future__ import annotations

from typing import Any

from apps.accounts.models import AccessEvent, Organization, User


def record(
    kind: str,
    *,
    email: str,
    actor: User | None = None,
    target: User | None = None,
    organization: Organization | None = None,
    ip: str | None = None,
    details: dict[str, Any] | None = None,
) -> AccessEvent:
    return AccessEvent.objects.create(
        kind=kind,
        email=email,
        actor=actor,
        target=target,
        organization=organization,
        ip=ip,
        details=details if details is not None else {},
    )
