"""O erro de regra dos servicos de conta (M2.1a, RF-28).

Sem status HTTP e sem importar `rest_framework`: a fase 1 nao tem rota. Na fase 2, as views
traduzem o `code` para o status da lista do RF-27 -- `ApiError`, ou `Throttled` no caso de
`too_many_requests`.
"""

from __future__ import annotations

from typing import Any


class AccountError(Exception):
    """Erro de regra com `code` estavel, `message` em portugues e `details` sempre presente."""

    def __init__(
        self, code: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, Any] = details if details is not None else {}
