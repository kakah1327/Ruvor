"""A orquestracao do calculo dos indicadores: laco por acao, transacao por acao, escrita e
relatorio (RF-20, RF-23, RF-25, RF-27).

O molde e `apps/analytics/compute.py` (`run_compute_metrics`, `MetricsFailed`,
`write_metrics`). Como la, nao ha `CollectionRun` nem escrita em `bronze` (D-60), e a
`bronze` nao e lida: tudo vem de `silver.asset`, `silver.company`,
`silver.financial_statement` e `silver.price`.

`calculated_at` e o `now()` de **uma** chamada, compartilhado por todas as acoes da execucao;
`today` e a data local dele. O calculo (`compute_indicators`, puro) roda **fora** da
transacao; so a escrita entra no `atomic()` de cada acao. `write_indicator` e chamada pelo
nome global: e a costura do RF-25, que o teste substitui com `monkeypatch.setattr`.

`gold.fundamental_indicator` e so-acrescimo (RF-20): nenhum caminho daqui faz `update` ou
`delete`. Recalcular insere linha nova.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset, Price
from apps.fundamentals.indicators import (
    ClassTicker,
    IndicatorInputs,
    IndicatorValues,
    PriceView,
    StatementView,
    compute_indicators,
    ticker_suffix,
)
from apps.fundamentals.models import Company, FinancialStatement, FundamentalIndicator

PRICE_WINDOW_DAYS = 10  # RF-23: no maximo 10 dias corridos antes da data local

# "Ticker da classe" (spec, Capitalizacao): sufixo 3 e ON; 4 a 8, PN. Unit (11) nunca entra.
ON_SUFFIXES = frozenset({"3"})
PN_SUFFIXES = frozenset({"4", "5", "6", "7", "8"})

# As colunas de `gold.fundamental_indicator` que vem de `IndicatorValues`, alem de `asset`,
# `calculated_at` e `statement`.
VALUE_FIELDS = (
    "account_plan",
    "scope",
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
    "price_date",
    "close",
    "shares_total",
    "eps",
    "bvps",
    "pe",
    "pb",
    "per_share_missing",
    "market_cap",
    "market_cap_missing",
)


@dataclass(frozen=True)
class AssetResult:
    """Uma linha do relatorio: o que aconteceu com uma acao que tinha balanco."""

    ticker: str
    reference_date: date | None = None
    pe: Decimal | None = None
    market_cap: Decimal | None = None
    market_cap_missing: str | None = None
    out_of_scale: bool = False
    error: str | None = None

    def render(self) -> str:
        if self.error is not None:
            return f"{self.ticker}: FALHOU ({self.error})"
        pe = "-" if self.pe is None else str(self.pe)
        # Sem valor e sem motivo so quando a capitalizacao nao coube na coluna (RF-22).
        if self.market_cap is not None:
            cap = str(self.market_cap)
        else:
            cap = self.market_cap_missing or "-"
        return f"{self.ticker}: {self.reference_date}, pe {pe}, market_cap {cap}"


@dataclass(frozen=True)
class ComputeReport:
    """O relatorio de uma execucao: uma linha por acao calculada e o resumo.

    `acoes` conta as acoes com balanco (as linhas acima do resumo, falhas inclusive);
    `sem balanco` conta, a parte, as acoes do catalogo cuja companhia nao tem
    `financial_statement` -- essas nao tem linha. `fora de escala` conta as acoes gravadas
    com algum valor anulado por nao caber na coluna (RF-22).
    """

    results: list[AssetResult]
    without_statements: int

    @property
    def failed(self) -> bool:
        return any(r.error for r in self.results)

    def render(self) -> str:
        lines = [r.render() for r in self.results]
        out_of_scale = sum(
            1 for r in self.results if r.error is None and r.out_of_scale
        )
        failed = sum(1 for r in self.results if r.error)
        lines.append(
            f"calculo: {len(self.results)} acoes, {self.without_statements} sem balanco, "
            f"{out_of_scale} fora de escala, {failed} falhas"
        )
        return "\n".join(lines)


class FundamentalsFailed(Exception):
    """Alguma acao falhou. `report` e o relatorio inteiro, para a casca imprimir."""

    def __init__(self, report: ComputeReport) -> None:
        super().__init__(", ".join(r.ticker for r in report.results if r.error))
        self.report = report


def run_compute_fundamentals(
    *, now: Callable[[], datetime] = timezone.now
) -> ComputeReport:
    """Calcula e grava os indicadores das acoes do catalogo com balanco, uma de cada vez."""
    calculated_at = now()  # uma vez: e o que identifica a execucao em `gold`
    today = timezone.localdate(calculated_at)
    assets = list(
        Asset.objects.filter(
            kind=Asset.Kind.STOCK, status=Asset.Status.ACTIVE
        ).order_by("ticker")
    )
    statements = _statements({a.code_cvm for a in assets if a.code_cvm})
    prices = _valid_prices(assets, today)
    classes = _class_tickers(assets, prices)

    results: list[AssetResult] = []
    without_statements = 0
    for asset in assets:
        views = statements.get(asset.code_cvm or "")
        if not views:
            without_statements += 1
            continue
        inputs = IndicatorInputs(
            today=today,
            ticker=asset.ticker,
            statements=views,
            price=prices.get(asset.pk),
            class_tickers=classes.get(asset.code_cvm or "", {}),
        )
        results.append(_compute_asset(asset, calculated_at, inputs))

    report = ComputeReport(results, without_statements)
    if report.failed:
        raise FundamentalsFailed(report)
    return report


def _statements(codes: set[str]) -> dict[str, list[StatementView]]:
    """Os balancos de cada companhia de `codes`, por `code_cvm`, `reference_date`
    decrescente."""
    company_codes = dict(
        Company.objects.filter(code_cvm__in=codes).values_list("pk", "code_cvm")
    )
    by_code: dict[str, list[StatementView]] = {}
    rows = FinancialStatement.objects.filter(company_id__in=company_codes).order_by(
        "company_id", "-reference_date"
    )
    for row in rows:
        by_code.setdefault(company_codes[row.company_id], []).append(_view(row))
    return by_code


def _view(row: FinancialStatement) -> StatementView:
    return StatementView(
        reference_date=row.reference_date,
        scope=row.scope,
        account_plan=row.account_plan,
        total_assets=row.total_assets,
        cash=row.cash,
        gross_debt=row.gross_debt,
        equity_parent=row.equity_parent,
        revenue=row.revenue,
        ebit=row.ebit,
        net_income_parent=row.net_income_parent,
        shares_on=row.shares_on,
        shares_pn=row.shares_pn,
        shares_scale=row.shares_scale,
        share_composition=row.share_composition,
    )


def _valid_prices(assets: list[Asset], today: date) -> dict[int, PriceView]:
    """O preco valido de cada acao (RF-23), por `asset.pk`: o `close` do ultimo pregao com
    `date` entre `today - 10 dias` e `today`. Mais antigo que isso, a acao fica de fora."""
    rows = (
        Price.objects.filter(
            asset__in=assets,
            date__lte=today,
            date__gte=today - timedelta(days=PRICE_WINDOW_DAYS),
        )
        .order_by("asset_id", "-date")
        .values_list("asset_id", "date", "close")
    )
    valid: dict[int, PriceView] = {}
    for asset_id, day, close in rows:
        if asset_id not in valid:  # o primeiro de cada acao e o mais recente
            valid[asset_id] = PriceView(date=day, close=close)
    return valid


def _class_tickers(
    assets: list[Asset], prices: dict[int, PriceView]
) -> dict[str, dict[str, list[ClassTicker]]]:
    """Os tickers de classe de cada companhia, por `code_cvm`: `"on"` e `"pn"`.

    Sai de `assets`, que ja sao so os `kind = stock` e `status = active`: ticker inativo
    nao entra (spec, Capitalizacao). O sufixo vem de `ticker_suffix`, a regex
    `^[A-Z0-9]{4}(\\d{1,2})$`.
    """
    classes: dict[str, dict[str, list[ClassTicker]]] = {}
    for asset in assets:
        if not asset.code_cvm:
            continue
        suffix = ticker_suffix(asset.ticker)
        if suffix in ON_SUFFIXES:
            kind = "on"
        elif suffix in PN_SUFFIXES:
            kind = "pn"
        else:
            continue
        price = prices.get(asset.pk)
        classes.setdefault(asset.code_cvm, {}).setdefault(kind, []).append(
            ClassTicker(asset.ticker, None if price is None else price.close)
        )
    return classes


def _compute_asset(
    asset: Asset, calculated_at: datetime, inputs: IndicatorInputs
) -> AssetResult:
    try:
        values = compute_indicators(inputs)  # fora da transacao: e puro
        with transaction.atomic():  # RF-25: uma transacao por acao
            write_indicator(asset, calculated_at, values)
    except Exception as exc:
        return AssetResult(asset.ticker, error=f"{type(exc).__name__}: {exc}")
    return AssetResult(
        asset.ticker,
        reference_date=inputs.statements[values.statement_index].reference_date,
        pe=values.pe,
        market_cap=values.market_cap,
        market_cap_missing=values.market_cap_missing,
        out_of_scale=values.out_of_scale,
    )


def write_indicator(
    asset: Asset, calculated_at: datetime, values: IndicatorValues
) -> None:
    """A linha de indicadores de `asset` nesta execucao. Sempre `create` (RF-20).

    O `statement` e o de indice `values.statement_index` entre os balancos da companhia em
    `reference_date` decrescente -- a mesma ordem de `IndicatorInputs.statements`.
    """
    statement = FinancialStatement.objects.filter(
        company__code_cvm=asset.code_cvm
    ).order_by("-reference_date")[values.statement_index]
    FundamentalIndicator.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        statement=statement,
        **{field: getattr(values, field) for field in VALUE_FIELDS},
    )
