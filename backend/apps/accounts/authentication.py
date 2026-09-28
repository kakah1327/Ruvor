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

import hmac
import re
from datetime import timedelta

from django.utils import timezone
from rest_framework import authentication, exceptions
from rest_framework.request import Request

from apps.accounts.models import ApiKey, User
from apps.accounts.tenancy import set_organization_id

# `rvr_<prefix>_<corpo>` (M4.2, RF-02)
_TOKEN = re.compile(r"rvr_([0-9a-f]{8})_([A-Za-z0-9_-]{43})")
_LAST_USED_EVERY = timedelta(seconds=60)
INVALID_API_KEY_MESSAGE = "Chave de API inválida."


class SessionAuthentication(authentication.SessionAuthentication):
    def authenticate(self, request: Request) -> tuple[User, None] | None:
        """O da mae; autenticou, poe a organizacao da conta no contexto (M4.2, RF-13)."""
        result = super().authenticate(request)
        if result is not None:
            set_organization_id(result[0].organization_id)
        return result

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


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """A chave pessoal de leitura, por `Authorization: Bearer <segredo>` (M4.2, RF-06; D-108).

    Sem o cabecalho, ou com outro esquema, nao e dela: `None`. Com `Bearer`, **qualquer** falha
    -- formato, `prefix` inexistente, hash, revogada, dona inativa -- e o mesmo 401
    `invalid_api_key`. A busca pelo `prefix` e a unica consulta sem escopo de `ApiKey` (RF-13):
    a organizacao so e conhecida depois de achar a chave. Nao exige CSRF: nao e cookie.
    """

    def authenticate(self, request: Request) -> tuple[User, ApiKey] | None:
        header = request.META.get("HTTP_AUTHORIZATION", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer":
            return None
        match = _TOKEN.fullmatch(token.strip())
        if match is None:
            raise exceptions.AuthenticationFailed(INVALID_API_KEY_MESSAGE)
        key = (
            ApiKey.unscoped.select_related("user").filter(prefix=match.group(1)).first()
        )
        if (
            key is None
            or key.revoked_at is not None
            or not hmac.compare_digest(key.secret_hash, _hash(token.strip()))
            or not key.user.is_active
        ):
            raise exceptions.AuthenticationFailed(INVALID_API_KEY_MESSAGE)
        user = key.user
        if user.must_change_password:
            # o import no metodo: ver `SessionAuthentication.enforce_csrf`
            from apps.api.errors import ApiError

            raise ApiError(
                403,
                "password_change_required",
                "Troque a senha provisória para continuar.",
                {},
            )
        agora = timezone.now()
        if key.last_used_at is None or agora - key.last_used_at > _LAST_USED_EVERY:
            key.last_used_at = agora
            key.save(update_fields=["last_used_at"])  # o gerente base: sem contexto
        set_organization_id(user.organization_id)
        return user, key


def _hash(secret: str) -> str:
    # o mesmo de `services._secret_hash`; importar `services` aqui traria o modulo inteiro
    # para o meio do import do DRF
    import hashlib

    return hashlib.sha256(secret.encode()).hexdigest()
