"""Configuracao da suite de testes e do plugin do mypy: preenche as variaveis RUVOR_*
obrigatorias com valores fixos e reexporta config.settings sem alteracao.

Nao e conftest.py porque o pytest-django chama django.setup() antes de carregar
qualquer conftest — o modulo de settings e o unico lugar que roda antes."""

import os

os.environ.setdefault("RUVOR_SECRET_KEY", "somente-para-teste")
os.environ.setdefault("RUVOR_ALLOWED_HOSTS", "testserver")

from config.settings import *  # noqa: E402, F403
