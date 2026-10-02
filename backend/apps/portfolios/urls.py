"""As rotas da carteira sob `/api/v1/` (M2.2a), sem barra final (D-86).

Incluidas por `config/urls.py` depois das de conta e das de leitura; o que nao casa em nenhuma
cai na view final da API.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from apps.portfolios.views import PortfolioHoldingsView, PortfoliosView, PortfolioView

urlpatterns: list[URLPattern | URLResolver] = [
    path("portfolios", PortfoliosView.as_view()),
    path("portfolios/<str:id>", PortfolioView.as_view()),
    path("portfolios/<str:id>/holdings", PortfolioHoldingsView.as_view()),
]
