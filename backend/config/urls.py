from django.urls import URLPattern, URLResolver, include, path, re_path

from apps.api.views import ApiNotFound
from config.views import health

urlpatterns: list[URLPattern | URLResolver] = [
    path("health", health),
    # As rotas de conta (M2.1a) antes das da API de leitura: prefixos distintos, mesma raiz.
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.api.urls")),
    # A carteira (M2.2a): prefixo proprio, `portfolios`, na mesma raiz.
    path("api/v1/", include("apps.portfolios.urls")),
    # A view final da API (D-86): depois de `/api/v1/`, pega o resto de `/api/` e
    # responde `not_found` no formato da API. Fora de `/api/`, o Django nao muda.
    re_path(r"^api/", ApiNotFound.as_view()),
]
