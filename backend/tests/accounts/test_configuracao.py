"""M2.1a, T1: sessao, cookies, cache e validadores (V-01, V-02, V-17, RF-12), e a fase 1 sem
o DRF.

Os valores que dependem de variavel de ambiente sao conferidos **em subprocesso**: as
settings sao avaliadas uma vez por processo, e trocar a variavel dentro da sessao do pytest
nao as reconstruiria (o molde e `tests/fundamentals/test_beat.py`).

O cache de producao e conferido com `config.settings`, e nao com `config.settings_test`:
este troca o cache pelo de memoria, e conferir por ele provaria so a troca.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.db import connection
from pytest_django.plugin import DjangoDbBlocker

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_APPS_DIR = _BACKEND_DIR / "apps"
_ACCOUNTS_DIR = _APPS_DIR / "accounts"

# Os modulos de `apps/accounts/` que a fase 2 cria e que podem importar o DRF.
_MODULOS_DA_FASE_2 = {
    "authentication.py",
    "permissions.py",
    "views.py",
    "serializers.py",
    "urls.py",
}

_SCRIPT = """
import json

import django

django.setup()

from django.conf import settings

print(json.dumps({
    "SESSION_COOKIE_HTTPONLY": settings.SESSION_COOKIE_HTTPONLY,
    "SESSION_COOKIE_SAMESITE": settings.SESSION_COOKIE_SAMESITE,
    "SESSION_COOKIE_SECURE": settings.SESSION_COOKIE_SECURE,
    "CSRF_COOKIE_HTTPONLY": settings.CSRF_COOKIE_HTTPONLY,
    "CSRF_COOKIE_SAMESITE": settings.CSRF_COOKIE_SAMESITE,
    "CSRF_COOKIE_SECURE": settings.CSRF_COOKIE_SECURE,
    "CSRF_TRUSTED_ORIGINS": settings.CSRF_TRUSTED_ORIGINS,
    "CACHES": settings.CACHES,
}))
"""


def _settings(modulo: str, **variaveis: str) -> dict[str, object]:
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": modulo, **variaveis}
    completed = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    resultado: dict[str, object] = json.loads(completed.stdout)
    return resultado


def test_v01_middleware_e_a_lista_do_rf01() -> None:
    assert settings.MIDDLEWARE == [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "apps.accounts.tenancy.OrganizationScopeMiddleware",  # M4.2, RF-13
    ]


def test_v01_sessoes_instaladas() -> None:
    assert "django.contrib.sessions" in settings.INSTALLED_APPS


def test_v01_a_tabela_de_sessao_mora_no_public(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    with django_db_blocker.unblock(), connection.cursor() as cursor:
        cursor.execute(
            "SELECT schemaname FROM pg_tables WHERE tablename = 'django_session'"
        )
        esquemas = [linha[0] for linha in cursor.fetchall()]

    assert esquemas == ["public"]


def test_v02_cookies_seguros_seguem_a_variavel() -> None:
    ligado = _settings("config.settings_test", RUVOR_SECURE_COOKIES="true")
    desligado = _settings("config.settings_test", RUVOR_SECURE_COOKIES="false")

    for valores, seguro in ((ligado, True), (desligado, False)):
        assert valores["SESSION_COOKIE_SECURE"] is seguro
        assert valores["CSRF_COOKIE_SECURE"] is seguro
        assert valores["SESSION_COOKIE_HTTPONLY"] is True
        assert valores["CSRF_COOKIE_HTTPONLY"] is False
        assert valores["SESSION_COOKIE_SAMESITE"] == "Lax"
        assert valores["CSRF_COOKIE_SAMESITE"] == "Lax"


def test_v02_cookies_seguros_desligados_sem_a_variavel() -> None:
    env = {chave: valor for chave, valor in os.environ.items()}
    env.pop("RUVOR_SECURE_COOKIES", None)
    env["DJANGO_SETTINGS_MODULE"] = "config.settings_test"
    completed = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["SESSION_COOKIE_SECURE"] is False


def test_v02_origens_confiaveis_toleram_espaco() -> None:
    valores = _settings(
        "config.settings_test",
        RUVOR_CSRF_TRUSTED_ORIGINS="https://a.example, https://b.example",
    )
    assert valores["CSRF_TRUSTED_ORIGINS"] == [
        "https://a.example",
        "https://b.example",
    ]


def test_v17_cache_de_producao_e_o_redis_do_banco_proprio() -> None:
    valores = _settings(
        "config.settings", RUVOR_CACHE_URL="redis://cache-de-teste:6379/1"
    )
    assert valores["CACHES"] == {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://cache-de-teste:6379/1",
            "KEY_PREFIX": "ruvor",
        }
    }


def test_v17_a_suite_usa_o_cache_de_memoria() -> None:
    assert settings.CACHES["default"]["BACKEND"] == (
        "django.core.cache.backends.locmem.LocMemCache"
    )


def _chamadas_de_clear_no_cache(arvore: ast.AST) -> list[int]:
    """Linhas de `cache.clear()` ou `caches[...].clear()`."""
    linhas = []
    for no in ast.walk(arvore):
        if not (
            isinstance(no, ast.Call)
            and isinstance(no.func, ast.Attribute)
            and no.func.attr == "clear"
        ):
            continue
        alvo = no.func.value
        if isinstance(alvo, ast.Name) and alvo.id == "cache":
            linhas.append(no.lineno)
        elif (
            isinstance(alvo, ast.Subscript)
            and isinstance(alvo.value, ast.Name)
            and alvo.value.id == "caches"
        ):
            linhas.append(no.lineno)
    return linhas


def test_v17_nenhum_codigo_de_apps_limpa_o_cache() -> None:
    achados = {}
    for arquivo in sorted(_APPS_DIR.rglob("*.py")):
        linhas = _chamadas_de_clear_no_cache(ast.parse(arquivo.read_text("utf-8")))
        if linhas:
            achados[str(arquivo.relative_to(_BACKEND_DIR))] = linhas
    assert achados == {}


def test_v17_a_varredura_pega_as_duas_formas() -> None:
    """A varredura acima reprova quando deve: sem isto, ela poderia passar vazia."""
    codigo = "cache.clear()\ncaches['default'].clear()\nlista.clear()\n"
    assert _chamadas_de_clear_no_cache(ast.parse(codigo)) == [1, 2]


def test_rf12_os_quatro_validadores_de_senha() -> None:
    assert settings.AUTH_PASSWORD_VALIDATORS == [
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


def _importa_drf(arvore: ast.AST) -> bool:
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import) and any(
            nome.name.split(".")[0] == "rest_framework" for nome in no.names
        ):
            return True
        if (
            isinstance(no, ast.ImportFrom)
            and no.module is not None
            and no.module.split(".")[0] == "rest_framework"
        ):
            return True
    return False


def test_fase1_sem_drf() -> None:
    """Nada da fase 1 de `apps/accounts/` importa o DRF (D-107): a fase 1 nao depende do
    M1.6a, que traz os tipos do DRF para o `mypy` estrito."""
    importam = [
        str(arquivo.relative_to(_BACKEND_DIR))
        for arquivo in sorted(_ACCOUNTS_DIR.rglob("*.py"))
        if arquivo.name not in _MODULOS_DA_FASE_2
        and _importa_drf(ast.parse(arquivo.read_text("utf-8")))
    ]
    assert importam == []


def test_fase1_a_varredura_do_drf_pega_as_duas_formas() -> None:
    assert _importa_drf(ast.parse("import rest_framework"))
    assert _importa_drf(ast.parse("from rest_framework.views import APIView"))
    assert not _importa_drf(ast.parse("from django.http import HttpRequest"))
