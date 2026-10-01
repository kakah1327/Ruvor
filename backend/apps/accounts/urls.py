"""As rotas de conta sob `/api/v1/` (M2.1a, fase 2), sem barra final (D-86).

Incluidas por `config/urls.py` antes das de `apps/api/urls.py`; o que nao casa aqui nem la
cai na view final da API.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from apps.accounts.views import (
    ApiKeysView,
    ApiKeyView,
    CsrfView,
    LoginView,
    LogoutView,
    MeView,
    OrganizationUsersView,
    OrganizationUserView,
    PasswordView,
    ReportCsvView,
    ReportJsonView,
    ReportsView,
    ReportView,
    SchemaView,
    SignupView,
    TemporaryPasswordView,
)

urlpatterns: list[URLPattern | URLResolver] = [
    path("auth/csrf", CsrfView.as_view()),
    path("auth/signup", SignupView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
    path("auth/password", PasswordView.as_view()),
    path("organization/users", OrganizationUsersView.as_view()),
    path("organization/users/<str:email>", OrganizationUserView.as_view()),
    path(
        "organization/users/<str:email>/temporary-password",
        TemporaryPasswordView.as_view(),
    ),
    path("api-keys", ApiKeysView.as_view()),
    path("api-keys/<str:prefix>", ApiKeyView.as_view()),
    path("reports", ReportsView.as_view()),
    path("reports/<str:id>", ReportView.as_view()),
    path("reports/<str:id>/json", ReportJsonView.as_view()),
    path("reports/<str:id>/csv", ReportCsvView.as_view()),
    path("schema", SchemaView.as_view()),
]
