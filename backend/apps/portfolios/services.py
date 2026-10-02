"""As regras da carteira (M2.2a), como servico: sem DRF (RF-20), a view por cima.

**Todo servico abre `organization_scope(actor.organization_id)`** antes de tocar uma das cinco
tabelas (RF-18): funciona igual pela rota, pelo teste direto ou numa thread, que nao herda o
contexto. A carteira e da organizacao, nao da pessoa: `admin` e `member` leem, mudam e trocam.

**O lado seguro** (RF-09.3): o peso gravado e o que veio. Nada aqui arredonda, normaliza para
somar 100, completa posicao, reordena por peso ou sugere ativo.

`{id}` e o UUID canonico (RF-12): texto que nao e UUID, UUID inexistente, de outra organizacao ou
de carteira arquivada dao o **mesmo** `portfolio_not_found`.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tenancy import organization_scope
from apps.assets.models import Asset
from apps.portfolios.errors import PortfolioError
from apps.portfolios.models import Portfolio, PortfolioHolding, PortfolioVersion

MIN_HOLDINGS = 2
MAX_HOLDINGS = 20
WEIGHTS_TOTAL = Decimal("100")
_CENT = Decimal("0.01")


def _after_portfolio_lock() -> None:
    """Ponto de desvio, sem efeito: entre a trava da carteira e a releitura da versao corrente
    (RF-12). O teste concorrente (V-08) o troca pelo nome global."""


def _before_insert_run() -> None:
    """Ponto de desvio, sem efeito: depois das decisoes do pedido de risco e antes do `insert`
    da execucao (RF-13). O teste concorrente (V-12) o troca pelo nome global."""


def _not_found() -> PortfolioError:
    return PortfolioError("portfolio_not_found", "Carteira não encontrada.", {})


def _public_id(portfolio_id: str) -> uuid.UUID:
    """O UUID **so na forma canonica**: a forma em maiusculas, sem hifens ou com chaves e outra
    carteira, que nao existe."""
    try:
        parsed = uuid.UUID(portfolio_id)
    except ValueError:
        raise _not_found() from None
    if str(parsed) != portfolio_id:
        raise _not_found()
    return parsed


def _get(portfolio_id: str) -> Portfolio:
    """A carteira nao arquivada da organizacao do contexto, pelo `public_id`."""
    portfolio = Portfolio.objects.filter(
        public_id=_public_id(portfolio_id), archived_at__isnull=True
    ).first()
    if portfolio is None:
        raise _not_found()
    return portfolio


def _holdings(raw: Sequence[Mapping[str, Any]]) -> list[tuple[Asset, Decimal]]:
    """A regra da composicao (RF-09.2), na ordem: quantas, cada posicao, a soma. Para na
    primeira etapa que falha. Devolve o ativo e o peso **exatamente** como veio."""
    if not MIN_HOLDINGS <= len(raw) <= MAX_HOLDINGS:
        raise PortfolioError(
            "invalid_holdings",
            "Composição inválida.",
            {"reason": "count_out_of_range", "count": len(raw)},
        )

    tickers = [str(item["ticker"]).strip().upper() for item in raw]
    assets = {a.ticker: a for a in Asset.objects.filter(ticker__in=tickers)}
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for index, (ticker, item) in enumerate(zip(tickers, raw, strict=True)):
        weight: Decimal = item["weight"]
        asset = assets.get(ticker)
        reason: str | None
        if ticker in seen:
            reason = "duplicate"
        elif asset is None:
            reason = "unknown_ticker"
        elif asset.kind != Asset.Kind.STOCK:
            reason = "not_a_stock"
        elif asset.status == Asset.Status.INACTIVE:
            reason = "inactive"
        elif not Decimal(0) < weight <= WEIGHTS_TOTAL:
            reason = "weight_out_of_range"
        else:
            reason = None
        seen.add(ticker)
        if reason is not None:
            items.append({"index": index, "ticker": ticker, "reason": reason})
    if items:
        raise PortfolioError(
            "invalid_holdings",
            "Composição inválida.",
            {"reason": "items", "items": items},
        )

    total = sum((item["weight"] for item in raw), Decimal(0))
    if total != WEIGHTS_TOTAL:
        raise PortfolioError(
            "invalid_holdings",
            "Composição inválida.",
            {"reason": "weights_sum", "sum": format(total, "f")},
        )
    return [(assets[t], item["weight"]) for t, item in zip(tickers, raw, strict=True)]


def _write_version(
    portfolio: Portfolio,
    number: int,
    actor: User,
    holdings: list[tuple[Asset, Decimal]],
    now: datetime,
) -> PortfolioVersion:
    version = PortfolioVersion.objects.create(
        portfolio=portfolio, number=number, created_by=actor, created_at=now
    )
    PortfolioHolding.objects.bulk_create(
        PortfolioHolding(version=version, asset=asset, weight=weight)
        for asset, weight in holdings
    )
    return version


def current_version(portfolio: Portfolio) -> PortfolioVersion:
    """A versao de maior `number`. Nunca nula: toda carteira nasce com a versao 1."""
    version = portfolio.versions.order_by("-number").first()
    if version is None:
        raise RuntimeError(f"carteira {portfolio.pk} sem versao")
    return version


def create_portfolio(
    actor: User,
    *,
    name: str,
    notional: Decimal | None,
    holdings: Sequence[Mapping[str, Any]],
) -> Portfolio:
    """A carteira, a versao 1 e as posicoes, numa transacao (RF-08)."""
    checked = _holdings(holdings)
    now = timezone.now()
    with organization_scope(actor.organization_id), transaction.atomic():
        portfolio = Portfolio.objects.create(
            organization_id=actor.organization_id,
            created_by=actor,
            name=name.strip(),
            notional=notional,
            created_at=now,
            updated_at=now,
        )
        _write_version(portfolio, 1, actor, checked, now)
    return portfolio


def list_portfolios(
    actor: User, *, limit: int = 50, offset: int = 0
) -> tuple[int, list[Portfolio]]:
    """As nao arquivadas da organizacao, da mais nova a mais velha (RF-10)."""
    if not 1 <= limit <= 100:
        raise PortfolioError(
            "invalid_parameter", "`limit` vai de 1 a 100.", {"parameter": "limit"}
        )
    if offset < 0:
        raise PortfolioError(
            "invalid_parameter",
            "`offset` não pode ser negativo.",
            {"parameter": "offset"},
        )
    with organization_scope(actor.organization_id):
        portfolios = (
            Portfolio.objects.filter(archived_at__isnull=True)
            .select_related("created_by")
            .order_by("-created_at", "-id")
        )
        return portfolios.count(), list(portfolios[offset : offset + limit])


def get_portfolio(actor: User, portfolio_id: str) -> Portfolio:
    with organization_scope(actor.organization_id):
        return _get(portfolio_id)


def update_portfolio(
    actor: User, portfolio_id: str, changes: Mapping[str, Any]
) -> Portfolio:
    """Nome e valor aplicado, sem versao nova (RF-11). `changes` traz so as chaves enviadas;
    `notional` nulo tira o valor."""
    with organization_scope(actor.organization_id):
        portfolio = _get(portfolio_id)
        fields = ["updated_at"]
        if "name" in changes:
            portfolio.name = str(changes["name"]).strip()
            fields.append("name")
        if "notional" in changes:
            portfolio.notional = changes["notional"]
            fields.append("notional")
        portfolio.updated_at = timezone.now()
        portfolio.save(update_fields=fields)
        return portfolio


def archive_portfolio(actor: User, portfolio_id: str) -> None:
    """Grava `archived_at` (RF-11). Nada se apaga."""
    with organization_scope(actor.organization_id):
        portfolio = _get(portfolio_id)
        now = timezone.now()
        portfolio.archived_at = now
        portfolio.updated_at = now
        portfolio.save(update_fields=["archived_at", "updated_at"])


def replace_holdings(
    actor: User, portfolio_id: str, holdings: Sequence[Mapping[str, Any]]
) -> Portfolio:
    """A versao `n + 1`, sob a trava da linha da carteira (RF-12). A mesma composicao da
    corrente, em qualquer ordem, nao cria versao."""
    checked = _holdings(holdings)
    with organization_scope(actor.organization_id):
        public_id = _public_id(portfolio_id)
        with transaction.atomic():
            # sem `of` e sem `select_related`: a consulta nao tem juncao, e `FOR UPDATE OF` com o
            # esquema no `db_table` o PostgreSQL recusa
            portfolio = (
                Portfolio.objects.select_for_update()
                .filter(public_id=public_id, archived_at__isnull=True)
                .first()
            )
            if portfolio is None:
                raise _not_found()
            _after_portfolio_lock()
            current = current_version(portfolio)
            existing = {(h.asset_id, h.weight) for h in current.holdings.all()}
            if existing == {(asset.pk, weight) for asset, weight in checked}:
                return portfolio
            now = timezone.now()
            _write_version(portfolio, current.number + 1, actor, checked, now)
            portfolio.updated_at = now
            portfolio.save(update_fields=["updated_at"])
            return portfolio


def loss_brl(notional: Decimal | None, var: Decimal | None) -> Decimal | None:
    """A perda em reais do VaR (RF-16): `notional * (1 - e^-var)`, em centavos."""
    if notional is None or var is None:
        return None
    return (notional * (1 - (-var).exp())).quantize(_CENT, rounding=ROUND_HALF_UP)
