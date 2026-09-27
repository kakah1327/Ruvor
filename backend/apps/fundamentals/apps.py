"""Configuracao do app de fundamentos."""

from __future__ import annotations

from django.apps import AppConfig


class FundamentalsConfig(AppConfig):
    """O rotulo e `fundamentals`, e e ele que nomeia as migrations."""

    name = "apps.fundamentals"
    label = "fundamentals"
    default_auto_field = "django.db.models.BigAutoField"
