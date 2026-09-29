"""M4.2, T7: a taxa em toda rota (RF-08; V-10, V-11).

As taxas sao baixadas pelo atributo `THROTTLE_RATES` da classe -- o DRF o le no import, e o
`override_settings` nao o alcanca. As variaveis sao lidas em subprocesso com
`config.settings`, e nao `config.settings_test`: este as sobrescreve com `""`, e o caso
"presente" sempre leria o padrao.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from apps.accounts import services
from apps.accounts import views as conta
from apps.accounts.models import User
from apps.accounts.throttling import ApiRateThrottle
from tests.accounts.conftest import SENHA, organizacao, usuario

BACKEND = Path(__file__).resolve().parents[2]
VARIAVEIS = ("RUVOR_THROTTLE_API_KEY", "RUVOR_THROTTLE_USER", "RUVOR_THROTTLE_ANON")
PADROES = {"auth": "10/min", "api_key": "600/min", "user": "600/min", "anon": "60/min"}
LEITURA = "/api/v1/assets"

_SCRIPT = """
import json

import django

django.setup()

from django.conf import settings

print(json.dumps(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]))
"""


# --- V-10: as variaveis -------------------------------------------------------------------


def _taxas(**variaveis: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in VARIAVEIS}
    env.update(variaveis, DJANGO_SETTINGS_MODULE="config.settings")
    feito = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert feito.returncode == 0, feito.stderr
    taxas: dict[str, str] = json.loads(feito.stdout)
    return taxas


def test_v10_variaveis_ausentes_valem_os_padroes() -> None:
    assert _taxas() == PADROES


def test_v10_variaveis_vazias_valem_os_padroes() -> None:
    assert _taxas(**dict.fromkeys(VARIAVEIS, "")) == PADROES


def test_v10_variaveis_presentes_valem_o_valor() -> None:
    assert _taxas(
        RUVOR_THROTTLE_API_KEY="7/s",
        RUVOR_THROTTLE_USER="8/hour",
        RUVOR_THROTTLE_ANON="900/min",
    ) == {**PADROES, "api_key": "7/s", "user": "8/hour", "anon": "900/min"}


# --- V-11: a suite mede a taxa real -------------------------------------------------------


def test_v11_a_suite_roda_com_as_taxas_padrao() -> None:
    rf = settings.REST_FRAMEWORK
    assert rf["DEFAULT_THROTTLE_RATES"] == PADROES
    assert rf["DEFAULT_THROTTLE_RATES"]["anon"] == "60/min"
    assert ApiRateThrottle.THROTTLE_RATES == PADROES


# --- V-10: cada linha da tabela do RF-08 --------------------------------------------------


@pytest.fixture
def ana() -> User:
    return usuario(organizacao("acme"), "ana@acme.test", role="admin")


@pytest.fixture
def taxa_de_dois(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ApiRateThrottle,
        "THROTTLE_RATES",
        {**PADROES, "api_key": "2/min", "user": "2/min", "anon": "2/min"},
    )


def _por_chave(user: User) -> APIClient:
    segredo = services.create_api_key(user, name="minha", ip=None)[1]
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    return cliente


def _logado(user: User) -> APIClient:
    cliente = APIClient()
    cliente.force_login(user)
    return cliente


def _estourou(resposta: Any) -> None:
    assert resposta.status_code == 429, resposta.content
    assert int(resposta["Retry-After"]) > 0
    erro = resposta.json()["error"]
    assert erro["code"] == "too_many_requests"
    assert erro["details"]["wait_seconds"] > 0


def _duas_e_estoura(cliente: APIClient, rota: str = LEITURA) -> None:
    for _ in range(2):
        resposta = cliente.get(rota)
        assert resposta.status_code == 200, resposta.content
    _estourou(cliente.get(rota))


@pytest.mark.django_db
@pytest.mark.usefixtures("taxa_de_dois")
def test_v10_a_chave(ana: User) -> None:
    _duas_e_estoura(_por_chave(ana))


@pytest.mark.django_db
@pytest.mark.usefixtures("taxa_de_dois")
def test_v10_a_sessao(ana: User) -> None:
    _duas_e_estoura(_logado(ana), "/api/v1/auth/me")


@pytest.mark.django_db
@pytest.mark.usefixtures("taxa_de_dois")
def test_v10_o_anonimo() -> None:
    _duas_e_estoura(APIClient())


@pytest.mark.django_db
@pytest.mark.usefixtures("taxa_de_dois")
def test_v10_a_sessao_e_a_chave_da_mesma_pessoa_contam_separado(ana: User) -> None:
    _duas_e_estoura(_logado(ana))
    _duas_e_estoura(_por_chave(ana))


@pytest.mark.django_db
@pytest.mark.usefixtures("taxa_de_dois")
def test_v10_duas_chaves_da_mesma_pessoa_contam_separado(ana: User) -> None:
    _duas_e_estoura(_por_chave(ana))
    _duas_e_estoura(_por_chave(ana))


@pytest.mark.django_db
@pytest.mark.usefixtures("taxa_de_dois")
def test_v10_dois_ips_anonimos_contam_separado() -> None:
    _duas_e_estoura(APIClient(REMOTE_ADDR="10.0.0.1"))
    _duas_e_estoura(APIClient(REMOTE_ADDR="10.0.0.2"))


# --- as rotas com o limite `auth` ---------------------------------------------------------


@pytest.mark.parametrize(
    "view", [conta.SignupView, conta.LoginView, conta.PasswordView]
)
def test_signup_login_e_password_so_com_o_limite_auth(view: type) -> None:
    assert view().get_throttles()[0].__class__ is conta.AuthRateThrottle
    assert len(view().get_throttles()) == 1


@pytest.mark.django_db
@pytest.mark.usefixtures("taxa_de_dois")
def test_o_login_nao_conta_na_taxa_anonima(ana: User) -> None:
    cliente = APIClient()
    for _ in range(3):
        resposta = cliente.post(
            "/api/v1/auth/login",
            {"email": "ninguem@acme.test", "password": SENHA},
            format="json",
        )
        assert resposta.status_code == 400, resposta.content
    # o login gastou tres do limite `auth`, nenhum do `anon`: a leitura ainda tem as duas
    _duas_e_estoura(cliente)
