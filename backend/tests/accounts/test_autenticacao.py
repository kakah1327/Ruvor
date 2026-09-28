"""M2.1a, T11: a autenticacao por sessao, a permissao de conta pronta e o `REST_FRAMEWORK`
(RF-03, RF-21, RF-29; V-03).

O CSRF so e conferido com `APIClient(enforce_csrf_checks=True)`: sem ele, o cliente de teste
marca a requisicao para o Django e o DRF pularem a checagem (`rest_framework/test.py`), e o
teste passaria vazio.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import _get_new_csrf_string
from rest_framework.request import Request
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import AccountReady
from apps.api.errors import ApiError
from tests.accounts.conftest import organizacao, requisicao, usuario

URLS_DE_TESTE = pytest.mark.urls("tests.api.urls_de_teste")
BACKEND = Path(__file__).resolve().parents[2]


def test_rest_framework_tem_as_chaves_da_fase_2() -> None:
    rf = settings.REST_FRAMEWORK
    assert rf["DEFAULT_AUTHENTICATION_CLASSES"] == [
        "apps.accounts.authentication.SessionAuthentication",
        "apps.accounts.authentication.ApiKeyAuthentication",  # M4.2, RF-06
    ]
    assert rf["NUM_PROXIES"] == 0
    assert rf["DEFAULT_THROTTLE_RATES"] == {"auth": "10/min"}
    assert "DEFAULT_THROTTLE_CLASSES" not in rf


@URLS_DE_TESTE
@pytest.mark.django_db
def test_v03_sem_login_e_401_com_www_authenticate(debug: bool) -> None:
    resposta = APIClient().get("/test/sem-permissao")
    assert resposta.status_code == 401
    assert resposta["WWW-Authenticate"] == "Session"
    assert resposta.json() == {
        "error": {
            "code": "not_authenticated",
            "message": "Entre para continuar.",
            "details": {},
        }
    }


def _drf(user: User | AnonymousUser) -> Request:
    """Um `Request` do DRF com o usuario posto pelo setter: sem autenticador, o `Request`
    daria sempre `AnonymousUser`."""
    drf = Request(requisicao())
    drf.user = user
    return drf


@pytest.mark.django_db
def test_account_ready_anonimo_e_false() -> None:
    assert AccountReady().has_permission(_drf(AnonymousUser()), APIView()) is False


@pytest.mark.django_db
def test_account_ready_com_senha_provisoria_levanta_password_change_required() -> None:
    user = usuario(organizacao(), "ana@acme.test", must_change_password=True)
    with pytest.raises(ApiError) as erro:
        AccountReady().has_permission(_drf(user), APIView())
    assert erro.value.status_code == 403
    assert erro.value.error_code == "password_change_required"


@pytest.mark.django_db
def test_account_ready_pronto_e_true() -> None:
    user = usuario(organizacao(), "ana@acme.test")
    assert AccountReady().has_permission(_drf(user), APIView()) is True


@URLS_DE_TESTE
@pytest.mark.django_db
def test_csrf_logado_sem_token_e_csrf_failed_e_com_token_passa() -> None:
    cliente = APIClient(enforce_csrf_checks=True)
    cliente.force_login(usuario(organizacao(), "ana@acme.test"))

    sem = cliente.post("/test/corpo", {"a": 1}, format="json")
    assert sem.status_code == 403
    assert sem.json()["error"]["code"] == "csrf_failed"

    # o `force_login` nao cria `csrftoken`: o segredo e posto no cookie e no cabecalho
    segredo = _get_new_csrf_string()
    cliente.cookies[settings.CSRF_COOKIE_NAME] = segredo
    com = cliente.post("/test/corpo", {"a": 1}, format="json", HTTP_X_CSRFTOKEN=segredo)
    assert com.status_code == 200, com.content
    assert com.json() == {"recebido": {"a": 1}}


def test_o_primeiro_import_do_drf_nao_cai_no_ciclo() -> None:
    """`rest_framework.views` como primeiro import do DRF, num processo novo: a classe de
    autenticacao e importada no meio dele, e o ciclo com `apps.api.errors` quebraria."""
    codigo = "import django; django.setup(); import rest_framework.views"
    ambiente = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings_test"}
    feito = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=BACKEND,
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
    )
    assert feito.returncode == 0, feito.stderr
