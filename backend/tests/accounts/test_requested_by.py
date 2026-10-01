"""M2.1a, T14: o autor do pedido de calculo, no pedido e na execucao que ele abre (RF-26; V-19).

- O `POST /risk` logado de um ativo nunca calculado grava o usuario no pedido novo, e a abertura
  daquele pedido (`_abrir_execucao` com `request_id`) grava o mesmo usuario na `risk_run`.
- O anonimo grava nulo nos dois. O segundo usuario que pede o mesmo ativo com pedido aberto
  recebe 202 e o pedido continua do primeiro. A abertura sem `request_id` (a rotina) grava nulo.

A abertura recebe `timezone.now()`: a `running` so conta dentro do prazo, contado do
relogio, e o caso da execucao em andamento depende disso.

A abertura e chamada pela **funcao com sublinhado**, como em `tests/risk/test_tasks.py`, com o
`_enqueue` trocado por duplo; o `POST`, com o `enqueue_chain` trocado pelo nome global de
`apps.api.views`. Nada fala com o Redis. A serie segue o molde de `_serie` de
`tests/risk/test_tasks.py`.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.api.models import ComputeRequest
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.models import RiskRun
from apps.risk.tasks import _abrir_execucao
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db

INICIO = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
ULTIMO_PREGAO = date(2026, 9, 18)  # sexta-feira
TICKER = "AAA3"


@pytest.fixture(autouse=True)
def filas(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Os duplos do `enqueue_chain` da view e do `_enqueue` da abertura: guardam o que
    receberam e nao falam com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.api.views.enqueue_chain", recebidos.append)
    monkeypatch.setattr("apps.risk.tasks._enqueue", recebidos.append)
    return recebidos


def _serie(ticker: str = TICKER, quantidade: int = config.MIN_SESSIONS) -> Asset:
    """Uma acao ativa com `quantidade` pregoes em dias uteis terminando em `ULTIMO_PREGAO`,
    log-retornos normais de desvio 1% a partir de 100, e nenhuma execucao."""
    asset = Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=INICIO,
        updated_at=INICIO,
    )
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    datas: list[date] = []
    dia = ULTIMO_PREGAO
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    nivel = 100.0
    retornos = np.random.default_rng(7).normal(0, 0.01, quantidade)
    linhas = []
    for dia, retorno in zip(sorted(datas), retornos, strict=True):
        nivel *= math.exp(float(retorno))
        valor = Decimal(str(nivel)).quantize(Decimal("0.000001"))
        linhas.append(
            Price(
                asset=asset,
                date=dia,
                open=valor,
                high=valor,
                low=valor,
                close=valor,
                adj_close=valor,
                volume=1000,
                log_return=None,
                run=coleta,
                updated_at=INICIO,
            )
        )
    Price.objects.bulk_create(linhas)
    return asset


def _cliente(user: User | None = None) -> APIClient:
    cliente = APIClient()
    if user is not None:
        cliente.force_login(user)
    return cliente


def _pede(cliente: APIClient, ticker: str = TICKER) -> ComputeRequest:
    resposta = cliente.post(f"/api/v1/assets/{ticker}/risk")
    assert resposta.status_code == 202, resposta.content
    return ComputeRequest.objects.get(asset__ticker=ticker)


def _abre(pedido: ComputeRequest) -> RiskRun:
    aberta = _abrir_execucao(
        pedido.asset.ticker,
        timezone.now().isoformat(),
        42,
        ["garch_1_1"],
        request_id=pedido.pk,
    )
    assert aberta["outcome"] == "opened", aberta
    assert aberta["run_id"] is not None
    return RiskRun.objects.get(pk=aberta["run_id"])


def test_v19_o_pedido_logado_grava_o_autor_no_pedido_e_na_execucao() -> None:
    _serie()
    ana = usuario(organizacao("acme"), "ana@acme.test")

    pedido = _pede(_cliente(ana))
    assert pedido.requested_by_id == ana.pk

    run = _abre(pedido)
    assert run.requested_by_id == ana.pk
    pedido.refresh_from_db()
    assert pedido.risk_run_id == run.pk


def test_v19_o_pedido_anonimo_grava_nulo_no_pedido_e_na_execucao() -> None:
    _serie()

    pedido = _pede(_cliente())
    assert pedido.requested_by_id is None

    run = _abre(pedido)
    assert run.requested_by_id is None


def test_v19_o_segundo_pedido_com_pedido_aberto_nao_muda_o_autor() -> None:
    _serie()
    org = organizacao("acme")
    ana = usuario(org, "ana@acme.test")
    bia = usuario(org, "bia@acme.test")

    primeiro = _pede(_cliente(ana))
    segundo = _pede(_cliente(bia))

    assert segundo.pk == primeiro.pk
    assert segundo.requested_by_id == ana.pk
    assert ComputeRequest.objects.count() == 1


def test_v19_a_execucao_ja_em_andamento_continua_de_quem_chegou_primeiro() -> None:
    _serie()
    org = organizacao("acme")
    ana = usuario(org, "ana@acme.test")
    bia = usuario(org, "bia@acme.test")
    run = _abre(_pede(_cliente(ana)))

    # o pedido de ana fecha sem fechar a execucao, e bia pede de novo: a `running` valida
    # do ativo da 202 sem pedido novo (RF-14), e nada muda de dono
    ComputeRequest.objects.update(status=ComputeRequest.Status.DONE)
    resposta = _cliente(bia).post(f"/api/v1/assets/{TICKER}/risk")
    assert resposta.status_code == 202, resposta.content
    assert ComputeRequest.objects.count() == 1

    # um pedido de bia ligado a mesma execucao, aberto por fora: a abertura so o liga
    pedido_bia = ComputeRequest.objects.create(
        asset=run.asset,
        status=ComputeRequest.Status.QUEUED,
        requested_at=INICIO,
        requested_by=bia,
    )
    aberta = _abrir_execucao(
        TICKER, timezone.now().isoformat(), 42, ["garch_1_1"], request_id=pedido_bia.pk
    )
    assert aberta["outcome"] == "already_running"
    assert aberta["run_id"] == run.pk
    run.refresh_from_db()
    assert run.requested_by_id == ana.pk


def test_v19_a_abertura_sem_pedido_grava_nulo() -> None:
    _serie()

    run_id = _abrir_execucao(TICKER, timezone.now().isoformat(), 42, ["garch_1_1"])

    assert run_id is not None
    assert RiskRun.objects.get(pk=run_id).requested_by_id is None
