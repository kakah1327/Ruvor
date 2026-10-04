"""As rotas de `/api/v1/` (D-86), sem barra final.

Rota que nao casa aqui cai na view final de `config/urls.py`, que responde `not_found`.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from apps.api.views import (
    AssetDetailView,
    AssetDisclosuresView,
    AssetEventsView,
    AssetFundamentalsView,
    AssetListView,
    AssetMetricsView,
    AssetPricesView,
    AssetReturnsView,
    AssetRiskView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path("assets", AssetListView.as_view()),
    path("assets/<str:ticker>", AssetDetailView.as_view()),
    path("assets/<str:ticker>/prices", AssetPricesView.as_view()),
    path("assets/<str:ticker>/events", AssetEventsView.as_view()),
    path("assets/<str:ticker>/metrics", AssetMetricsView.as_view()),
    path("assets/<str:ticker>/risk", AssetRiskView.as_view()),
    path("assets/<str:ticker>/returns", AssetReturnsView.as_view()),
    path("assets/<str:ticker>/fundamentals", AssetFundamentalsView.as_view()),
    path("assets/<str:ticker>/disclosures", AssetDisclosuresView.as_view()),
]
