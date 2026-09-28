"""O esquema OpenAPI da API (M4.2, RF-12).

- `SessionScheme` e `ApiKeyScheme`: as duas classes de autenticacao no esquema, como
  `sessionAuth` (o cookie `sessionid`) e `apiKeyAuth` (HTTP `bearer`). Registradas pelo import no
  `ready()` de `apps/accounts/apps.py`.
- `ApiErrorSerializer`: o erro da D-86, so descricao, o componente `ApiError`.
- `AutoSchema`, o `DEFAULT_SCHEMA_CLASS`: toda operacao ganha a resposta `default` apontando para
  o `ApiError`, e so a view com `api_key_scope = "read"` lista o `apiKeyAuth` -- o
  drf-spectacular, sozinho, listaria os dois autenticadores do padrao em toda operacao.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema as SpectacularAutoSchema
from rest_framework import serializers

API_KEY_SCHEME = "apiKeyAuth"

# Os `type: ignore[no-untyped-call]` abaixo sao do drf-spectacular 0.30.0, que nao anota o
# `__init_subclass__` das extensoes nem o `_get_response_for_code`.


class SessionScheme(OpenApiAuthenticationExtension):  # type: ignore[no-untyped-call]
    """A sessao do Django. Prioridade acima da do drf-spectacular, que casa as subclasses da
    `SessionAuthentication` do DRF com o nome `cookieAuth`."""

    target_class = "apps.accounts.authentication.SessionAuthentication"
    name = "sessionAuth"
    priority = 1

    def get_security_definition(self, auto_schema: Any) -> dict[str, str]:
        return {"type": "apiKey", "in": "cookie", "name": settings.SESSION_COOKIE_NAME}


class ApiKeyScheme(OpenApiAuthenticationExtension):  # type: ignore[no-untyped-call]
    """A chave de API, `Authorization: Bearer rvr_...` (RF-06)."""

    target_class = "apps.accounts.authentication.ApiKeyAuthentication"
    name = API_KEY_SCHEME

    def get_security_definition(self, auto_schema: Any) -> dict[str, str]:
        return {"type": "http", "scheme": "bearer"}


class ApiErrorDetailSerializer(serializers.Serializer[None]):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField()


class ApiErrorSerializer(serializers.Serializer[None]):
    """O corpo de erro da D-86, `{error: {code, message, details}}`. Os codigos de cada rota
    vivem nas specs: uma lista aqui seria copia sem fonte."""

    error = ApiErrorDetailSerializer()


class AutoSchema(SpectacularAutoSchema):
    def get_auth(self) -> list[dict[str, list[str]]]:
        auths: list[dict[str, list[str]]] = super().get_auth()
        if getattr(self.view, "api_key_scope", None) != "read":
            auths = [a for a in auths if API_KEY_SCHEME not in a]
        return auths

    def _get_response_bodies(self, direction: str = "response") -> dict[str, Any]:
        responses: dict[str, Any] = super()._get_response_bodies(direction)  # type: ignore[arg-type]
        if direction == "response":
            responses["default"] = self._get_response_for_code(  # type: ignore[no-untyped-call]
                ApiErrorSerializer, "default", direction=direction
            )
        return responses
