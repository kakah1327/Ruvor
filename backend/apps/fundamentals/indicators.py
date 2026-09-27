"""Os indicadores fundamentalistas de uma acao, puros (RF-21 a RF-24b, RF-26).

Sem ORM, sem relogio e sem `silver.price`: quem chama (`compute.py`) le a `silver`, filtra
o preco pelo RF-23 e entrega tudo em `IndicatorInputs`; `today` e a data local de
`calculated_at`. Toda aritmetica em `Decimal`, contexto padrao; a quantizacao as casas das
colunas de `gold.fundamental_indicator` fica para o fim.

A ordem de aplicacao e contrato do plano:

1. `q1..q4` (RF-21): os quatro primeiros de `statements`, se cada intervalo entre
   `reference_date` consecutivas esta em 88..93 dias e os quatro tem o mesmo `scope`;
2. a tabela Indicadores da spec, com os nulos dela e o "so `general`" pelo `account_plan`
   de `statement`;
3. fora de escala (RF-22): valor que nao cabe na coluna vira nulo e liga `out_of_scale`;
4. o motivo por acao (RF-24), `per_share_reason`, anulando por cima as colunas dele;
5. a capitalizacao (RF-24b), `market_cap`, regras 0 a 6 na ordem da spec.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import pairwise

GENERAL = "general"
TTM_QUARTERS = 4
MIN_QUARTER_DAYS = 88
MAX_QUARTER_DAYS = 93
STALE_DAYS = 460
UNIT_SUFFIX = "11"
TICKER_SUFFIX = re.compile(r"^[A-Z0-9]{4}(\d{1,2})$")

# As casas das colunas: `(22, 2)` em reais, `(18, 10)` razao, `(18, 6)` por acao.
MONEY_PLACES = Decimal("0.01")
RATIO_PLACES = Decimal("0.0000000001")
PER_SHARE_PLACES = Decimal("0.000001")
MONEY_LIMIT = Decimal(10) ** 20
RATIO_LIMIT = Decimal(10) ** 8
PER_SHARE_LIMIT = Decimal(10) ** 12

MONEY_FIELDS = (
    "revenue_ttm",
    "ebit_ttm",
    "net_income_ttm",
    "equity_parent",
    "total_assets",
    "gross_debt",
    "cash",
    "net_debt",
)
RATIO_FIELDS = ("net_margin", "ebit_margin", "roe", "net_debt_to_equity")
PER_SHARE_FIELDS = ("close", "eps", "bvps", "pe", "pb")

# RF-24: a lista fechada, na ordem, com as colunas que cada motivo anula.
_PRICE_AND_PER_SHARE = ("price_date", "close", "eps", "bvps", "pe", "pb")
_PER_SHARE = ("eps", "bvps", "pe", "pb")
REASON_NULLS: dict[str, tuple[str, ...]] = {
    "unit": _PRICE_AND_PER_SHARE,
    "stale_statement": _PRICE_AND_PER_SHARE,
    "no_share_count": _PER_SHARE,
    "share_scale_unknown": _PER_SHARE,
    "no_price": ("price_date", "close", "pe", "pb"),
}


@dataclass(frozen=True)
class StatementView:
    """As colunas de `silver.financial_statement` que o calculo usa."""

    reference_date: date
    scope: str
    account_plan: str
    total_assets: Decimal | None
    cash: Decimal | None
    gross_debt: Decimal | None
    equity_parent: Decimal | None
    revenue: Decimal | None
    ebit: Decimal | None
    net_income_parent: Decimal | None
    shares_on: int | None
    shares_pn: int | None
    shares_scale: int | None
    share_composition: bool


@dataclass(frozen=True)
class PriceView:
    """O preco valido de um ticker (RF-23): o `close` do pregao `date`."""

    date: date
    close: Decimal


@dataclass(frozen=True)
class ClassTicker:
    """Um ticker ativo de uma classe (ON ou PN), com o preco valido ou `None`."""

    ticker: str
    close: Decimal | None


@dataclass(frozen=True)
class IndicatorInputs:
    today: date  # data local de calculated_at
    ticker: str
    statements: list[StatementView]  # da companhia, reference_date decrescente
    price: PriceView | None  # do proprio ticker, ja filtrado pelo RF-23
    class_tickers: dict[str, list[ClassTicker]]  # "on"/"pn" -> tickers ativos da classe


@dataclass(frozen=True)
class IndicatorValues:
    """As colunas de `gold.fundamental_indicator` menos `asset`, `calculated_at` e
    `statement`; mais o `statement_index` usado e `out_of_scale`."""

    statement_index: int
    account_plan: str
    scope: str
    revenue_ttm: Decimal | None
    ebit_ttm: Decimal | None
    net_income_ttm: Decimal | None
    equity_parent: Decimal | None
    total_assets: Decimal | None
    gross_debt: Decimal | None
    cash: Decimal | None
    net_debt: Decimal | None
    net_margin: Decimal | None
    ebit_margin: Decimal | None
    roe: Decimal | None
    net_debt_to_equity: Decimal | None
    price_date: date | None
    close: Decimal | None
    shares_total: int | None
    eps: Decimal | None
    bvps: Decimal | None
    pe: Decimal | None
    pb: Decimal | None
    per_share_missing: str | None
    market_cap: Decimal | None
    market_cap_missing: str | None
    out_of_scale: bool


def ticker_suffix(ticker: str) -> str | None:
    """O sufixo numerico do ticker (`PETR4` -> `4`, `TAEE11` -> `11`); `None` se nao casa."""
    found = TICKER_SUFFIX.match(ticker)
    return found.group(1) if found else None


def quarters(statements: list[StatementView]) -> list[StatementView] | None:
    """`q1..q4` (RF-21), ou `None` se nao ha quatro trimestres consecutivos no mesmo
    escopo."""
    if len(statements) < TTM_QUARTERS:
        return None
    window = statements[:TTM_QUARTERS]
    if len({item.scope for item in window}) != 1:
        return None
    for newer, older in pairwise(window):
        days = (newer.reference_date - older.reference_date).days
        if not MIN_QUARTER_DAYS <= days <= MAX_QUARTER_DAYS:
            return None
    return window


def is_stale(statement: StatementView, today: date) -> bool:
    """Regra 0 da Capitalizacao: mais de 460 dias entre o balanco e `today`."""
    return (today - statement.reference_date).days > STALE_DAYS


def per_share_reason(inputs: IndicatorInputs) -> str | None:
    """O primeiro motivo do RF-24 que casa, na ordem da spec; `None` se nenhum."""
    statement = inputs.statements[0]
    if ticker_suffix(inputs.ticker) == UNIT_SUFFIX:
        return "unit"
    if is_stale(statement, inputs.today):
        return "stale_statement"
    if not statement.share_composition:
        return "no_share_count"
    if statement.shares_scale is None:
        return "share_scale_unknown"
    if inputs.price is None:
        return "no_price"
    return None


def market_cap(inputs: IndicatorInputs) -> tuple[Decimal | None, str | None]:
    """A capitalizacao (RF-24b): `(valor, None)` ou `(None, motivo)`, regras 0 a 6 na
    ordem da spec. O valor sai sem quantizar."""
    statement = inputs.statements[0]
    if is_stale(statement, inputs.today):
        return None, "stale_statement"
    if not statement.share_composition:
        return None, "no_share_count"
    if statement.shares_scale is None:
        return None, "share_scale_unknown"
    quantities = {"on": statement.shares_on or 0, "pn": statement.shares_pn or 0}
    held = [kind for kind in ("on", "pn") if quantities[kind] > 0]
    tickers = {kind: inputs.class_tickers.get(kind, []) for kind in ("on", "pn")}
    if any(len(tickers[kind]) > 1 for kind in held):
        return None, "ambiguous_class"
    if not any(item.close is not None for kind in tickers for item in tickers[kind]):
        return None, "no_price"
    if any(not tickers[kind] or tickers[kind][0].close is None for kind in held):
        return None, "missing_class_price"
    total = Decimal(0)
    for kind in held:
        close = tickers[kind][0].close
        assert close is not None  # a regra 5 acima garante
        total += close * quantities[kind]
    return total, None


def _ttm(window: list[StatementView] | None, field: str) -> Decimal | None:
    if window is None:
        return None
    values: list[Decimal | None] = [getattr(item, field) for item in window]
    if any(value is None for value in values):
        return None
    return sum((value for value in values if value is not None), Decimal(0))


def _fit(value: Decimal | None, places: Decimal, limit: Decimal) -> Decimal | None:
    """Quantiza `value` as casas da coluna; `None` se nao cabe (RF-22)."""
    if value is None or abs(value) >= limit:
        return None
    quantized = value.quantize(places)
    return None if abs(quantized) >= limit else quantized


def compute_indicators(inputs: IndicatorInputs) -> IndicatorValues:
    """Os indicadores de uma acao, na ordem de aplicacao do plano."""
    if not inputs.statements:
        raise ValueError(f"{inputs.ticker}: sem financial_statement")
    statement = inputs.statements[0]
    general = statement.account_plan == GENERAL

    # 1. q1..q4 (RF-21).
    window = quarters(inputs.statements)

    # 2. A tabela Indicadores.
    revenue_ttm = _ttm(window, "revenue") if general else None
    ebit_ttm = _ttm(window, "ebit") if general else None
    net_income_ttm = _ttm(window, "net_income_parent")
    equity = statement.equity_parent
    gross_debt = statement.gross_debt if general else None
    cash = statement.cash if general else None
    net_debt = (
        gross_debt - cash if gross_debt is not None and cash is not None else None
    )
    revenue_positive = revenue_ttm is not None and revenue_ttm > 0
    net_margin = (
        net_income_ttm / revenue_ttm
        if net_income_ttm is not None and revenue_ttm is not None and revenue_positive
        else None
    )
    ebit_margin = (
        ebit_ttm / revenue_ttm
        if ebit_ttm is not None and revenue_ttm is not None and revenue_positive
        else None
    )
    roe = (
        net_income_ttm / equity
        if net_income_ttm is not None and equity is not None and equity > 0
        else None
    )
    net_debt_to_equity = (
        net_debt / equity
        if net_debt is not None and equity is not None and equity > 0
        else None
    )
    shares_total: int | None = None
    if statement.shares_on is not None and statement.shares_pn is not None:
        shares_total = (statement.shares_on + statement.shares_pn) or None
    eps = (
        net_income_ttm / shares_total
        if net_income_ttm is not None and shares_total is not None
        else None
    )
    bvps = (
        equity / shares_total
        if equity is not None and shares_total is not None
        else None
    )
    price = inputs.price
    close = price.close if price is not None else None
    pe = close / eps if close is not None and eps is not None and eps != 0 else None
    pb = close / bvps if close is not None and bvps is not None and bvps > 0 else None

    # 3. Fora de escala (RF-22), com a quantizacao as casas das colunas.
    raw: dict[str, Decimal | None] = {
        "revenue_ttm": revenue_ttm,
        "ebit_ttm": ebit_ttm,
        "net_income_ttm": net_income_ttm,
        "equity_parent": equity,
        "total_assets": statement.total_assets,
        "gross_debt": gross_debt,
        "cash": cash,
        "net_debt": net_debt,
        "net_margin": net_margin,
        "ebit_margin": ebit_margin,
        "roe": roe,
        "net_debt_to_equity": net_debt_to_equity,
        "close": close,
        "eps": eps,
        "bvps": bvps,
        "pe": pe,
        "pb": pb,
    }
    fitted: dict[str, Decimal | None] = {}
    out_of_scale = False
    for fields, places, limit in (
        (MONEY_FIELDS, MONEY_PLACES, MONEY_LIMIT),
        (RATIO_FIELDS, RATIO_PLACES, RATIO_LIMIT),
        (PER_SHARE_FIELDS, PER_SHARE_PLACES, PER_SHARE_LIMIT),
    ):
        for field in fields:
            fitted[field] = _fit(raw[field], places, limit)
            if raw[field] is not None and fitted[field] is None:
                out_of_scale = True

    # 4. O motivo por acao (RF-24), anulando por cima as colunas dele.
    reason = per_share_reason(inputs)
    nulled = set(REASON_NULLS[reason]) if reason is not None else set()
    kept = {field: None if field in nulled else fitted[field] for field in fitted}
    price_date = (
        price.date if price is not None and "price_date" not in nulled else None
    )

    # 5. A capitalizacao (RF-24b).
    cap, cap_reason = market_cap(inputs)
    fitted_cap = _fit(cap, MONEY_PLACES, MONEY_LIMIT)
    if cap is not None and fitted_cap is None:
        out_of_scale = True

    return IndicatorValues(
        statement_index=0,
        account_plan=statement.account_plan,
        scope=statement.scope,
        revenue_ttm=kept["revenue_ttm"],
        ebit_ttm=kept["ebit_ttm"],
        net_income_ttm=kept["net_income_ttm"],
        equity_parent=kept["equity_parent"],
        total_assets=kept["total_assets"],
        gross_debt=kept["gross_debt"],
        cash=kept["cash"],
        net_debt=kept["net_debt"],
        net_margin=kept["net_margin"],
        ebit_margin=kept["ebit_margin"],
        roe=kept["roe"],
        net_debt_to_equity=kept["net_debt_to_equity"],
        price_date=price_date,
        close=kept["close"],
        shares_total=shares_total,
        eps=kept["eps"],
        bvps=kept["bvps"],
        pe=kept["pe"],
        pb=kept["pb"],
        per_share_missing=reason,
        market_cap=fitted_cap,
        market_cap_missing=cap_reason,
        out_of_scale=out_of_scale,
    )
