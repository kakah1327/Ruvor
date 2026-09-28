"""A autenticacao da API: a sessao do Django, com CSRF (M2.1a, RF-03; D-100).

A mae, a `SessionAuthentication` do DRF, so exige CSRF de quem **esta** logado: para anonimo
ou inativo, `authenticate` devolve `None` antes do `enforce_csrf`. Por isso o `signup` e o
`login` chamam o `enforce_csrf` explicitamente (RF-04). Esta subclasse muda duas coisas:

- `authenticate_header` devolve `"Session"`. Sem cabecalho, a `APIView` rebaixa o
  `NotAuthenticated` a 403; com ele, a resposta e 401 com `WWW-Authenticate: Session`;
- a falha de CSRF sai como `ApiError(403, "csrf_failed")`, e nao como o `PermissionDenied`
  da mae, que o tratador de `apps/api/errors.py` mapearia para `permission_denied`.
"""

from __future__ import annotations

from rest_framework import authentication, exceptions
from rest_framework.request import Request


class SessionAuthentication(authentication.SessionAuthentication):
    def authenticate_header(self, request: Request) -> str:
        return "Session"

    def enforce_csrf(self, request: Request) -> None:
        # O import fica aqui, e nao no topo, de proposito: o DRF importa esta classe no meio
        # do import de `rest_framework.views` (`views.py:18` importa `rest_framework.schemas`,
        # e `schemas/__init__.py:32` avalia `DEFAULT_AUTHENTICATION_CLASSES`), antes de
        # `set_rollback` existir. `apps.api.errors` importa `set_rollback` de
        # `rest_framework.views` no topo: importado aqui em cima, o ciclo quebraria o
        # primeiro `import rest_framework.views` do processo.
        from apps.api.errors import ApiError

        try:
            super().enforce_csrf(request)
        except exceptions.PermissionDenied as exc:
            raise ApiError(
                403,
                "csrf_failed",
                "Falha na verificação CSRF. Recarregue a página e tente de novo.",
                {},
            ) from exc
