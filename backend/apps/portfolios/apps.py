"""Configuracao do app de carteiras."""

from __future__ import annotations

from django.apps import AppConfig


class PortfoliosConfig(AppConfig):
    """O rotulo resultante e `portfolios`, e e ele que nomeia as migrations."""

    name = "apps.portfolios"
