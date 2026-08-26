"""Configuracao do Flask por ambiente. Selecionada via FLASK_ENV / FLASK_DEBUG."""
from __future__ import annotations

import os


class BaseConfig:
    SECRET_KEY = os.environ.get("VARLAB_SECRET_KEY", "dev-secret-change-me")
    DEFAULT_TICKERS = ["^BVSP", "PETR4.SA", "VALE3.SA", "ITUB4.SA"]
    DEFAULT_ALPHAS = [0.05, 0.01]


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True


class ProdConfig(BaseConfig):
    DEBUG = False


CONFIG_BY_ENV = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
}


def get_config(env: str | None = None):
    env = env or os.environ.get("VARLAB_ENV", "development")
    return CONFIG_BY_ENV.get(env, DevConfig)
