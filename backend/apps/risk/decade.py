"""A decada do ativo e a serie que o motor ve (RF-02 do M2.4), num modulo puro.

A `web` importa este modulo na rota do laboratorio, e a `web` nao tem o motor: aqui so entram a
biblioteca padrao, `apps.assets.models` e `apps.risk.config` -- **nunca** `engine`, `pandas` nem
`apps.risk.compute`, `apps.risk.snapshots` ou `apps.risk.tasks`. Um teste confere pela arvore
sintatica (`tests/risk/test_decada.py`).

- **a serie**: as linhas de `silver.price` com o criterio do `clean_prices` do motor sobre o
  `adj_close` -- nao nulo e maior que zero --, em ordem de data. `compute._bars` delega a
  `valid_bars`, e a producao e o laboratorio veem a mesma serie;
- **o inicio**: o primeiro pregao dessa serie; **o fim**: a mesma data de calendario dez anos
  depois (29/02 vira 28/02, a regra de `period1_for`);
- **a serie do experimento**: os pregoes com data **menor ou igual** ao fim;
- **completa**: o ultimo pregao da serie inteira com data maior ou igual ao fim;
- **suficiente**: a serie do experimento com pelo menos `config.MIN_SESSIONS` pregoes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from apps.assets.models import Asset, Price
from apps.risk import config


def valid_bars(asset: Asset) -> list[Price]:
    """O criterio do `clean_prices` do motor sobre o `adj_close`: nao nulo e > 0, em ordem de data."""
    return [
        p
        for p in Price.objects.filter(asset=asset).order_by("date")
        if p.adj_close is not None and p.adj_close > 0
    ]


def decade_end(first: date) -> date:
    """A mesma data de calendario dez anos depois de `first`; 29/02 vira 28/02."""
    try:
        return first.replace(year=first.year + 10)
    except ValueError:  # 29/02 num ano que nao e bissexto
        return first.replace(year=first.year + 10, day=28)


@dataclass(frozen=True)
class Decade:
    first_price_date: date
    end_date: date
    last_price_date: date
    complete: bool  # last_price_date >= end_date
    sessions: int  # len(series)
    series: list[Price]  # [b for b in bars if b.date <= end_date]  -- <=, nunca <

    @property
    def sufficient(self) -> bool:
        return self.sessions >= config.MIN_SESSIONS


def decade_of(bars: Sequence[Price]) -> Decade | None:
    """A decada de `bars` (a saida de `valid_bars`, em ordem de data); `None` sem barras.

    O inicio e `bars[0]`, nunca `bars[-1]`: o fim se conta do primeiro pregao.
    """
    if not bars:
        return None
    first = bars[0].date
    end = decade_end(first)
    last = bars[-1].date
    series = [b for b in bars if b.date <= end]
    return Decade(
        first_price_date=first,
        end_date=end,
        last_price_date=last,
        complete=last >= end,
        sessions=len(series),
        series=series,
    )
