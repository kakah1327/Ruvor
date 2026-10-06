"""Configuracao do app de retorno (M5.1)."""

from __future__ import annotations

from django.apps import AppConfig


class ReturnsConfig(AppConfig):
    """O rotulo resultante e `returns`, e e ele que nomeia as migrations."""

    name = "apps.returns"
