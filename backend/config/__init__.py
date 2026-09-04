"""Expoe a aplicacao Celery: e o que faz `celery -A config` encontra-la."""

from config.celery import app as celery_app

__all__ = ("celery_app",)
