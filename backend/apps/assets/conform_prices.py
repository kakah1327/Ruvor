"""Conformacao: da resposta crua do `chart` v8 do Yahoo para o que vira `silver.price` e
`silver.corporate_event`.

Funcoes puras sobre dicionarios, no molde de `conform.py` (que e do catalogo). Nada aqui
importa modelo, abre transacao ou chama o cliente — isso e do `prices`. Tambem nao calcula
`log_return`: ele depende do antecessor no banco, e nasce em `write_conformed`.

A forma da resposta esta na spec, em "Contratos externos → A fonte": `chart.result[0]` com
`meta`, `timestamp[]`, `indicators.quote[0].{open,high,low,close,volume}[]`,
`indicators.adjclose[0].adjclose[]` e `events.{dividends,splits}` como dicionarios
indexados pelo timestamp em string. `events`, `events.dividends` e `events.splits` sao
opcionais: ausencia e zero eventos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from zoneinfo import ZoneInfo

q6 = Decimal("0.000001")
Q4 = Decimal("0.0001")


def quantize(v: Any) -> Decimal:
    """Preco vindo como float do JSON, quantizado a seis casas (RF-08)."""
    return Decimal(str(v)).quantize(q6)


@dataclass(frozen=True)
class Bar:
    """Um pregao por vir a `silver.price`, sem o `log_return`."""

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal
    volume: int


@dataclass(frozen=True)
class Event:
    """Um evento corporativo por vir a `silver.corporate_event`.

    `kind` e texto, nao `CorporateEvent.Kind`: este modulo nao importa modelo; quem
    grava mapeia.
    """

    date: date
    kind: Literal["dividend", "split"]
    amount: Decimal | None = None
    numerator: Decimal | None = None
    denominator: Decimal | None = None


@dataclass(frozen=True)
class ConformedChart:
    """O resultado de conformar uma resposta: pregoes, eventos e quantos foram descartados."""

    bars: list[Bar]
    events: list[Event]
    discarded: int


def _trading_date(ts: int, meta: dict[str, Any]) -> date:
    """RF-06: a data do pregao e o timestamp convertido para o fuso da bolsa, nunca UTC."""
    return datetime.fromtimestamp(ts, ZoneInfo(meta["exchangeTimezoneName"])).date()


def conform_chart(payload: dict[str, Any]) -> ConformedChart:
    """Conforma `chart.result[0]`. Sem `result[0]` levanta `ValueError` — defesa: quem
    chama ja filtrou a resposta sem serie (404) antes.

    Pregao com `close` ou `adj_close` nulo e descartado e contado (RF-06). Cada item de
    `events.dividends` vira `Event(kind="dividend")` e cada `events.splits` vira
    `Event(kind="split")` (RF-09).
    """
    results = (payload.get("chart") or {}).get("result") or []
    if not results:
        raise ValueError("payload sem chart.result[0]")
    result = results[0]
    meta = result["meta"]
    quote = result["indicators"]["quote"][0]
    adjclose = result["indicators"]["adjclose"][0]["adjclose"]

    bars: list[Bar] = []
    discarded = 0
    for i, ts in enumerate(result["timestamp"]):
        close = quote["close"][i]
        adj_close = adjclose[i]
        if close is None or adj_close is None:
            discarded += 1
            continue
        bars.append(
            Bar(
                date=_trading_date(ts, meta),
                open=quantize(quote["open"][i]),
                high=quantize(quote["high"][i]),
                low=quantize(quote["low"][i]),
                close=quantize(close),
                adj_close=quantize(adj_close),
                volume=int(quote["volume"][i]),
            )
        )

    events: list[Event] = []
    raw_events = result.get("events") or {}
    for item in (raw_events.get("dividends") or {}).values():
        events.append(
            Event(
                date=_trading_date(item["date"], meta),
                kind="dividend",
                amount=quantize(item["amount"]),
            )
        )
    for item in (raw_events.get("splits") or {}).values():
        events.append(
            Event(
                date=_trading_date(item["date"], meta),
                kind="split",
                numerator=Decimal(str(item["numerator"])).quantize(Q4),
                denominator=Decimal(str(item["denominator"])).quantize(Q4),
            )
        )

    return ConformedChart(bars=bars, events=events, discarded=discarded)
