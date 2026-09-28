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

Depois dos indicadores vem a segunda fase (M3.2, RF-10 e RF-15), **sempre**, mesmo com falha
na primeira: le de volta as linhas de `gold.fundamental_indicator` gravadas com este
`calculated_at` -- as gravadas, nao os valores calculados, para que a acao que falhou nao
entre no grupo de ninguem --, compara cada uma com os pares (`peers.compare_all`, puro) e
grava uma `gold.peer_comparison` por linha, uma transacao por acao, por
`write_peer_comparison` chamada pelo nome global (a costura do RF-15). Tambem so-acrescimo.
`FundamentalsFailed` so levanta depois das duas fases.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
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
from apps.fundamentals.models import (
    Company,
    FinancialStatement,
    FundamentalIndicator,
    PeerComparison,
)
from apps.fundamentals.peers import (
    INDICATORS,
    Comparison,
    Level,
    PeerInput,
    compare_all,
)

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
class PeerResult:
    """O que aconteceu com a comparacao de uma acao, na segunda fase."""

    ticker: str
    level: Level
    error: str | None = None


@dataclass(frozen=True)
class ComputeReport:
    """O relatorio de uma execucao: uma linha por acao calculada e o resumo.

    `acoes` conta as acoes com balanco (as linhas acima do resumo, falhas inclusive);
    `sem balanco` conta, a parte, as acoes do catalogo cuja companhia nao tem
    `financial_statement` -- essas nao tem linha. `fora de escala` conta as acoes gravadas
    com algum valor anulado por nao caber na coluna (RF-22).

    `peer_results` e a segunda fase: uma por linha de indicador desta execucao. No texto,
    depois das linhas da primeira fase, vem uma linha por comparacao que falhou e o resumo
    `comparacao: ...`; a `calculo: ...` segue por ultimo, contando so a primeira fase.
    """

    results: list[AssetResult]
    without_statements: int
    peer_results: list[PeerResult] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return bool(self.failures())

    def failures(self) -> list[str]:
        """Os tickers que falharam: os da primeira fase, depois os da segunda, marcados."""
        return [r.ticker for r in self.results if r.error] + [
            f"{r.ticker} (comparacao)" for r in self.peer_results if r.error
        ]

    def render(self) -> str:
        lines = [r.render() for r in self.results]
        lines.extend(
            f"{r.ticker}: comparacao FALHOU ({r.error})"
            for r in self.peer_results
            if r.error
        )
        without_group = sum(
            1 for r in self.peer_results if r.error is None and r.level == "none"
        )
        peer_failed = sum(1 for r in self.peer_results if r.error)
        lines.append(
            f"comparacao: {len(self.peer_results)} acoes, {without_group} sem grupo, "
            f"{peer_failed} falhas"
        )
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
        super().__init__(", ".join(report.failures()))
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

    peer_results = _compare(calculated_at)  # sempre, mesmo com falha acima (RF-10)
    report = ComputeReport(results, without_statements, peer_results)
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
        pk=row.pk,
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
        statement = inputs.statements[values.statement_index]
        with transaction.atomic():  # RF-25: uma transacao por acao
            write_indicator(asset, calculated_at, values, statement)
    except Exception as exc:
        return AssetResult(asset.ticker, error=f"{type(exc).__name__}: {exc}")
    return AssetResult(
        asset.ticker,
        reference_date=statement.reference_date,
        pe=values.pe,
        market_cap=values.market_cap,
        market_cap_missing=values.market_cap_missing,
        out_of_scale=values.out_of_scale,
    )


def write_indicator(
    asset: Asset,
    calculated_at: datetime,
    values: IndicatorValues,
    statement: StatementView,
) -> None:
    """A linha de indicadores de `asset` nesta execucao. Sempre `create` (RF-20).

    O `statement` e o balanco de onde `values` saiu, o de indice `values.statement_index`
    em `IndicatorInputs.statements`: a linha aponta para o `pk` dele, sem buscar de novo —
    um balanco gravado entre o calculo e a escrita nao troca o documento da linha.
    """
    FundamentalIndicator.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        statement_id=statement.pk,
        **{field: getattr(values, field) for field in VALUE_FIELDS},
    )


def _compare(calculated_at: datetime) -> list[PeerResult]:
    """A segunda fase (RF-10, RF-15): compara as linhas gravadas nesta execucao."""
    indicators = list(
        FundamentalIndicator.objects.filter(calculated_at=calculated_at)
        .select_related("asset")
        .order_by("asset__ticker")
    )
    comparisons = compare_all(
        [
            PeerInput(
                ticker=row.asset.ticker,
                code_cvm=row.asset.code_cvm or "",
                sector=row.asset.sector,
                subsector=row.asset.subsector,
                segment=row.asset.segment,
                values={name: getattr(row, name) for name in INDICATORS},
            )
            for row in indicators
        ]
    )
    results: list[PeerResult] = []
    for row in indicators:
        comparison = comparisons[row.asset.ticker]
        try:
            with transaction.atomic():  # RF-15: uma transacao por acao
                write_peer_comparison(row, comparison)
        except Exception as exc:
            results.append(
                PeerResult(
                    row.asset.ticker,
                    comparison.level,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        results.append(PeerResult(row.asset.ticker, comparison.level))
    return results


def write_peer_comparison(
    indicator: FundamentalIndicator, comparison: Comparison
) -> None:
    """A comparacao da linha `indicator` com os pares. Sempre `create` (RF-10); `asset` e
    `calculated_at` sao copiados da linha."""
    sector, subsector, segment = comparison.group
    columns: dict[str, object] = {}
    for name in INDICATORS:
        values = comparison.indicators[name]
        columns[f"{name}_peer_median"] = values.median
        columns[f"{name}_percentile"] = values.percentile
        columns[f"{name}_peer_count"] = values.count
    PeerComparison.objects.create(
        indicator=indicator,
        asset_id=indicator.asset_id,
        calculated_at=indicator.calculated_at,
        peer_level=comparison.level,
        group_sector=sector,
        group_subsector=subsector,
        group_segment=segment,
        **columns,
    )
