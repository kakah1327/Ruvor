"""V-02 do M2.1b: o `POST /risk` exige conta pronta (RF-01; D-140).

- Anonimo -> 401 `not_authenticated`, com `WWW-Authenticate: Session`, e nenhum pedido.
- Senha provisoria por trocar -> 403 `password_change_required`, e nenhum pedido.
- Conta pronta -> 202 e um pedido novo em `core.compute_request`.
- O `GET` anonimo -> 200.
- `AssetRiskView` declara `ReadOpenWriteAccountReady` no proprio corpo, e a classe **delega**
  a `AccountReady`: com `AccountReady.has_permission` trocado por um duble que levanta
  `ApiError(418, "delegou", ...)`, o `POST` logado responde 418 e o `GET`, 200.

A sessao entra por `force_login`. Nada fala com o Redis: o `enqueue_chain` da view e trocado
por duble, pelo nome global de `apps.api.views`.
"""

from __future__ import annotations

from typing import Any, NoReturn

import pytest
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.accounts.models import Organization, User
from apps.accounts.permissions import AccountReady
from apps.api.errors import ApiError
from apps.api.models import ComputeRequest
from apps.api.permissions import ReadOpenWriteAccountReady
from apps.api.views import AssetRiskView
from apps.assets.models import Asset

pytestmark = pytest.mark.django_db

TICKER = "NOVO3"
ROTA = f"/api/v1/assets/{TICKER}/risk"


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """O duble do `enqueue_chain`, pelo nome que a view chama: nao fala com o Redis."""
    recebidos: list[int] = []
    monkeypatch.setattr("apps.api.views.enqueue_chain", recebidos.append)
    return recebidos


@pytest.fixture(autouse=True)
def ativo() -> Asset:
    """Uma acao ativa nunca calculada: o `POST` de conta pronta abre o pedido."""
    agora = timezone.now()
    return Asset.objects.create(
        ticker=TICKER,
        kind=Asset.Kind.STOCK,
        name=f"{TICKER} S.A.",
        trading_name=TICKER,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{TICKER}.SA",
        created_at=agora,
        updated_at=agora,
    )


def _usuario(*, must_change_password: bool) -> User:
    return User.objects.create_user(
        email="pede@ruvor.test",
        name="Quem Pede",
        organization=Organization.objects.get(slug="ruvor"),
        password="senha-de-teste-longa",
        must_change_password=must_change_password,
    )


def _logado(*, must_change_password: bool = False) -> APIClient:
    cliente = APIClient()
    cliente.force_login(_usuario(must_change_password=must_change_password))
    return cliente


def _codigo(corpo: dict[str, Any]) -> str:
    codigo: str = corpo["error"]["code"]
    return codigo


def test_anonimo_recebe_401_not_authenticated_com_www_authenticate(
    fila: list[int],
) -> None:
    resposta = APIClient().post(ROTA)

    assert resposta.status_code == 401, resposta.content
    assert _codigo(resposta.json()) == "not_authenticated"
    assert resposta["WWW-Authenticate"] == "Session"
    assert not ComputeRequest.objects.exists()
    assert fila == []


def test_senha_provisoria_recebe_403_password_change_required(
    fila: list[int],
) -> None:
    resposta = _logado(must_change_password=True).post(ROTA)

    assert resposta.status_code == 403, resposta.content
    assert _codigo(resposta.json()) == "password_change_required"
    assert not ComputeRequest.objects.exists()
    assert fila == []


def test_conta_pronta_recebe_202_e_abre_um_pedido_novo(fila: list[int]) -> None:
    resposta = _logado().post(ROTA)

    assert resposta.status_code == 202, resposta.content
    novo = ComputeRequest.objects.get()
    assert novo.asset.ticker == TICKER
    assert novo.status == ComputeRequest.Status.QUEUED
    assert resposta.json()["request"]["id"] == novo.pk


def test_o_get_anonimo_continua_200() -> None:
    resposta = APIClient().get(ROTA)

    assert resposta.status_code == 200, resposta.content


def test_a_view_declara_a_permissao_mista_no_proprio_corpo() -> None:
    assert AssetRiskView.__dict__["permission_classes"] == [ReadOpenWriteAccountReady]


def test_a_permissao_delega_a_account_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    def delegou(self: AccountReady, request: Request, view: APIView) -> NoReturn:
        raise ApiError(418, "delegou", "delegou", {})

    cliente = _logado()
    monkeypatch.setattr(AccountReady, "has_permission", delegou)

    escrita = cliente.post(ROTA)
    assert escrita.status_code == 418, escrita.content
    assert _codigo(escrita.json()) == "delegou"

    leitura = cliente.get(ROTA)
    assert leitura.status_code == 200, leitura.content
