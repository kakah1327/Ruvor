"""O erro de regra da carteira (M2.2a), no molde de `AccountError` (`apps/accounts/errors.py`).

Django puro, sem DRF (RF-20): a view traduz o `code` para o status HTTP pelo `STATUS_BY_CODE` de
`apps/portfolios/views.py`.
"""

from __future__ import annotations

from typing import Any


class PortfolioError(Exception):
    """Erro de regra com `code` estavel, `message` em portugues e `details` sempre presente."""

    def __init__(
        self, code: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details: dict[str, Any] = details if details is not None else {}
