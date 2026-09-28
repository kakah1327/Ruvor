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
    "django.contrib.sessions",
    "rest_framework",
    "apps.accounts",
    "apps.assets",
    "apps.analytics",
    "apps.risk",
    "apps.fundamentals",
]

AUTH_USER_MODEL = "accounts.User"

# Sessao do Django no banco, CSRF e o usuario da requisicao (M2.1a, RF-01), na ordem que o
# Django recomenda. As views do DRF sao `csrf_exempt`: o middleware nao as confere, quem
# confere e a autenticacao do DRF (fase 2 do M2.1a).
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

# Cookies (RF-02). `Secure` so com HTTPS, que o ambiente local nao tem; a hospedagem liga.
# O `csrftoken` fica legivel pelo frontend, que o devolve em `X-CSRFToken`.
_SECURE_COOKIES = os.environ.get("RUVOR_SECURE_COOKIES", "false").lower() in {
    "1",
    "true",
    "yes",
}
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = _SECURE_COOKIES
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = _SECURE_COOKIES
CSRF_TRUSTED_ORIGINS = _split_hosts(os.environ.get("RUVOR_CSRF_TRUSTED_ORIGINS", ""))

# RF-12. O validador de semelhanca procura `username`, `first_name` e `last_name` por
# padrao, que o usuario do projeto nao tem: sem `user_attributes`, ele nao ve o `name`.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("email", "name")},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Cache do Django (RF-22): o contador do bloqueio de entrada. Banco proprio do Redis -- o do
# `RUVOR_REDIS_URL` e o broker e o backend de resultados do Celery, e o `clear()` do
# `RedisCache` e `flushdb`. Nenhum codigo de `apps/` chama `cache.clear()`.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": _required("RUVOR_CACHE_URL"),
        "KEY_PREFIX": "ruvor",
    }
}

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
    "fundamentos": {
        "task": "apps.fundamentals.tasks.rotina_fundamentos",
        "schedule": _cron("RUVOR_BEAT_FUNDAMENTALS_CRON", "0 8 * * 1"),
    },
    "comunicados": {
        "task": "apps.fundamentals.tasks.importar_comunicados",
        "schedule": _cron("RUVOR_BEAT_DISCLOSURES_CRON", "0 20 * * 1-5"),
    },
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
