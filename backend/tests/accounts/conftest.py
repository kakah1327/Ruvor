"""Infraestrutura dos testes de `apps/accounts` (M2.1a).

**O cache.** A suite usa o `LocMemCache` (RF-22), que dura a rodada inteira, e o
`RequestFactory` usa sempre o mesmo `REMOTE_ADDR`: sem limpar, as falhas de entrada de um
teste somariam no contador do seguinte. Aqui, em `tests/`, o `clear()` e permitido; a
proibicao e de `backend/apps/`.

**A sessao.** `requisicao()` monta um `HttpRequest` passado pelo `SessionMiddleware` e pelo
`AuthenticationMiddleware`, com sessao real em `django_session`. O `login()` do Django grava
a linha no `cycle_key`, mas os dados de autenticacao so vao ao banco no `session.save()`:
todo teste que reabre uma sessao por `requisicao(session_key=...)` chama antes
`chave(request)` na requisicao que a produziu.

**Depois do `transaction=True`.** O teste concorrente usa a marca `TRANSACIONAL` e a fixture
`banco_limpo` de `tests/api/migracao.py`, como todo teste `transaction=True` do repositorio:
o `flush` do Django nao ve as tabelas com esquema no `db_table`, e quem limpa `core`, `bronze`,
`silver` e `gold` e recria a `ruvor` e o Ibovespa e o `banco_limpo`.
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from pytest_django import Settings

from apps.accounts.models import Organization, User

SENHA = "cavalo-bateria-grampo-42"


@pytest.fixture(autouse=True)
def cache_limpo() -> None:
    cache.clear()


@pytest.fixture(params=[True, False], ids=["debug_ligado", "debug_desligado"])
def debug(request: pytest.FixtureRequest, settings: Settings) -> bool:
    """Copia da de `tests/api/conftest.py` (V-03, V-20): `conftest` nao se importa."""
    ligado: bool = request.param
    settings.DEBUG = ligado
    return ligado


def _sem_resposta(request: HttpRequest) -> HttpResponse:
    return HttpResponse()


def requisicao(session_key: str | None = None, ip: str = "127.0.0.1") -> HttpRequest:
    """Um `POST /` com sessao real; com `session_key`, reabre aquela sessao."""
    request = RequestFactory().post("/", REMOTE_ADDR=ip)
    if session_key is not None:
        request.COOKIES[settings.SESSION_COOKIE_NAME] = session_key
    SessionMiddleware(_sem_resposta).process_request(request)
    AuthenticationMiddleware(_sem_resposta).process_request(request)
    return request


def chave(request: HttpRequest) -> str:
    """Grava a sessao da requisicao e devolve a chave dela."""
    request.session.save()
    key = request.session.session_key
    assert key is not None
    return key


def autenticado(session_key: str) -> bool:
    """A sessao, reaberta numa requisicao nova, autentica alguem?"""
    return bool(requisicao(session_key=session_key).user.is_authenticated)


def organizacao(slug: str = "acme", *, pessoal: bool = False) -> Organization:
    return Organization.objects.create(
        name=slug.capitalize(), slug=slug, is_personal=pessoal
    )


def usuario(
    org: Organization,
    email: str,
    *,
    role: str = "member",
    password: str = SENHA,
    name: str = "Pessoa de Teste",
    must_change_password: bool = False,
    is_active: bool = True,
) -> User:
    return User.objects.create_user(
        email=email,
        name=name,
        organization=org,
        password=password,
        role=role,
        must_change_password=must_change_password,
        is_active=is_active,
    )
