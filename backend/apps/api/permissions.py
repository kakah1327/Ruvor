"""A permissao mista do `/risk` (M2.1b, RF-01; D-140).

`apps.accounts.permissions` importa `apps.api.errors`, que nao importa views nem permissoes:
o import abaixo nao fecha ciclo.
"""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.permissions import AccountReady


class ReadOpenWriteAccountReady(BasePermission):
    """Leitura aberta; escrita so com conta pronta (D-140).

    Metodo seguro -> True. Qualquer outro -> `AccountReady`: False sem login (o DRF responde
    401 `not_authenticated`), `password_change_required` com a senha provisoria por trocar.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return AccountReady().has_permission(request, view)
