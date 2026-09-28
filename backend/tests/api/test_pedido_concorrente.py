"""V-14 e V-15: dois `POST` concorrentes (RF-16, RF-17).

Todo teste aqui e `transaction=True` -- com `TRANSACIONAL` e `banco_limpo` de
`tests/api/migracao.py`, como todo teste assim --, porque a corrida precisa de commit de
verdade entre conexoes, e cada thread abre a sua (o Django da uma por thread). Cada thread
chama a view pelo `APIRequestFactory`, sem o cliente de teste, que liga e desliga sinais
globais a cada pedido.

**A espera** e uma `threading.Barrier(2)` no ponto de desvio `_before_insert` de
`apps/api/views.py` -- depois das decisoes do `POST` e antes do `insert` --, com
`wait(timeout=2)` e a `BrokenBarrierError` engolida: nunca vira erro da view. Com a trava
global, a segunda thread espera a trava e nunca chega a barreira; a espera da primeira
estoura, ela insere e confirma, e a segunda ve o pedido (202, V-14) ou o teto (429, V-15).
Sem a trava, as duas passam pela barreira juntas: no mesmo ativo, a segunda bate no indice
parcial -- um 500 --; em ativos diferentes, as duas inserem e o teto passa.

**O duplo** e `apps.api.views.enqueue_chain` -- o nome que a view chama no `on_commit`; o de
`apps.api.ondemand` nao teria efeito.

**O invariante**, conferido no fim de cada teste: nenhum pedido aberto aponta para
`risk_run` fechada, e ha no maximo um pedido aberto por ativo.

Cada thread chama `connections.close_all()` no `finally`; o teste faz `join(timeout=30)` e
reprova se alguma ficou viva -- antes da desmontagem, cujo `TRUNCATE` travaria na trava de
uma thread viva em vez de reprovar.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any, cast

import pytest
from django.db import connections
from django.db.models import Count
from django.utils import timezone
from pytest_django import Settings
from rest_framework.test import APIRequestFactory

from apps.api.models import ComputeRequest
from apps.api.ondemand import OPEN_STATUSES
from apps.api.views import AssetRiskView
from apps.assets.models import Asset
from apps.risk.models import RiskRun
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]

Status = ComputeRequest.Status

ESPERA_QUE_ESTOURA = 2
JOIN = 30

Resultado = tuple[int, dict[str, Any]]


@pytest.fixture(autouse=True)
def prazo(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """O duplo do `enqueue_chain`, pelo nome que a view chama: nao fala com o Redis."""
    recebidos: list[int] = []
    monkeypatch.setattr("apps.api.views.enqueue_chain", recebidos.append)
    return recebidos


@pytest.fixture(autouse=True)
def barreira(monkeypatch: pytest.MonkeyPatch) -> threading.Barrier:
    """A `Barrier(2)` em `_before_insert`, com a espera curta e o estouro engolido."""
    barreira = threading.Barrier(2)

    def espera_a_outra() -> None:
        try:
            barreira.wait(timeout=ESPERA_QUE_ESTOURA)
        except threading.BrokenBarrierError:
            pass

    monkeypatch.setattr("apps.api.views._before_insert", espera_a_outra)
    return barreira


# --- os dados ------------------------------------------------------------------------------


def _ativo(ticker: str) -> Asset:
    agora = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )


def _pedido(asset: Asset, status: str, requested_at: datetime) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset, status=status, requested_at=requested_at
    )


# --- as threads ----------------------------------------------------------------------------


def _post(ticker: str) -> Resultado:
    """O `POST` do `/risk` pela view, com o corpo renderizado."""
    pedido = APIRequestFactory().post(f"/api/v1/assets/{ticker}/risk")
    resposta = AssetRiskView.as_view()(pedido, ticker=ticker)
    resposta.render()
    corpo: dict[str, Any] = json.loads(resposta.content)
    return resposta.status_code, corpo


def _alvo(ticker: str) -> Callable[[], Resultado]:
    return lambda: _post(ticker)


def _parte(
    nome: str, alvo: Callable[[], Resultado], saida: list[tuple[str, object]]
) -> threading.Thread:
    """Roda `alvo` numa thread; o resultado -- ou a excecao -- volta por `saida`."""

    def corre() -> None:
        try:
            saida.append((nome, alvo()))
        except BaseException as exc:  # a excecao volta ao teste, que a reprova
            saida.append((nome, exc))
        finally:
            connections.close_all()

    thread = threading.Thread(target=corre, name=nome, daemon=True)
    thread.start()
    return thread


def _corre(*tickers: str) -> list[Resultado]:
    """Um `POST` por ticker, cada um na sua thread, ao mesmo tempo; as respostas em ordem
    de status."""
    saida: list[tuple[str, object]] = []
    threads = [
        _parte(f"post{i}-{ticker}", _alvo(ticker), saida)
        for i, ticker in enumerate(tickers)
    ]
    for thread in threads:
        thread.join(timeout=JOIN)
    vivas = [t.name for t in threads if t.is_alive()]
    assert vivas == [], f"threads vivas depois de {JOIN} s: {vivas}"
    erros = [(nome, r) for nome, r in saida if isinstance(r, BaseException)]
    assert erros == []
    resultados = [cast(Resultado, r) for _, r in saida]
    return sorted(resultados, key=lambda r: r[0])


def _invariante() -> None:
    """Nenhum pedido aberto aponta para `risk_run` fechada; no maximo um aberto por ativo."""
    abertos = ComputeRequest.objects.filter(status__in=OPEN_STATUSES)
    sobre_fechada = list(
        abertos.filter(risk_run__isnull=False)
        .exclude(risk_run__status=RiskRun.Status.RUNNING)
        .values_list("pk", "risk_run_id", "risk_run__status")
    )
    assert sobre_fechada == []
    por_ativo = list(abertos.values("asset_id").annotate(n=Count("pk")).filter(n__gt=1))
    assert por_ativo == []


def _abertos() -> list[str]:
    return sorted(
        ComputeRequest.objects.filter(status__in=OPEN_STATUSES).values_list(
            "asset__ticker", flat=True
        )
    )


# --- V-14: um pedido por ativo -------------------------------------------------------------


def test_dois_posts_do_mesmo_ativo_abrem_um_pedido_so(fila: list[int]) -> None:
    _ativo("NOVO3")

    resultados = _corre("NOVO3", "NOVO3")

    assert [status for status, _ in resultados] == [202, 202], resultados
    ids = {corpo["request"]["id"] for _, corpo in resultados}
    novo = ComputeRequest.objects.get()
    assert ids == {novo.pk}
    assert novo.status == Status.QUEUED
    assert fila == [novo.pk]
    _invariante()


# --- V-15: o teto estrito ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("teto", "abertos_antes"),
    [(2, ["CCCC3"]), (1, [])],
    ids=["teto_2_com_um_aberto", "teto_1_com_zero_abertos"],
)
def test_dois_posts_de_ativos_diferentes_nao_passam_do_teto(
    settings: Settings, fila: list[int], teto: int, abertos_antes: list[str]
) -> None:
    settings.RUVOR_ON_DEMAND_MAX = teto
    for ticker in abertos_antes:
        _pedido(_ativo(ticker), Status.RUNNING, timezone.now() - timedelta(minutes=5))
    _ativo("AAAA3")
    _ativo("BBBB3")

    resultados = _corre("AAAA3", "BBBB3")

    assert [status for status, _ in resultados] == [202, 429], resultados
    aceito, recusado = resultados
    assert recusado[1]["error"]["code"] == "on_demand_queue_full"
    assert recusado[1]["error"]["details"] == {"max": teto}
    assert aceito[1]["request"]["status"] == "queued"
    assert ComputeRequest.objects.filter(status__in=OPEN_STATUSES).count() == teto
    assert len(fila) == 1
    _invariante()


def test_pedido_vencido_nao_conta_para_o_teto(
    settings: Settings, fila: list[int]
) -> None:
    """Nao e a prova da trava global: sem ela, o `UPDATE` do `expire_stale` sobre a mesma
    linha vencida ja serializa as duas transacoes (medido na T12). Quem prova a trava sao os
    dois testes acima."""
    settings.RUVOR_ON_DEMAND_MAX = 1
    vencido = _pedido(
        _ativo("CCCC3"), Status.QUEUED, timezone.now() - timedelta(minutes=45)
    )
    _ativo("AAAA3")
    _ativo("BBBB3")

    resultados = _corre("AAAA3", "BBBB3")

    assert [status for status, _ in resultados] == [202, 429], resultados
    assert ComputeRequest.objects.get(pk=vencido.pk).status == Status.EXPIRED
    assert len(_abertos()) == 1
    assert len(fila) == 1
    _invariante()
