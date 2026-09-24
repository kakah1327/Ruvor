"""Configuracao do app de metricas de comportamento."""

from __future__ import annotations

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """O rotulo resultante e `analytics`, e e ele que nomeia as migrations."""

    name = "apps.analytics"
