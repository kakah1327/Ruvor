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

**Depois do `transaction=True`.** O teste nao roda numa transacao desfeita no fim: o que ele
grava fica. E o `flush` do fim **nao limpa** as tabelas com esquema no `db_table` -- ele
lista as tabelas pelo `search_path` e so ve cinco do `public` (medido em 2026-09-27) --,
entao o que o teste gravou em `core` sobraria para os testes seguintes. A fixture **de
modulo** `restaura_dados_de_migracao` limpa o que os testes deixaram em `core` e garante a
`ruvor` e o Ibovespa. A desmontagem dela roda depois da desmontagem de funcao do ultimo teste
do modulo, portanto depois do ultimo `flush`; uma fixture de funcao pedida pelo teste nao
serviria, porque a marca `django_db` monta o `_django_db_helper` antes dela e o desmonta
depois. O teste `transaction=True` declara `available_apps`: e o que faz o `flush` usar
`TRUNCATE ... CASCADE` -- sem isso, o `TRUNCATE` de `auth_permission` e recusado, porque a
tabela de juncao `core.user_user_permissions`, que o `flush` nao ve, aponta para ela.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator

import pytest
from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from pytest_django.plugin import DjangoDbBlocker

from apps.accounts.models import Organization, User

SENHA = "cavalo-bateria-grampo-42"


@pytest.fixture(autouse=True)
def cache_limpo() -> None:
    cache.clear()


@pytest.fixture(scope="module")
def restaura_dados_de_migracao(
    django_db_setup: None, django_db_blocker: DjangoDbBlocker
) -> Iterator[None]:
    yield
    organizacao = importlib.import_module(
        "apps.accounts.migrations.0002_marco1_organization"
    )
    ibovespa = importlib.import_module("apps.assets.migrations.0002_ibovespa")
    with django_db_blocker.unblock():
        with connection.cursor() as cursor:
            # a auditoria so cresce pelo ORM; no banco de teste, quem limpa e o TRUNCATE
            cursor.execute("TRUNCATE core.access_event")
        User.objects.all().delete()
        Organization.objects.exclude(slug="ruvor").delete()
        organizacao.cria_organizacao_do_marco1(django_apps, None)
        ibovespa.cria_ibovespa(django_apps, None)


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
