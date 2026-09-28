"""Rotas que so existem nos testes da `identidade` (M4.2), pedidas por
`@pytest.mark.urls("tests.accounts.urls_de_teste")`.

Ficam **fora** de `/api/` (prefixo `test/`): sob `/api/`, a view final as engoliria, e os testes
de declaracao sobre o resolvedor as veriam. Vem **antes** do `urlpatterns` de `config.urls`, que
segue valendo por inteiro.
"""

from __future__ import annotations

from typing import Any, ClassVar

from django.urls import URLPattern, URLResolver, path
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.tenancy import current_organization_id
from config.urls import urlpatterns as config_urlpatterns


class OrganizacaoDoContexto(APIView):
    """Devolve o `organization_id` do contexto, como a view o ve (V-17)."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF
    api_key_scope: ClassVar[str | None] = "read"

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response({"organization_id": current_organization_id()})


class SemEscopo(APIView):
    """Nao declara `api_key_scope`: e onde se prova que o padrao e recusar (RF-07)."""

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})


urlpatterns: list[URLPattern | URLResolver] = [
    path("test/organizacao", OrganizacaoDoContexto.as_view()),
    path("test/sem-escopo", SemEscopo.as_view()),
    *config_urlpatterns,
]
