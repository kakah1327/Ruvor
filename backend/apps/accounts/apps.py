"""Configuracao do app de contas."""

from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """O rotulo resultante e `accounts`, e e ele que nomeia as migrations."""

    name = "apps.accounts"

    def ready(self) -> None:
        # registra as extensoes de autenticacao do esquema OpenAPI (M4.2, RF-12)
        from apps.accounts import schema  # noqa: F401
