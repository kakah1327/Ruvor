"""As rotas de `/api/v1/` (D-86). As de negocio entram a partir da T7 do M1.6a.

Rota que nao casa aqui cai na view final de `config/urls.py`, que responde `not_found`.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver

urlpatterns: list[URLPattern | URLResolver] = []
