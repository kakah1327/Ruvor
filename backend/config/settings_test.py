"""Configuracao da suite de testes e do plugin do mypy: preenche as variaveis RUVOR_*
obrigatorias com valores fixos e reexporta config.settings sem alteracao.

Nao e conftest.py porque o pytest-django chama django.setup() antes de carregar
qualquer conftest — o modulo de settings e o unico lugar que roda antes."""

import os

os.environ.setdefault("RUVOR_SECRET_KEY", "somente-para-teste")
os.environ.setdefault("RUVOR_ALLOWED_HOSTS", "testserver")

# Valores deliberadamente diferentes dos do compose: coincidentes, um .env incompleto
# passaria despercebido em F3-04. RUVOR_REDIS_URL entra aqui porque settings.py a le
# pelo _required, e este modulo tambem e importado pelo plugin do django-stubs.
os.environ.setdefault("RUVOR_DB_HOST", "nao-usar")
os.environ.setdefault("RUVOR_DB_PORT", "1")
os.environ.setdefault("RUVOR_DB_NAME", "nao-usar")
os.environ.setdefault("RUVOR_DB_USER", "nao-usar")
os.environ.setdefault("RUVOR_DB_PASSWORD", "nao-usar")
os.environ.setdefault("RUVOR_REDIS_URL", "redis://nao-usar:1/0")

from config.settings import *  # noqa: E402, F403
