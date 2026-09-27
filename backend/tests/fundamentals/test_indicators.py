"""`compute_indicators`, `per_share_reason` e `market_cap`: o calculo puro dos indicadores.

Sem banco e sem relogio. Os numeros sao simples e escritos aqui; o esperado de cada um e
conferido a mao no comentario ao lado. O caso base (`base()`): quatro trimestres civis de
2024, plano `general`, consolidado; receita 100 + 110 + 90 + 100 = 400, EBIT
20 + 25 + 15 + 20 = 80, lucro 10 + 12 + 8 + 10 = 40; no ultimo, ativo 1000, caixa 50,
divida 150, PL 400, 60 ON + 40 PN; preco 8,00; ON a 8,00 e PN a 6,00. `today` e
2025-03-31, 90 dias depois do balanco — longe dos 460 da regra 0, salvo nos testes de
`stale_statement`.
"""

from __future__ import annotations

from dataclasses import fields, replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.fundamentals.indicators import (
    ClassTicker,
    IndicatorInputs,
    IndicatorValues,
    PriceView,
    StatementView,
    compute_indicators,
    market_cap,
    per_share_reason,
)

Q4, Q3, Q2, Q1 = (
    date(2024, 12, 31),
    date(2024, 9, 30),
    date(2024, 6, 30),
    date(2024, 3, 31),
)
TODAY = date(2025, 3, 31)  # 90 dias depois de Q4
PRICE = PriceView(date(2025, 3, 28), Decimal("8.00"))
CLASSES = {
    "on": [ClassTicker("XPTO3", Decimal("8.00"))],
    "pn": [ClassTicker("XPTO4", Decimal("6.00"))],
}

# As colunas `Decimal` de `gold.fundamental_indicator`.
DECIMAL_FIELDS = (
    "revenue_ttm",
    "ebit_ttm",
    "net_income_ttm",
    "equity_parent",
    "total_assets",
    "gross_debt",
    "cash",
    "net_debt",
    "net_margin",
    "ebit_margin",
    "roe",
    "net_debt_to_equity",
    "close",
    "eps",
    "bvps",
    "pe",
    "pb",
    "market_cap",
)
PRICE_AND_PER_SHARE = ("price_date", "close", "eps", "bvps", "pe", "pb")
PER_SHARE = ("eps", "bvps", "pe", "pb")
NOT_GENERAL_NULLS = (
    "revenue_ttm",
    "ebit_ttm",
    "net_margin",
    "ebit_margin",
    "gross_debt",
    "cash",
    "net_debt",
    "net_debt_to_equity",
)


def statement(reference_date: date, **overrides: object) -> StatementView:
    base_fields: dict[str, object] = {
        "reference_date": reference_date,
        "scope": "consolidated",
        "account_plan": "general",
        "total_assets": Decimal("1000.00"),
        "cash": Decimal("50.00"),
        "gross_debt": Decimal("150.00"),
        "equity_parent": Decimal("400.00"),
        "revenue": Decimal("100.00"),
        "ebit": Decimal("20.00"),
        "net_income_parent": Decimal("10.00"),
        "shares_on": 60,
        "shares_pn": 40,
        "shares_scale": 1,
        "share_composition": True,
    }
    base_fields.update(overrides)
    return StatementView(**base_fields)  # type: ignore[arg-type]


def base_statements() -> list[StatementView]:
    return [
        statement(Q4),
        statement(
            Q3,
            revenue=Decimal("110.00"),
            ebit=Decimal("25.00"),
            net_income_parent=Decimal("12.00"),
        ),
        statement(
            Q2,
            revenue=Decimal("90.00"),
            ebit=Decimal("15.00"),
            net_income_parent=Decimal("8.00"),
        ),
        statement(Q1),
    ]


def base(**overrides: object) -> IndicatorInputs:
    inputs = IndicatorInputs(
        today=TODAY,
        ticker="XPTO4",
        statements=base_statements(),
        price=PRICE,
        class_tickers=CLASSES,
    )
    return replace(inputs, **overrides)  # type: ignore[arg-type]


def with_latest(**overrides: object) -> IndicatorInputs:
    """O caso base com o ultimo balanco alterado."""
    statements = base_statements()
    statements[0] = replace(statements[0], **overrides)  # type: ignore[arg-type]
    return base(statements=statements)


def value(values: IndicatorValues, field: str) -> object:
    return getattr(values, field)


# --- RF-21: q1..q4 ---------------------------------------------------------------------


def test_rf21_quatro_trimestres_civis_somam_o_isolado() -> None:
    values = compute_indicators(base())
    assert values.statement_index == 0
    assert values.revenue_ttm == Decimal("400.00")  # 100 + 110 + 90 + 100
    assert values.ebit_ttm == Decimal("80.00")  # 20 + 25 + 15 + 20
    assert values.net_income_ttm == Decimal("40.00")  # 10 + 12 + 8 + 10


def test_rf21_camil_trimestres_fora_do_calendario() -> None:
    # Exercicio de marco a fevereiro: 30/11, 31/08, 31/05, 29/02 — intervalos 91, 92, 92.
    statements = [
        statement(date(2024, 11, 30), revenue=Decimal("300.00")),
        statement(date(2024, 8, 31), revenue=Decimal("200.00")),
        statement(date(2024, 5, 31), revenue=Decimal("250.00")),
        statement(date(2024, 2, 29), revenue=Decimal("250.00")),
    ]
    values = compute_indicators(base(statements=statements, today=date(2025, 1, 31)))
    assert values.revenue_ttm == Decimal("1000.00")  # 300 + 200 + 250 + 250
    assert values.net_income_ttm == Decimal("40.00")  # 4 x 10


def test_rf21_buraco_anula_os_doze_meses() -> None:
    # Falta 2024-06-30: de 30/09 a 31/03 sao 183 dias.
    statements = [
        statement(Q4),
        statement(Q3),
        statement(Q1),
        statement(date(2023, 12, 31)),
    ]
    values = compute_indicators(base(statements=statements))
    for field in ("revenue_ttm", "ebit_ttm", "net_income_ttm", "net_margin"):
        assert value(values, field) is None, field
    for field in ("ebit_margin", "roe", "eps", "pe"):
        assert value(values, field) is None, field
    # O que vem so do ultimo balanco nao depende dos trimestres.
    assert values.equity_parent == Decimal("400.00")
    assert values.bvps == Decimal("4.000000")  # 400 / 100
    assert values.per_share_missing is None  # buraco nao e motivo do RF-24


def test_rf21_intervalo_de_87_dias_anula() -> None:
    # Intervalos 87, 91 e 91: so o primeiro fora.
    dates = [
        Q4,
        Q4 - timedelta(days=87),
        Q4 - timedelta(days=178),
        Q4 - timedelta(days=269),
    ]
    statements = [
        replace(s, reference_date=d)
        for s, d in zip(base_statements(), dates, strict=True)
    ]
    assert compute_indicators(base(statements=statements)).revenue_ttm is None


def test_rf21_intervalo_de_94_dias_anula() -> None:
    statements = base_statements()
    statements[3] = replace(statements[3], reference_date=Q2 - timedelta(days=94))
    assert compute_indicators(base(statements=statements)).revenue_ttm is None


def test_rf21_intervalos_de_88_e_93_dias_valem() -> None:
    dates = [
        Q4,
        Q4 - timedelta(days=88),
        Q4 - timedelta(days=181),
        Q4 - timedelta(days=270),
    ]
    statements = [
        replace(s, reference_date=d)
        for s, d in zip(base_statements(), dates, strict=True)
    ]
    # Intervalos 88, 93 e 89.
    assert compute_indicators(base(statements=statements)).revenue_ttm == Decimal(
        "400.00"
    )


def test_rf21_escopo_misto_anula() -> None:
    statements = base_statements()
    statements[2] = replace(statements[2], scope="individual")
    values = compute_indicators(base(statements=statements))
    assert values.revenue_ttm is None
    assert values.ebit_ttm is None
    assert values.net_income_ttm is None


def test_rf21_menos_de_quatro_trimestres_anula() -> None:
    values = compute_indicators(base(statements=base_statements()[:3]))
    assert values.revenue_ttm is None
    assert values.net_income_ttm is None
    assert values.total_assets == Decimal("1000.00")


def test_rf21_valor_nulo_num_trimestre_anula_so_aquele_campo() -> None:
    statements = base_statements()
    statements[2] = replace(statements[2], ebit=None)
    values = compute_indicators(base(statements=statements))
    assert values.ebit_ttm is None
    assert values.ebit_margin is None
    assert values.revenue_ttm == Decimal("400.00")
    assert values.net_income_ttm == Decimal("40.00")


def test_rf21_usa_so_os_quatro_mais_recentes() -> None:
    statements = [
        *base_statements(),
        statement(date(2023, 12, 31), revenue=Decimal("999.00")),
    ]
    assert compute_indicators(base(statements=statements)).revenue_ttm == Decimal(
        "400.00"
    )


# --- RF-22: a tabela Indicadores -------------------------------------------------------


def test_rf22_caso_base_linha_a_linha() -> None:
    values = compute_indicators(base())
    assert values.account_plan == "general"
    assert values.scope == "consolidated"
    assert values.equity_parent == Decimal("400.00")
    assert values.total_assets == Decimal("1000.00")
    assert values.gross_debt == Decimal("150.00")
    assert values.cash == Decimal("50.00")
    assert values.net_debt == Decimal("100.00")  # 150 - 50
    assert values.net_margin == Decimal("0.1000000000")  # 40 / 400
    assert values.ebit_margin == Decimal("0.2000000000")  # 80 / 400
    assert values.roe == Decimal("0.1000000000")  # 40 / 400
    assert values.net_debt_to_equity == Decimal("0.2500000000")  # 100 / 400
    assert values.shares_total == 100  # 60 + 40
    assert values.eps == Decimal("0.400000")  # 40 / 100
    assert values.bvps == Decimal("4.000000")  # 400 / 100
    assert values.price_date == date(2025, 3, 28)
    assert values.close == Decimal("8.000000")
    assert values.pe == Decimal("20.000000")  # 8 / 0,4
    assert values.pb == Decimal("2.000000")  # 8 / 4
    assert values.per_share_missing is None
    assert values.market_cap == Decimal("720.00")  # 8 x 60 + 6 x 40
    assert values.market_cap_missing is None
    assert values.out_of_scale is False


def test_rf22_quantiza_as_casas_das_colunas() -> None:
    values = compute_indicators(with_latest(equity_parent=Decimal("300.00")))
    # 40 / 300 = 0,1333...; 100 / 300 = 0,3333...; 300 / 100 = 3; 8 / 3 = 2,6666...
    assert str(values.roe) == "0.1333333333"
    assert str(values.net_debt_to_equity) == "0.3333333333"
    assert str(values.bvps) == "3.000000"
    assert str(values.pb) == "2.666667"
    assert str(values.revenue_ttm) == "400.00"
    assert str(values.market_cap) == "720.00"


def test_rf22_balanco_nulo_na_silver_fica_nulo() -> None:
    values = compute_indicators(
        with_latest(total_assets=None, cash=None, gross_debt=None, equity_parent=None)
    )
    for field in ("total_assets", "cash", "gross_debt", "equity_parent", "net_debt"):
        assert value(values, field) is None, field
    for field in ("roe", "net_debt_to_equity", "bvps", "pb"):
        assert value(values, field) is None, field
    assert values.net_margin == Decimal("0.1000000000")


def test_rf22_divida_liquida_nula_com_um_dos_dois_nulo() -> None:
    assert compute_indicators(with_latest(cash=None)).net_debt is None
    assert compute_indicators(with_latest(gross_debt=None)).net_debt is None
    values = compute_indicators(with_latest(cash=None))
    assert values.gross_debt == Decimal("150.00")
    assert values.net_debt_to_equity is None


def test_rf22_divida_liquida_negativa() -> None:
    values = compute_indicators(with_latest(cash=Decimal("350.00")))
    assert values.net_debt == Decimal("-200.00")  # 150 - 350
    assert values.net_debt_to_equity == Decimal("-0.5000000000")  # -200 / 400


@pytest.mark.parametrize("revenue", [Decimal("0.00"), Decimal("-25.00")])
def test_rf22_receita_nao_positiva_anula_as_margens(revenue: Decimal) -> None:
    statements = [replace(s, revenue=revenue) for s in base_statements()]
    values = compute_indicators(base(statements=statements))
    assert values.revenue_ttm == revenue * 4
    assert values.net_margin is None
    assert values.ebit_margin is None
    assert values.roe == Decimal("0.1000000000")


def test_rf22_lucro_negativo_da_margem_e_roe_negativos() -> None:
    statements = [
        replace(s, net_income_parent=Decimal("-10.00")) for s in base_statements()
    ]
    values = compute_indicators(base(statements=statements))
    assert values.net_income_ttm == Decimal("-40.00")
    assert values.net_margin == Decimal("-0.1000000000")  # -40 / 400
    assert values.roe == Decimal("-0.1000000000")  # -40 / 400


@pytest.mark.parametrize("equity", [Decimal("0.00"), Decimal("-100.00")])
def test_rf22_pl_nao_positivo_anula_roe_e_alavancagem(equity: Decimal) -> None:
    values = compute_indicators(with_latest(equity_parent=equity))
    assert values.equity_parent == equity
    assert values.roe is None
    assert values.net_debt_to_equity is None
    assert values.pb is None  # bvps <= 0


def test_rf22_pl_negativo_da_vpa_negativo_e_pvp_nulo() -> None:
    values = compute_indicators(with_latest(equity_parent=Decimal("-100.00")))
    assert values.bvps == Decimal("-1.000000")  # -100 / 100
    assert values.pb is None


def test_rf22_quantidade_total_nula_com_uma_classe_nula() -> None:
    values = compute_indicators(with_latest(shares_pn=None))
    assert values.shares_total is None
    assert values.eps is None
    assert values.bvps is None
    assert values.pe is None
    assert values.pb is None


def test_rf22_quantidade_total_zero_fica_nula() -> None:
    values = compute_indicators(with_latest(shares_on=0, shares_pn=0))
    assert values.shares_total is None
    assert values.eps is None
    assert values.bvps is None


def test_rf22_lpa_negativo_da_pl_negativo_gravado() -> None:
    statements = [
        replace(s, net_income_parent=Decimal("-5.00")) for s in base_statements()
    ]
    values = compute_indicators(base(statements=statements))
    assert values.eps == Decimal("-0.200000")  # -20 / 100
    assert values.pe == Decimal("-40.000000")  # 8 / -0,2


def test_rf22_lpa_zero_anula_pl() -> None:
    statements = [
        replace(s, net_income_parent=Decimal("0.00")) for s in base_statements()
    ]
    values = compute_indicators(base(statements=statements))
    assert values.eps == Decimal("0.000000")
    assert values.pe is None
    assert values.pb == Decimal("2.000000")


def test_rf22_sem_preco_anula_preco_e_multiplos() -> None:
    values = compute_indicators(base(price=None))
    assert values.price_date is None
    assert values.close is None
    assert values.pe is None
    assert values.pb is None


@pytest.mark.parametrize("plan", ["bank", "insurance", "unknown"])
def test_rf22_fora_de_general_os_oito_nulos(plan: str) -> None:
    statements = [replace(s, account_plan=plan) for s in base_statements()]
    values = compute_indicators(base(statements=statements))
    for field in NOT_GENERAL_NULLS:
        assert value(values, field) is None, field
    assert values.account_plan == plan
    # O que nao e so-`general` segue calculado.
    assert values.net_income_ttm == Decimal("40.00")
    assert values.equity_parent == Decimal("400.00")
    assert values.total_assets == Decimal("1000.00")
    assert values.roe == Decimal("0.1000000000")
    assert values.eps == Decimal("0.400000")
    assert values.pe == Decimal("20.000000")
    assert values.out_of_scale is False


def test_rf22_plano_e_o_do_ultimo_balanco() -> None:
    # So o ultimo e banco: vale o `account_plan` de `statement`.
    values = compute_indicators(with_latest(account_plan="bank"))
    assert values.account_plan == "bank"
    assert values.revenue_ttm is None
    # E o inverso: o ultimo `general` com um anterior `bank` calcula.
    statements = base_statements()
    statements[1] = replace(statements[1], account_plan="bank")
    assert compute_indicators(base(statements=statements)).revenue_ttm == Decimal(
        "400.00"
    )


def test_rf22_pl_de_um_real_anula_roe_e_liga_fora_de_escala() -> None:
    # Lucro de 25 milhoes por trimestre: 100 milhoes em 12 meses; PL de R$ 1.
    statements = [
        replace(s, net_income_parent=Decimal("25000000.00")) for s in base_statements()
    ]
    statements[0] = replace(statements[0], equity_parent=Decimal("1.00"))
    values = compute_indicators(base(statements=statements))
    assert values.net_income_ttm == Decimal("100000000.00")
    assert values.roe is None  # 10^8 / 1 = 10^8, nao cabe em (18, 10)
    assert values.out_of_scale is True
    assert values.net_debt_to_equity == Decimal("100.0000000000")  # 100 / 1, cabe
    assert values.equity_parent == Decimal("1.00")


def test_rf22_razao_logo_abaixo_do_limite_cabe() -> None:
    statements = [
        replace(s, net_income_parent=Decimal("24999999.99")) for s in base_statements()
    ]
    statements[0] = replace(statements[0], equity_parent=Decimal("1.00"))
    values = compute_indicators(base(statements=statements))
    assert values.roe == Decimal("99999999.9600000000")  # 4 x 24.999.999,99
    assert values.out_of_scale is False


def test_rf22_pl_fora_de_escala_em_coluna_por_acao() -> None:
    # LPA de 4 x 10^-14: 0,04 / 10^12 acoes; P/L = 8 / (4 x 10^-14) = 2 x 10^14 >= 10^12.
    statements = [
        replace(s, net_income_parent=Decimal("0.01")) for s in base_statements()
    ]
    statements[0] = replace(statements[0], shares_on=10**12, shares_pn=0)
    values = compute_indicators(base(statements=statements))
    assert values.pe is None
    assert values.out_of_scale is True


def test_rf26_todo_valor_e_decimal() -> None:
    values = compute_indicators(base())
    for field in DECIMAL_FIELDS:
        v = value(values, field)
        assert type(v) is Decimal, field
    assert type(values.shares_total) is int
    assert type(values.price_date) is date


def test_rf26_os_campos_sao_as_colunas_da_gold() -> None:
    names = {f.name for f in fields(IndicatorValues)}
    assert names == {
        "statement_index",
        "account_plan",
        "scope",
        *DECIMAL_FIELDS,
        "price_date",
        "shares_total",
        "per_share_missing",
        "market_cap_missing",
        "out_of_scale",
    }


# --- RF-24: o motivo por acao ----------------------------------------------------------


def test_rf24_unit_anula_seis_e_mantem_o_resto() -> None:
    values = compute_indicators(base(ticker="TAEE11"))
    assert values.per_share_missing == "unit"
    for field in PRICE_AND_PER_SHARE:
        assert value(values, field) is None, field
    assert values.shares_total == 100
    assert values.roe == Decimal("0.1000000000")
    assert values.revenue_ttm == Decimal("400.00")
    assert values.market_cap == Decimal(
        "720.00"
    )  # a unit tem a capitalizacao da companhia


def test_rf24_stale_statement_a_461_dias_anula_seis() -> None:
    values = compute_indicators(base(today=Q4 + timedelta(days=461)))
    assert values.per_share_missing == "stale_statement"
    for field in PRICE_AND_PER_SHARE:
        assert value(values, field) is None, field
    assert values.shares_total == 100
    assert values.net_income_ttm == Decimal("40.00")
    assert values.roe == Decimal("0.1000000000")


def test_rf24_a_460_dias_nao_e_stale() -> None:
    values = compute_indicators(base(today=Q4 + timedelta(days=460)))
    assert values.per_share_missing is None
    assert values.pe == Decimal("20.000000")
    assert values.market_cap == Decimal("720.00")


def test_rf24_no_share_count_anula_quatro_e_mantem_preco() -> None:
    values = compute_indicators(
        with_latest(
            share_composition=False, shares_on=None, shares_pn=None, shares_scale=None
        )
    )
    assert values.per_share_missing == "no_share_count"
    for field in PER_SHARE:
        assert value(values, field) is None, field
    assert values.price_date == date(2025, 3, 28)
    assert values.close == Decimal("8.000000")


def test_rf24_share_scale_unknown_anula_quatro_por_cima_e_mantem_preco() -> None:
    # Com as quantidades presentes, a tabela calcularia LPA e VPA; o motivo anula por cima.
    values = compute_indicators(with_latest(shares_scale=None))
    assert values.per_share_missing == "share_scale_unknown"
    for field in PER_SHARE:
        assert value(values, field) is None, field
    assert values.price_date == date(2025, 3, 28)
    assert values.close == Decimal("8.000000")
    assert values.shares_total == 100


def test_rf24_no_price_anula_preco_e_multiplos_e_mantem_lpa_e_vpa() -> None:
    values = compute_indicators(base(price=None))
    assert values.per_share_missing == "no_price"
    for field in ("price_date", "close", "pe", "pb"):
        assert value(values, field) is None, field
    assert values.eps == Decimal("0.400000")
    assert values.bvps == Decimal("4.000000")


def test_rf24_nenhum_motivo_grava_nulo() -> None:
    assert compute_indicators(base()).per_share_missing is None


def test_rf24_lpa_nulo_por_pl_nulo_nao_grava_motivo() -> None:
    values = compute_indicators(with_latest(equity_parent=None))
    assert values.bvps is None
    assert values.per_share_missing is None


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        # unit antes de stale_statement
        (base(ticker="TAEE11", today=Q4 + timedelta(days=461)), "unit"),
        # stale_statement antes de no_share_count
        (
            replace(
                with_latest(share_composition=False, shares_scale=None),
                today=Q4 + timedelta(days=461),
            ),
            "stale_statement",
        ),
        # no_share_count antes de no_price
        (replace(with_latest(share_composition=False), price=None), "no_share_count"),
        # share_scale_unknown antes de no_price
        (replace(with_latest(shares_scale=None), price=None), "share_scale_unknown"),
    ],
)
def test_rf24_a_ordem_dos_motivos(inputs: IndicatorInputs, expected: str) -> None:
    assert per_share_reason(inputs) == expected
    assert compute_indicators(inputs).per_share_missing == expected


# --- RF-24b: a capitalizacao -----------------------------------------------------------


def test_rf24b_regra_6_so_on_com_preco() -> None:
    # VALE3: so ON, com preco.
    inputs = replace(
        with_latest(shares_on=100, shares_pn=0),
        ticker="VALE3",
        class_tickers={"on": [ClassTicker("VALE3", Decimal("60.50"))], "pn": []},
    )
    assert market_cap(inputs) == (Decimal("6050.00"), None)  # 60,50 x 100
    values = compute_indicators(inputs)
    assert values.market_cap == Decimal("6050.00")
    assert values.market_cap_missing is None


def test_rf24b_regra_6_soma_as_classes() -> None:
    assert market_cap(base()) == (Decimal("720.00"), None)  # 8 x 60 + 6 x 40


def test_rf24b_nao_depende_do_preco_do_proprio_ticker() -> None:
    values = compute_indicators(base(price=None))
    assert values.market_cap == Decimal("720.00")


def test_rf24b_classe_sem_ticker_e_missing_class_price() -> None:
    # PETR4 sem PETR3 no catalogo.
    inputs = base(
        ticker="PETR4", class_tickers={"pn": [ClassTicker("PETR4", Decimal("30.00"))]}
    )
    assert market_cap(inputs) == (None, "missing_class_price")
    values = compute_indicators(inputs)
    assert values.market_cap is None
    assert values.market_cap_missing == "missing_class_price"


def test_rf24b_classe_com_ticker_sem_preco_e_missing_class_price() -> None:
    inputs = base(
        class_tickers={
            "on": [ClassTicker("XPTO3", None)],
            "pn": [ClassTicker("XPTO4", Decimal("6.00"))],
        }
    )
    assert market_cap(inputs) == (None, "missing_class_price")


def test_rf24b_classe_sem_quantidade_nao_precisa_de_ticker() -> None:
    inputs = replace(
        with_latest(shares_on=100, shares_pn=0),
        class_tickers={"on": [ClassTicker("XPTO3", Decimal("8.00"))]},
    )
    assert market_cap(inputs) == (Decimal("800.00"), None)  # 8 x 100


def test_rf24b_dois_pn_ativos_e_ambiguous_class() -> None:
    inputs = base(
        class_tickers={
            "on": [ClassTicker("XPTO3", Decimal("8.00"))],
            "pn": [
                ClassTicker("XPTO5", Decimal("6.00")),
                ClassTicker("XPTO6", Decimal("6.10")),
            ],
        }
    )
    assert market_cap(inputs) == (None, "ambiguous_class")
    assert compute_indicators(inputs).market_cap_missing == "ambiguous_class"


def test_rf24b_ambiguous_class_com_ou_sem_preco_antes_de_no_price() -> None:
    # Regra 3 antes da 4: dois PN, nenhum com preco.
    inputs = base(
        class_tickers={
            "on": [ClassTicker("XPTO3", None)],
            "pn": [ClassTicker("XPTO5", None), ClassTicker("XPTO6", None)],
        }
    )
    assert market_cap(inputs) == (None, "ambiguous_class")


def test_rf24b_dois_tickers_em_classe_sem_quantidade_nao_e_ambiguo() -> None:
    inputs = replace(
        with_latest(shares_on=100, shares_pn=0),
        class_tickers={
            "on": [ClassTicker("XPTO3", Decimal("8.00"))],
            "pn": [ClassTicker("XPTO5", None), ClassTicker("XPTO6", None)],
        },
    )
    assert market_cap(inputs) == (Decimal("800.00"), None)


def test_rf24b_sem_preco_em_ticker_nenhum_e_no_price() -> None:
    inputs = base(class_tickers={})
    assert market_cap(inputs) == (None, "no_price")


def test_rf24b_regra_4_antes_da_5() -> None:
    # As duas classes tem ticker, nenhum com preco: `no_price`, nao `missing_class_price`.
    inputs = base(
        class_tickers={
            "on": [ClassTicker("XPTO3", None)],
            "pn": [ClassTicker("XPTO4", None)],
        }
    )
    assert market_cap(inputs) == (None, "no_price")
    assert compute_indicators(inputs).market_cap_missing == "no_price"


def test_rf24b_no_share_count() -> None:
    inputs = with_latest(
        share_composition=False, shares_on=None, shares_pn=None, shares_scale=None
    )
    assert market_cap(inputs) == (None, "no_share_count")
    assert compute_indicators(inputs).market_cap_missing == "no_share_count"


def test_rf24b_share_scale_unknown() -> None:
    inputs = with_latest(shares_on=None, shares_pn=None, shares_scale=None)
    assert market_cap(inputs) == (None, "share_scale_unknown")
    assert compute_indicators(inputs).market_cap_missing == "share_scale_unknown"


def test_rf24b_stale_statement_a_461_dias() -> None:
    inputs = base(today=Q4 + timedelta(days=461))
    assert market_cap(inputs) == (None, "stale_statement")
    assert compute_indicators(inputs).market_cap_missing == "stale_statement"


def test_rf24b_stale_statement_antes_de_no_share_count() -> None:
    inputs = replace(
        with_latest(share_composition=False), today=Q4 + timedelta(days=461)
    )
    assert market_cap(inputs) == (None, "stale_statement")


def test_rf24b_a_460_dias_calcula() -> None:
    assert market_cap(base(today=Q4 + timedelta(days=460))) == (Decimal("720.00"), None)


def test_rf24b_unit_tem_o_valor_da_companhia() -> None:
    # TAEE11: a unit nunca e ticker da classe, mas recebe a capitalizacao da companhia.
    values = compute_indicators(base(ticker="TAEE11"))
    assert values.market_cap == Decimal("720.00")
    assert values.per_share_missing == "unit"
