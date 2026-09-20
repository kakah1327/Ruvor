"""Configuracao do app de ativos."""

from __future__ import annotations

from django.apps import AppConfig


class AssetsConfig(AppConfig):
    """O rotulo resultante e `assets`, e e ele que nomeia as migrations."""

    name = "apps.assets"
