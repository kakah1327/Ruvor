"""Configuracao do app de risco."""

from __future__ import annotations

from django.apps import AppConfig


class RiskConfig(AppConfig):
    """O rotulo resultante e `risk`, e e ele que nomeia as migrations."""

    name = "apps.risk"
