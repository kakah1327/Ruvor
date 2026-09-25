"""Configuracao do Django. Tudo vem de variaveis RUVOR_*."""

from __future__ import annotations

import os
from pathlib import Path

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"variavel de ambiente obrigatoria ausente: {name}")
    return value


SECRET_KEY = _required("RUVOR_SECRET_KEY")
DEBUG = os.environ.get("RUVOR_DEBUG", "false").lower() in {"1", "true", "yes"}


def _split_hosts(valor: str) -> list[str]:
    """Separa por virgula, tira o espaco em volta de cada item e descarta vazios."""
    return [parte.strip() for parte in valor.split(",") if parte.strip()]


ALLOWED_HOSTS = _split_hosts(os.environ.get("RUVOR_ALLOWED_HOSTS", ""))

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "apps.accounts",
    "apps.assets",
    "apps.analytics",
    "apps.risk",
]

AUTH_USER_MODEL = "accounts.User"

# MIDDLEWARE nao ganha AuthenticationMiddleware: a exigencia (auth.E013) so dispara com
# LoginRequiredMiddleware presente, e ele nao esta. Sessao e autenticacao de requisicao
# sao do M2.1.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES: dict[str, dict[str, str]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": _required("RUVOR_DB_HOST"),
        "PORT": _required("RUVOR_DB_PORT"),
        "NAME": _required("RUVOR_DB_NAME"),
        "USER": _required("RUVOR_DB_USER"),
        "PASSWORD": _required("RUVOR_DB_PASSWORD"),
    }
}

# Fila. CELERY_TASK_ALWAYS_EAGER nao e definido de proposito: o modo sincrono fica
# desligado, senao a tarefa de fumaca rodaria no proprio web e nao provaria nada.
CELERY_BROKER_URL = _required("RUVOR_REDIS_URL")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL


def _cron(name: str, default: str) -> crontab:
    # `or`, nao o segundo argumento do get: o compose passa a variavel VAZIA quando o .env
    # nao a define (ver "A infraestrutura"), e vazio tem de valer o padrao
    fields = (os.environ.get(name) or default).split()
    if len(fields) != 5:
        raise ImproperlyConfigured(
            f"{name}: esperados 5 campos de cron, veio {len(fields)}"
        )
    minute, hour, day_of_month, month_of_year, day_of_week = fields
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )


CELERY_BEAT_SCHEDULE = {
    "catalogo": {
        "task": "apps.assets.tasks.importar_ativos",
        "schedule": _cron("RUVOR_BEAT_ASSETS_CRON", "0 7 * * 1"),
    },
    "precos": {
        "task": "apps.assets.tasks.rotina_diaria",
        "schedule": _cron("RUVOR_BEAT_PRICES_CRON", "30 19 * * 1-5"),
    },
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
