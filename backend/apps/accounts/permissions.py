"""A permissao de conta pronta (M2.1a, RF-29; D-102).

**Toda view que exige conta declara `AccountReady`**; `IsAuthenticated` puro, so as de `me`,
`password` e `logout`, que servem a quem ainda tem senha provisoria (RF-07). Um teste
(`tests/accounts/test_permissao_de_conta.py`) reprova `IsAuthenticated` fora dessas tres.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.api.errors import ApiError


class AccountReady(BasePermission):
    """Autenticado e sem senha provisoria por trocar.

    Sem login, devolve `False`: havendo autenticador, o DRF transforma isso em
    `NotAuthenticated`, 401. Com a senha por trocar, **levanta** `password_change_required`:
    devolver `False` viraria `permission_denied`.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if user is None or not user.is_authenticated:
            return False
        if getattr(user, "must_change_password", False):
            raise ApiError(
                403,
                "password_change_required",
                "Troque a senha provisória para continuar.",
                {},
            )
        return True
