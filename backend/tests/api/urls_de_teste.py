"""Rotas que so existem nos testes da API, pedidas por
`@pytest.mark.urls("tests.api.urls_de_teste")`.

Ficam **fora** de `/api/` (prefixo `test/`): sob `/api/`, a view final as engoliria. E vem
**antes** do `urlpatterns` de `config.urls`, que segue valendo por inteiro.
"""

from __future__ import annotations

from typing import Any, NoReturn

from django.urls import URLPattern, URLResolver, path
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.urls import urlpatterns as config_urlpatterns

# O texto que a view de erro leva na excecao: o corpo do 500 nao pode conte-lo.
SEGREDO = "detalhe-interno-que-nao-pode-vazar"


class SemPermissaoDeclarada(APIView):
    """Nao declara `permission_classes`: herda o padrao, `IsAuthenticated`."""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})


class ErroNaoPrevisto(APIView):
    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo

    def get(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise ValueError(SEGREDO)


class SoGet(APIView):
    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response({"ok": True})


class LeOCorpo(APIView):
    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response({"recebido": request.data})


urlpatterns: list[URLPattern | URLResolver] = [
    path("test/sem-permissao", SemPermissaoDeclarada.as_view()),
    path("test/erro", ErroNaoPrevisto.as_view()),
    path("test/so-get", SoGet.as_view()),
    path("test/corpo", LeOCorpo.as_view()),
    *config_urlpatterns,
]
