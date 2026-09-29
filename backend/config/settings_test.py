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
os.environ.setdefault("RUVOR_CACHE_URL", "redis://nao-usar:1/1")

# As taxas da API (M4.2, RF-08) com `=`, e nao `setdefault`: a suite roda com os padroes mesmo
# que o .env de dev suba a `ANON`. E o que faz o V-11 medir a taxa real.
os.environ["RUVOR_THROTTLE_API_KEY"] = ""
os.environ["RUVOR_THROTTLE_USER"] = ""
os.environ["RUVOR_THROTTLE_ANON"] = ""

from config.settings import *  # noqa: F403

# O cache da suite e o de memoria (M2.1a, RF-22): nenhum teste escreve no Redis vivo, e o
# contador do bloqueio de uma rodada nao vaza para a seguinte.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
