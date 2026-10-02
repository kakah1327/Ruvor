"""M2.2a, T3: os servicos da composicao (RF-08 a RF-12, RF-18; V-05 a V-09 pelo servico).

Os servicos sao chamados **sem contexto posto**: cada um abre o `organization_scope` de quem pede,
e e isso que se prova. As leituras de conferencia vao pelo gerente base (`unscoped`).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.utils import timezone

from apps.accounts.tenancy import current_organization_id
from apps.assets.models import Asset
from apps.portfolios.errors import PortfolioError
from apps.portfolios.models import Portfolio, PortfolioHolding, PortfolioVersion
from apps.portfolios.services import (
    archive_portfolio,
    create_portfolio,
    get_portfolio,
    list_portfolios,
    loss_brl,
    replace_holdings,
    update_portfolio,
)
from tests.portfolios.dados import Pessoas, acao, org_e_pessoas

pytestmark = pytest.mark.django_db

TICKERS = ("PETR4", "VALE3", "ITUB4", "BBAS3")


@pytest.fixture
def pessoas() -> Pessoas:
    for ticker in TICKERS:
        acao(ticker, [])
    acao("OIBR3", [], status=Asset.Status.INACTIVE)
    return org_e_pessoas()


def _pos(*pares: tuple[str, str]) -> list[dict[str, Any]]:
    return [{"ticker": t, "weight": Decimal(w)} for t, w in pares]


METADE = _pos(("PETR4", "50.00"), ("VALE3", "50.00"))


def _cria(pessoas: Pessoas, nome: str = "Minha carteira") -> Portfolio:
    return create_portfolio(
        pessoas.admin, name=nome, notional=Decimal("100000.00"), holdings=METADE
    )


def _detalhes(erro: pytest.ExceptionInfo[PortfolioError]) -> dict[str, Any]:
    assert erro.value.code == "invalid_holdings"
    assert erro.value.message == "Composição inválida."
    return erro.value.details


def _posicoes(version: PortfolioVersion) -> set[tuple[str, Decimal]]:
    return {
        (h.asset.ticker, h.weight)
        for h in PortfolioHolding.unscoped.filter(version=version).select_related(
            "asset"
        )
    }


# --- V-05: criar ------------------------------------------------------------------------


def test_v05_cria_a_carteira_a_versao_1_e_as_posicoes(pessoas: Pessoas) -> None:
    portfolio = create_portfolio(
        pessoas.member,
        name="  Renda  ",
        notional=None,
        holdings=_pos((" petr4 ", "33.33"), ("VALE3", "66.67")),
    )
    assert current_organization_id() is None
    linha = Portfolio.unscoped.get(pk=portfolio.pk)
    assert (linha.organization_id, linha.created_by_id) == (
        pessoas.acme.pk,
        pessoas.member.pk,
    )
    assert (linha.name, linha.notional, linha.archived_at) == ("Renda", None, None)
    assert linha.created_at == linha.updated_at
    versao = PortfolioVersion.unscoped.get(portfolio=portfolio)
    assert versao.number == 1
    assert versao.created_by_id == pessoas.member.pk
    assert _posicoes(versao) == {
        ("PETR4", Decimal("33.33")),
        ("VALE3", Decimal("66.67")),
    }


def test_v05_o_peso_gravado_e_o_decimal_enviado(pessoas: Pessoas) -> None:
    portfolio = create_portfolio(
        pessoas.admin,
        name="x",
        notional=Decimal("10.50"),
        holdings=_pos(("PETR4", "0.01"), ("VALE3", "99.99")),
    )
    pesos = sorted(
        PortfolioHolding.unscoped.filter(version__portfolio=portfolio).values_list(
            "weight", flat=True
        )
    )
    assert pesos == [Decimal("0.01"), Decimal("99.99")]
    assert Portfolio.unscoped.get(pk=portfolio.pk).notional == Decimal("10.50")


# --- V-06: a regra da composicao --------------------------------------------------------


def _item(index: int, ticker: str, reason: str) -> dict[str, Any]:
    return {"index": index, "ticker": ticker, "reason": reason}


CASOS_DE_ITEM = {
    "duplicate": (
        [("PETR4", "50"), ("petr4", "25"), ("VALE3", "25")],
        [_item(1, "PETR4", "duplicate")],
    ),
    "unknown_ticker": (
        [("PETR4", "50"), ("XXXX3", "50")],
        [_item(1, "XXXX3", "unknown_ticker")],
    ),
    "not_a_stock": (
        [("IBOV", "50"), ("PETR4", "50")],
        [_item(0, "IBOV", "not_a_stock")],
    ),
    "inactive": (
        [("PETR4", "50"), ("OIBR3", "50")],
        [_item(1, "OIBR3", "inactive")],
    ),
    "weight_zero": (
        [("PETR4", "0"), ("VALE3", "100")],
        [_item(0, "PETR4", "weight_out_of_range")],
    ),
    "weight_negativo": (
        [("PETR4", "-10"), ("VALE3", "50"), ("ITUB4", "60")],
        [_item(0, "PETR4", "weight_out_of_range")],
    ),
    "weight_acima_de_100": (
        [("PETR4", "100.01"), ("VALE3", "-0.01")],
        [
            _item(0, "PETR4", "weight_out_of_range"),
            _item(1, "VALE3", "weight_out_of_range"),
        ],
    ),
}


@pytest.mark.parametrize("caso", sorted(CASOS_DE_ITEM))
def test_v06_cada_reason_sozinho(pessoas: Pessoas, caso: str) -> None:
    pares, itens = CASOS_DE_ITEM[caso]
    with pytest.raises(PortfolioError) as erro:
        create_portfolio(pessoas.admin, name="x", notional=None, holdings=_pos(*pares))
    assert _detalhes(erro) == {"reason": "items", "items": itens}


def test_v06_os_varios_juntos_em_ordem_de_index_um_por_item(pessoas: Pessoas) -> None:
    pares = [
        ("OIBR3", "10"),  # 0: inativa
        ("PETR4", "10"),  # 1: valida
        ("oibr3", "10"),  # 2: duplicada **e** inativa -> duplicate
        ("XXXX3", "10"),  # 3: desconhecida
        ("IBOV", "10"),  # 4: indice
        ("VALE3", "100.01"),  # 5: peso fora
        ("ITUB4", "40"),  # 6: valida
    ]
    with pytest.raises(PortfolioError) as erro:
        create_portfolio(pessoas.admin, name="x", notional=None, holdings=_pos(*pares))
    assert _detalhes(erro) == {
        "reason": "items",
        "items": [
            {"index": 0, "ticker": "OIBR3", "reason": "inactive"},
            {"index": 2, "ticker": "OIBR3", "reason": "duplicate"},
            {"index": 3, "ticker": "XXXX3", "reason": "unknown_ticker"},
            {"index": 4, "ticker": "IBOV", "reason": "not_a_stock"},
            {"index": 5, "ticker": "VALE3", "reason": "weight_out_of_range"},
        ],
    }


@pytest.mark.parametrize("quantas", [0, 1, 21])
def test_v06_quantas_fora_de_2_a_20(pessoas: Pessoas, quantas: int) -> None:
    pares = [(f"Z{i:03d}3", "1") for i in range(quantas)]
    with pytest.raises(PortfolioError) as erro:
        create_portfolio(pessoas.admin, name="x", notional=None, holdings=_pos(*pares))
    assert _detalhes(erro) == {"reason": "count_out_of_range", "count": quantas}


def test_v06_vinte_posicoes_passam(pessoas: Pessoas) -> None:
    for i in range(20):
        acao(f"Y{i:03d}3", [])
    pares = [(f"Y{i:03d}3", "5.00") for i in range(20)]
    create_portfolio(pessoas.admin, name="x", notional=None, holdings=_pos(*pares))


@pytest.mark.parametrize("ultimo", ["49.99", "50.01"])
def test_v06_a_soma_diferente_de_100(pessoas: Pessoas, ultimo: str) -> None:
    with pytest.raises(PortfolioError) as erro:
        create_portfolio(
            pessoas.admin,
            name="x",
            notional=None,
            holdings=_pos(("PETR4", "50.00"), ("VALE3", ultimo)),
        )
    soma = format(Decimal("50.00") + Decimal(ultimo), "f")
    assert soma in {"99.99", "100.01"}
    assert _detalhes(erro) == {"reason": "weights_sum", "sum": soma}


def test_v06_a_contagem_vem_antes_dos_itens_e_os_itens_antes_da_soma(
    pessoas: Pessoas,
) -> None:
    with pytest.raises(PortfolioError) as erro:
        create_portfolio(
            pessoas.admin, name="x", notional=None, holdings=_pos(("XXXX3", "1"))
        )
    assert _detalhes(erro)["reason"] == "count_out_of_range"
    with pytest.raises(PortfolioError) as erro:
        create_portfolio(
            pessoas.admin,
            name="x",
            notional=None,
            holdings=_pos(("XXXX3", "1"), ("PETR4", "1")),
        )
    assert _detalhes(erro)["reason"] == "items"


def test_v06_nenhum_erro_grava_linha(pessoas: Pessoas) -> None:
    portfolio = _cria(pessoas)
    for pares in (
        [("PETR4", "100")],
        [("PETR4", "50"), ("XXXX3", "50")],
        [("PETR4", "50"), ("VALE3", "49")],
    ):
        with pytest.raises(PortfolioError):
            create_portfolio(
                pessoas.admin, name="y", notional=None, holdings=_pos(*pares)
            )
        with pytest.raises(PortfolioError):
            replace_holdings(pessoas.admin, str(portfolio.public_id), _pos(*pares))
    assert Portfolio.unscoped.count() == 1
    assert PortfolioVersion.unscoped.count() == 1
    assert PortfolioHolding.unscoped.count() == 2


# --- V-07: listar, ler, mudar, arquivar -------------------------------------------------


def test_v07_lista_so_as_da_organizacao_sem_arquivadas_da_mais_nova(
    pessoas: Pessoas,
) -> None:
    primeira = _cria(pessoas, "primeira")
    segunda = _cria(pessoas, "segunda")
    terceira = _cria(pessoas, "terceira")
    create_portfolio(pessoas.de_fora, name="de fora", notional=None, holdings=METADE)
    archive_portfolio(pessoas.admin, str(segunda.public_id))
    # o mesmo instante nas duas que sobram: o desempate e o `id`, decrescente
    instante = timezone.now() - timedelta(days=1)
    Portfolio.unscoped.filter(pk__in=[primeira.pk, terceira.pk]).update(
        created_at=instante
    )

    total, linhas = list_portfolios(pessoas.member)

    assert total == 2
    assert [p.pk for p in linhas] == [terceira.pk, primeira.pk]
    assert current_organization_id() is None


def test_v07_limit_e_offset(pessoas: Pessoas) -> None:
    criadas = [_cria(pessoas, f"c{i}") for i in range(3)]
    total, linhas = list_portfolios(pessoas.admin, limit=1, offset=1)
    assert total == 3
    assert [p.pk for p in linhas] == [criadas[1].pk]


@pytest.mark.parametrize(
    ("limit", "offset", "parametro"),
    [(0, 0, "limit"), (101, 0, "limit"), (50, -1, "offset")],
)
def test_v07_limit_e_offset_fora_da_faixa(
    pessoas: Pessoas, limit: int, offset: int, parametro: str
) -> None:
    with pytest.raises(PortfolioError) as erro:
        list_portfolios(pessoas.admin, limit=limit, offset=offset)
    assert erro.value.code == "invalid_parameter"
    assert erro.value.details == {"parameter": parametro}


def test_v07_mudar_nome_e_valor_sem_versao_nova(pessoas: Pessoas) -> None:
    portfolio = _cria(pessoas)
    antes = Portfolio.unscoped.get(pk=portfolio.pk).updated_at

    update_portfolio(
        pessoas.member,
        str(portfolio.public_id),
        {"name": " Nova ", "notional": Decimal("5.00")},
    )

    linha = Portfolio.unscoped.get(pk=portfolio.pk)
    assert (linha.name, linha.notional) == ("Nova", Decimal("5.00"))
    assert linha.updated_at > antes
    assert PortfolioVersion.unscoped.filter(portfolio=portfolio).count() == 1


def test_v07_notional_nulo_tira_o_valor(pessoas: Pessoas) -> None:
    portfolio = _cria(pessoas)
    update_portfolio(pessoas.admin, str(portfolio.public_id), {"notional": None})
    linha = Portfolio.unscoped.get(pk=portfolio.pk)
    assert (linha.name, linha.notional) == ("Minha carteira", None)


def test_v07_so_o_nome_mantem_o_valor(pessoas: Pessoas) -> None:
    portfolio = _cria(pessoas)
    update_portfolio(pessoas.admin, str(portfolio.public_id), {"name": "Outro"})
    assert Portfolio.unscoped.get(pk=portfolio.pk).notional == Decimal("100000.00")


def test_v07_arquivada_some_de_todas_as_operacoes(pessoas: Pessoas) -> None:
    portfolio = _cria(pessoas)
    pid = str(portfolio.public_id)
    archive_portfolio(pessoas.admin, pid)
    assert Portfolio.unscoped.get(pk=portfolio.pk).archived_at is not None

    operacoes: list[Callable[[], object]] = [
        lambda: get_portfolio(pessoas.admin, pid),
        lambda: update_portfolio(pessoas.admin, pid, {"name": "x"}),
        lambda: replace_holdings(pessoas.admin, pid, METADE),
        lambda: archive_portfolio(pessoas.admin, pid),
    ]
    for operacao in operacoes:
        with pytest.raises(PortfolioError) as erro:
            operacao()
        assert erro.value.code == "portfolio_not_found"


# --- V-08: trocar a composicao ----------------------------------------------------------


def test_v08_a_versao_2_e_a_versao_1_intacta(pessoas: Pessoas) -> None:
    portfolio = _cria(pessoas)
    antes = Portfolio.unscoped.get(pk=portfolio.pk).updated_at

    replace_holdings(
        pessoas.member,
        str(portfolio.public_id),
        _pos(("ITUB4", "70.00"), ("BBAS3", "30.00")),
    )

    v1 = PortfolioVersion.unscoped.get(portfolio=portfolio, number=1)
    v2 = PortfolioVersion.unscoped.get(portfolio=portfolio, number=2)
    assert _posicoes(v1) == {("PETR4", Decimal("50.00")), ("VALE3", Decimal("50.00"))}
    assert _posicoes(v2) == {("ITUB4", Decimal("70.00")), ("BBAS3", Decimal("30.00"))}
    assert v2.created_by_id == pessoas.member.pk
    assert Portfolio.unscoped.get(pk=portfolio.pk).updated_at > antes


def test_v08_a_mesma_composicao_em_outra_ordem_nao_cria_versao(
    pessoas: Pessoas,
) -> None:
    portfolio = _cria(pessoas)
    antes = Portfolio.unscoped.get(pk=portfolio.pk).updated_at

    replace_holdings(
        pessoas.admin,
        str(portfolio.public_id),
        _pos(("vale3", "50"), ("PETR4", "50.0")),
    )

    assert PortfolioVersion.unscoped.filter(portfolio=portfolio).count() == 1
    assert Portfolio.unscoped.get(pk=portfolio.pk).updated_at == antes


def test_v08_mudar_so_um_peso_cria_versao(pessoas: Pessoas) -> None:
    portfolio = _cria(pessoas)
    replace_holdings(
        pessoas.admin,
        str(portfolio.public_id),
        _pos(("PETR4", "50.01"), ("VALE3", "49.99")),
    )
    assert PortfolioVersion.unscoped.filter(portfolio=portfolio).count() == 2


# --- V-09: a organizacao e o papel ------------------------------------------------------


def test_v09_outra_organizacao_recebe_o_mesmo_404_que_um_id_que_nao_existe(
    pessoas: Pessoas,
) -> None:
    portfolio = _cria(pessoas)
    ids = [
        str(portfolio.public_id),  # de outra organizacao, para quem pede
        str(uuid.uuid4()),
        "abc",
        str(portfolio.public_id).upper(),
    ]
    for pid in ids:
        quem = pessoas.de_fora if pid == ids[0] else pessoas.admin
        operacoes: list[Callable[[], object]] = [
            lambda: get_portfolio(quem, pid),
            lambda: update_portfolio(quem, pid, {"name": "x"}),
            lambda: archive_portfolio(quem, pid),
            lambda: replace_holdings(quem, pid, _pos(("ITUB4", "50"), ("BBAS3", "50"))),
        ]
        for operacao in operacoes:
            with pytest.raises(PortfolioError) as erro:
                operacao()
            assert (erro.value.code, erro.value.message, erro.value.details) == (
                "portfolio_not_found",
                "Carteira não encontrada.",
                {},
            )
    linha = Portfolio.unscoped.get(pk=portfolio.pk)
    assert (linha.name, linha.archived_at) == ("Minha carteira", None)
    assert PortfolioVersion.unscoped.filter(portfolio=portfolio).count() == 1


def test_v09_member_e_admin_mexem_na_carteira_um_do_outro(pessoas: Pessoas) -> None:
    da_admin = _cria(pessoas)
    do_member = create_portfolio(
        pessoas.member, name="do member", notional=None, holdings=METADE
    )
    for quem, portfolio in ((pessoas.member, da_admin), (pessoas.admin, do_member)):
        pid = str(portfolio.public_id)
        assert get_portfolio(quem, pid).pk == portfolio.pk
        update_portfolio(quem, pid, {"name": "mudada"})
        replace_holdings(quem, pid, _pos(("ITUB4", "50"), ("BBAS3", "50")))
        assert PortfolioVersion.unscoped.filter(portfolio=portfolio).count() == 2


# --- a perda em reais -------------------------------------------------------------------


def test_loss_brl_o_valor_escrito_a_mao() -> None:
    # 100000 * (1 - e^-0,0283415120) = 2794,3658... -> 2794,37
    assert loss_brl(Decimal("100000.00"), Decimal("0.0283415120")) == Decimal("2794.37")


def test_loss_brl_nulo_de_qualquer_lado() -> None:
    assert loss_brl(None, Decimal("0.02")) is None
    assert loss_brl(Decimal("100.00"), None) is None
