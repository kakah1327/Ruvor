"""As views da API. Nesta etapa, so a view final de `/api/`.

Este modulo nao importa o motor, nem direta nem indiretamente (RF-10): nada de `engine`,
`pandas`, `apps.risk.tasks`, `apps.risk.compute`, `apps.risk.snapshots` ou
`apps.assets.tasks`. O V-10 (`tests/api/test_sem_motor.py`) confere.
"""

from __future__ import annotations

from typing import Any, NoReturn

from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView


class ApiNotFound(APIView):
    """A view final de `/api/` (D-86): rota inexistente responde `not_found` no formato
    da API, com `DEBUG` ligado ou nao — nao depende do `handler404` do Django, que o
    `DEBUG` ligado ignora.

    Levanta `NotFound` em todo metodo de `http_method_names`, para que um metodo sem
    tratador nao vire 405 numa rota que nao existe.
    """

    permission_classes = [AllowAny]  # noqa: RUF012 -- a forma do DRF; o V-09 le do corpo

    def get(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def post(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def put(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    def head(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound

    # O mesmo `ignore` dos stubs do DRF no `APIView.options`: o `View` do Django tipa o
    # pedido como `HttpRequest`, e o DRF entrega o `Request` dele.
    def options(  # type: ignore[override]
        self, request: Request, *args: Any, **kwargs: Any
    ) -> NoReturn:
        raise NotFound

    def trace(self, request: Request, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotFound
