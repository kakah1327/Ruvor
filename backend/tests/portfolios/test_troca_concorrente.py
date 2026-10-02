"""M2.2a, T3: duas trocas de composicao ao mesmo tempo (RF-12; V-08, a parte concorrente).

No molde de `tests/api/test_pedido_concorrente.py`: `transaction=True`, com `TRANSACIONAL` e
`banco_limpo`, porque a corrida precisa de commit de verdade entre conexoes. **A espera** e uma
`threading.Barrier(2)` no ponto de desvio `_after_portfolio_lock` de `apps/portfolios/services.py`,
com `wait(timeout=2)` e a `BrokenBarrierError` engolida. Com a trava da linha, a segunda thread
espera a trava e nunca chega a barreira; a espera da primeira estoura, ela grava a versao 2 e
confirma, e a segunda le a versao 2 e grava a 3. Sem a trava, as duas leem a versao 1 juntas e
tentam gravar duas versoes 2 -- o unico `portfolio_version_number` levanta.

Cada thread chama `connections.close_all()` no `finally`; o teste faz `join(timeout=30)` e
reprova se alguma ficou viva.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from decimal import Decimal
from functools import partial

import pytest
from django.db import connections

from apps.portfolios.models import PortfolioHolding, PortfolioVersion
from apps.portfolios.services import create_portfolio, replace_holdings
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)
from tests.portfolios.dados import acao, org_e_pessoas

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]

ESPERA_QUE_ESTOURA = 2
JOIN = 30


@pytest.fixture(autouse=True)
def barreira(monkeypatch: pytest.MonkeyPatch) -> threading.Barrier:
    """A `Barrier(2)` em `_after_portfolio_lock`, com a espera curta e o estouro engolido."""
    barreira = threading.Barrier(2)

    def espera_a_outra() -> None:
        try:
            barreira.wait(timeout=ESPERA_QUE_ESTOURA)
        except threading.BrokenBarrierError:
            pass

    monkeypatch.setattr(
        "apps.portfolios.services._after_portfolio_lock", espera_a_outra
    )
    return barreira


def _parte(
    nome: str, alvo: Callable[[], object], saida: list[tuple[str, object]]
) -> threading.Thread:
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


def test_v08_duas_trocas_ao_mesmo_tempo_dao_as_versoes_2_e_3() -> None:
    for ticker in ("PETR4", "VALE3", "ITUB4", "BBAS3"):
        acao(ticker, [])
    pessoas = org_e_pessoas()
    portfolio = create_portfolio(
        pessoas.admin,
        name="x",
        notional=None,
        holdings=[
            {"ticker": "PETR4", "weight": Decimal("50")},
            {"ticker": "VALE3", "weight": Decimal("50")},
        ],
    )
    pid = str(portfolio.public_id)
    composicoes = {
        "a": [
            {"ticker": "ITUB4", "weight": Decimal("50")},
            {"ticker": "BBAS3", "weight": Decimal("50")},
        ],
        "b": [
            {"ticker": "PETR4", "weight": Decimal("20")},
            {"ticker": "BBAS3", "weight": Decimal("80")},
        ],
    }

    saida: list[tuple[str, object]] = []
    threads = [
        _parte(
            nome,
            partial(replace_holdings, pessoas.member, pid, composicao),
            saida,
        )
        for nome, composicao in composicoes.items()
    ]
    for thread in threads:
        thread.join(timeout=JOIN)
    assert not any(thread.is_alive() for thread in threads)

    excecoes = [r for _, r in saida if isinstance(r, BaseException)]
    assert excecoes == []
    assert len(saida) == 2
    numeros = sorted(
        PortfolioVersion.unscoped.filter(portfolio=portfolio).values_list(
            "number", flat=True
        )
    )
    assert numeros == [1, 2, 3]
    # cada composicao virou uma versao, com as posicoes dela
    gravadas = {
        frozenset(
            PortfolioHolding.unscoped.filter(
                version__portfolio=portfolio, version__number=n
            ).values_list("asset__ticker", "weight")
        )
        for n in (2, 3)
    }
    assert gravadas == {
        frozenset((i["ticker"], i["weight"]) for i in c) for c in composicoes.values()
    }
