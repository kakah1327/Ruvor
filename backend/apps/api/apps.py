"""Configuracao do app da API HTTP."""

from __future__ import annotations

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """O rotulo resultante e `api`. Roda na `web`, que nao tem o motor (RF-10)."""

    name = "apps.api"
