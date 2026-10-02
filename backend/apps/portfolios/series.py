"""A serie da carteira (M2.2a, RF-06): o indice que vai ao motor como `close`.

**So a biblioteca padrao e o ORM** (D-59): a `web` calcula a serie para gravar o manifesto da
execucao e nao tem `pandas`; o `worker` passa pelo mesmo `build` e chega ao mesmo indice, bit a
bit, e ao mesmo hash.

- **As datas** sao a interseccao das datas em que cada acao da versao tem `adj_close > 0`.
- **O retorno** de cada data e `R_k = sum_i (w_i / 100) * (adj_i(d_k) / adj_i(d_{k-1}) - 1)`:
  pesos fixos, rebalanceados a cada data. Uma lacuna da serie da o retorno de varios pregoes numa
  data so.
- **O indice** e `I_0 = 1.0` e `I_k = I_{k-1} * (1 + R_k)`.
- **Em `float`**, com `float(adj_close)` e `float(w_i) / 100`, nessa ordem, e a soma **na ordem
  do ticker**: a soma de `float` nao e associativa, e outra ordem daria outro indice.
- **O hash** e o SHA-256 do texto com uma linha `f"{d.isoformat()}|{I!r}\\n"` por data: o `repr`
  de `float` e exato e deterministico.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import pairwise

from apps.assets.models import Price
from apps.portfolios.models import PortfolioVersion


@dataclass(frozen=True)
class AssetCoverage:
    """O historico de uma acao sozinha, sem a interseccao: o que o `insufficient_history`
    mostra de cada uma."""

    ticker: str
    first_date: date | None
    sessions: int


@dataclass(frozen=True)
class PortfolioSeries:
    dates: tuple[date, ...]
    index: tuple[float, ...]  # I_0 = 1.0
    sha256: str
    price_run_id: int | None  # None quando a serie e vazia
    coverage: tuple[AssetCoverage, ...]  # em ordem de ticker


def compute(
    prices: Mapping[str, Sequence[tuple[date, Decimal]]],
    weights: Mapping[str, Decimal],
) -> tuple[tuple[date, ...], tuple[float, ...]]:
    """As datas e o indice da carteira, a partir dos precos e dos pesos de cada ticker.

    `prices` tem uma entrada para cada ticker de `weights`, inclusive a vazia.
    """
    tickers = sorted(weights)  # a soma sai sempre na ordem do ticker
    by_date = {t: dict(prices[t]) for t in tickers}
    dates = sorted(set.intersection(*(set(by_date[t]) for t in tickers)))
    index = [1.0] if dates else []
    # float(Decimal) / 100, nessa ordem
    w = {t: float(weights[t]) / 100 for t in tickers}
    for prev, cur in pairwise(dates):
        r = 0.0
        for t in tickers:
            r += w[t] * (float(by_date[t][cur]) / float(by_date[t][prev]) - 1)
        index.append(index[-1] * (1 + r))
    return tuple(dates), tuple(index)


def series_sha256(dates: Sequence[date], index: Sequence[float]) -> str:
    text = "".join(
        f"{d.isoformat()}|{v!r}\n" for d, v in zip(dates, index, strict=True)
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(
    version: PortfolioVersion, *, first: date | None = None, last: date | None = None
) -> PortfolioSeries:
    """A serie da versao, lida de `silver.price` numa consulta so.

    Quem chama ja esta sob `organization_scope`: as posicoes vem pelo gerente com escopo. Toda
    posicao entra em `prices`, a sem preco com a lista vazia -- e a interseccao com ela e vazia.
    `first` e `last` filtram as datas, inclusive.

    `price_run_id` e o maior `run_id` entre as linhas **das datas da interseccao**, de todas as
    posicoes; `coverage` conta as linhas de cada acao sozinha.
    """
    weights: dict[str, Decimal] = {}
    asset_ids: list[int] = []
    for holding in version.holdings.select_related("asset"):
        weights[holding.asset.ticker] = holding.weight
        asset_ids.append(holding.asset_id)

    rows = Price.objects.filter(asset__in=asset_ids, adj_close__gt=0)
    if first is not None:
        rows = rows.filter(date__gte=first)
    if last is not None:
        rows = rows.filter(date__lte=last)

    prices: dict[str, list[tuple[date, Decimal]]] = {t: [] for t in weights}
    runs: dict[tuple[str, date], int] = {}
    for ticker, day, adj_close, run_id in rows.order_by(
        "asset__ticker", "date"
    ).values_list("asset__ticker", "date", "adj_close", "run_id"):
        prices[ticker].append((day, adj_close))
        runs[(ticker, day)] = run_id

    dates, index = compute(prices, weights)
    in_series = set(dates)
    price_run_id = max(
        (run_id for (_, day), run_id in runs.items() if day in in_series),
        default=None,
    )
    coverage = tuple(
        AssetCoverage(
            ticker=t,
            first_date=prices[t][0][0] if prices[t] else None,
            sessions=len(prices[t]),
        )
        for t in sorted(weights)
    )
    return PortfolioSeries(
        dates=dates,
        index=index,
        sha256=series_sha256(dates, index),
        price_run_id=price_run_id,
        coverage=coverage,
    )
