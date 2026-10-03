"""M2.2a, T5: dois pedidos de risco ao mesmo tempo (RF-13; V-12).

No molde de `tests/api/test_pedido_concorrente.py`: `transaction=True`, com `TRANSACIONAL` e
`banco_limpo`. **A espera** e uma `threading.Barrier(2)` no ponto de desvio `_before_insert_run` de
`apps/portfolios/services.py`, depois das decisoes e antes do `insert`, com `wait(timeout=2)` e a
`BrokenBarrierError` engolida. Com a trava dos pedidos (7103), a segunda thread espera a trava e
nunca chega a barreira: a primeira insere e confirma, e a segunda ve a execucao (mesma versao) ou o
teto (outra organizacao). Sem a trava, as duas passam juntas e as duas inserem.

**O duplo** e o `send_task` da app do Celery: nao fala com o Redis.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import timedelta
from functools import partial
from typing import Any

import pytest
from django.db import connections
from django.utils import timezone
from pytest_django import Settings

from apps.accounts.models import User
from apps.portfolios.errors import PortfolioError
from apps.portfolios.models import Portfolio, PortfolioRiskRun
from apps.portfolios.services import request_risk
from config.celery import app
from tests.accounts.conftest import organizacao, usuario
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)
from tests.portfolios.dados import carteira, org_e_pessoas, serie_longa

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]

ESPERA_QUE_ESTOURA = 2
JOIN = 30
PESOS = {"PETR4": "60.00", "VALE3": "40.00"}


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    nomes: list[str] = []

    def send_task(name: str, **kwargs: Any) -> None:
        nomes.append(name)

    monkeypatch.setattr(app, "send_task", send_task)
    return nomes


@pytest.fixture(autouse=True)
def barreira(monkeypatch: pytest.MonkeyPatch) -> threading.Barrier:
    barreira = threading.Barrier(2)

    def espera_a_outra() -> None:
        try:
            barreira.wait(timeout=ESPERA_QUE_ESTOURA)
        except threading.BrokenBarrierError:
            pass

    monkeypatch.setattr("apps.portfolios.services._before_insert_run", espera_a_outra)
    return barreira


def _parte(
    nome: str, alvo: Callable[[], object], saida: list[tuple[str, object]]
) -> threading.Thread:
    def corre() -> None:
        try:
            saida.append((nome, alvo()))
        except BaseException as exc:  # a excecao volta ao teste
            saida.append((nome, exc))
        finally:
            connections.close_all()

    thread = threading.Thread(target=corre, name=nome, daemon=True)
    thread.start()
    return thread


def _corre(*pedidos: tuple[User, Portfolio]) -> list[object]:
    saida: list[tuple[str, object]] = []
    threads = [
        _parte(
            f"p{i}",
            partial(request_risk, pessoa, str(portfolio.public_id), timezone.now()),
            saida,
        )
        for i, (pessoa, portfolio) in enumerate(pedidos)
    ]
    for thread in threads:
        thread.join(timeout=JOIN)
    assert not any(thread.is_alive() for thread in threads)
    assert len(saida) == len(pedidos)
    return [r for _, r in saida]


def test_v12_dois_pedidos_da_mesma_versao_dao_uma_execucao() -> None:
    serie_longa("PETR4")
    serie_longa("VALE3")
    pessoas = org_e_pessoas()
    portfolio = carteira(pessoas.admin, PESOS)

    resultados = _corre((pessoas.admin, portfolio), (pessoas.member, portfolio))

    assert resultados == [None, None]  # o segundo ve a execucao em andamento
    assert PortfolioRiskRun.unscoped.count() == 1


def test_v12_duas_organizacoes_com_teto_1_dao_uma_execucao_e_um_queue_full(
    settings: Settings,
) -> None:
    settings.RUVOR_PORTFOLIO_COMPUTE_MAX = 1
    serie_longa("PETR4")
    serie_longa("VALE3")
    pessoas = org_e_pessoas()
    de_b = usuario(organizacao("org-b"), "admin@org-b.test", role="admin")
    portfolio_a = carteira(pessoas.admin, PESOS)
    portfolio_b = carteira(de_b, PESOS)

    resultados = _corre((pessoas.admin, portfolio_a), (de_b, portfolio_b))

    erros = [r for r in resultados if isinstance(r, PortfolioError)]
    assert [e.code for e in erros] == ["portfolio_queue_full"]
    assert [r for r in resultados if not isinstance(r, PortfolioError)] == [None]
    assert PortfolioRiskRun.unscoped.count() == 1
    assert PortfolioRiskRun.unscoped.get().calculated_at > timezone.now() - timedelta(
        minutes=1
    )
