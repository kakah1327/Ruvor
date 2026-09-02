"""Configuracao do Django. Tudo vem de variaveis RUVOR_*; nao ha banco neste bloco (F4)."""

from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"variavel de ambiente obrigatoria ausente: {name}")
    return value


SECRET_KEY = _required("RUVOR_SECRET_KEY")
DEBUG = os.environ.get("RUVOR_DEBUG", "false").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [h for h in os.environ.get("RUVOR_ALLOWED_HOSTS", "").split(",") if h]

INSTALLED_APPS = ["rest_framework"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Vazio de proposito: F2b-02. O Django preenche com o backend "dummy", que levanta
# ImproperlyConfigured em qualquer acesso — e o teste da T3 prova isso.
DATABASES: dict[str, dict[str, str]] = {}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
