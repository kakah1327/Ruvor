"""A taxa de toda rota da API (M4.2, RF-08).

`ApiRateThrottle` e a `DEFAULT_THROTTLE_CLASSES`: o escopo e a identidade saem de quem fez o
pedido -- a chave pelo `prefix`, a sessao pelo usuario, o anonimo pelo IP. As views com
`throttle_classes` proprias (`signup`, `login`, `password`, com o `AuthRateThrottle`) nao passam
por aqui: o DRF usa a declarada no lugar do padrao.

**Este modulo e importado no meio do import de `rest_framework.views`** (o `throttle_classes`
padrao e avaliado antes de `APIView` existir): importar `APIView`, `apps.api.views` ou
`apps.accounts.views` no topo da `ImportError`. `Request` e `APIView` so sob `TYPE_CHECKING`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.throttling import SimpleRateThrottle

from apps.accounts.models import ApiKey

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class ApiRateThrottle(SimpleRateThrottle):
    """A taxa por chave, por usuario ou por IP, com escopo escolhido a cada pedido."""

    ident: str

    def __init__(self) -> None:
        pass  # o escopo depende do pedido; o `SimpleRateThrottle.__init__` exigiria um fixo

    def allow_request(self, request: Request, view: APIView) -> bool:
        self.scope, self.ident = self._who(request)
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {"scope": self.scope, "ident": self.ident}

    def _who(self, request: Request) -> tuple[str, str]:
        if isinstance(request.auth, ApiKey):
            return "api_key", f"key:{request.auth.prefix}"
        if request.user.is_authenticated:
            return "user", f"user:{request.user.pk}"
        return "anon", f"anon:{self.get_ident(request)}"
