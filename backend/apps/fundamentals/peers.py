"""A comparacao de uma acao com os pares, pura (RF-11 a RF-14).

Sem ORM e sem relogio: quem chama (`compute.py`) le as linhas de `gold.fundamental_indicator`
desta execucao e entrega uma `PeerInput` por linha. Toda aritmetica em `Decimal`, contexto
padrao; a mediana e quantizada as casas da coluna do indicador, o percentil a quatro casas.

As regras, na ordem do plano:

1. a classificacao de uma companhia e a tupla do `PeerInput` de menor `ticker` dela;
2. a chave e a tupla, nunca o nome: segmento = (setor, subsetor, segmento), com os tres nao
   nulos; subsetor = (setor, subsetor), com os dois;
3. o grupo e o conjunto de companhias (`code_cvm`) da mesma chave de segmento; abaixo de
   `MIN_PEERS`, o da mesma chave de subsetor; abaixo de novo, `none`;
4. os valores do grupo: um por companhia -- o da propria acao para a companhia dela; para as
   outras, o do ticker de menor ordem com o valor nao nulo;
5. mediana, percentil (estritamente menores / (n - 1)) e contagem, nulos com o valor da acao
   nulo ou `n < MIN_PEERS`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

INDICATORS = ("roe", "net_margin", "ebit_margin", "net_debt_to_equity", "pe", "pb")
PLACES = {  # as casas da coluna em fundamental_indicator
    "roe": Decimal("1E-10"),
    "net_margin": Decimal("1E-10"),
    "ebit_margin": Decimal("1E-10"),
    "net_debt_to_equity": Decimal("1E-10"),
    "pe": Decimal("1E-6"),
    "pb": Decimal("1E-6"),
}
MIN_PEERS = 3
PERCENTILE_PLACES = Decimal("0.0001")

Level = Literal["segment", "subsector", "none"]
Group = tuple[str | None, str | None, str | None]


@dataclass(frozen=True)
class PeerInput:
    """Uma linha de indicador desta execucao."""

    ticker: str
    code_cvm: str
    sector: str | None
    subsector: str | None
    segment: str | None
    values: Mapping[str, Decimal | None]  # chaves = INDICATORS


@dataclass(frozen=True)
class IndicatorComparison:
    median: Decimal | None
    percentile: Decimal | None
    count: int | None


@dataclass(frozen=True)
class Comparison:
    level: Level
    group: Group  # (setor, subsetor, segmento)
    indicators: Mapping[str, IndicatorComparison]  # chaves = INDICATORS


_EMPTY = IndicatorComparison(None, None, None)
_NO_GROUP: Group = (None, None, None)


def compare_all(rows: Sequence[PeerInput]) -> dict[str, Comparison]:
    """Ticker -> comparacao, para cada linha de `rows`."""
    by_company: dict[str, list[PeerInput]] = {}
    for row in rows:
        by_company.setdefault(row.code_cvm, []).append(row)
    for members in by_company.values():
        members.sort(key=lambda member: member.ticker)

    # Regras 1 e 2: a classificacao pelo menor ticker, a chave pela tupla.
    classification: dict[str, Group] = {}
    segments: dict[tuple[str, str, str], set[str]] = {}
    subsectors: dict[tuple[str, str], set[str]] = {}
    for code, members in by_company.items():
        first = members[0]
        classification[code] = (first.sector, first.subsector, first.segment)
        if first.sector is None or first.subsector is None:
            continue
        subsectors.setdefault((first.sector, first.subsector), set()).add(code)
        if first.segment is not None:
            segments.setdefault(
                (first.sector, first.subsector, first.segment), set()
            ).add(code)

    result: dict[str, Comparison] = {}
    for row in rows:
        level, group, companies = _group_of(
            classification[row.code_cvm], segments, subsectors
        )
        if level == "none":
            result[row.ticker] = Comparison(
                level="none",
                group=_NO_GROUP,
                indicators={indicator: _EMPTY for indicator in INDICATORS},
            )
            continue
        result[row.ticker] = Comparison(
            level=level,
            group=group,
            indicators={
                indicator: _compare(indicator, row, companies, by_company)
                for indicator in INDICATORS
            },
        )
    return result


def _group_of(
    key: Group,
    segments: Mapping[tuple[str, str, str], set[str]],
    subsectors: Mapping[tuple[str, str], set[str]],
) -> tuple[Level, Group, set[str]]:
    """Regra 3: o nivel, a tupla que valeu e as companhias do grupo."""
    sector, subsector, segment = key
    if sector is None or subsector is None:
        return "none", _NO_GROUP, set()
    if segment is not None:
        companies = segments.get((sector, subsector, segment), set())
        if len(companies) >= MIN_PEERS:
            return "segment", (sector, subsector, segment), companies
    companies = subsectors.get((sector, subsector), set())
    if len(companies) >= MIN_PEERS:
        return "subsector", (sector, subsector, None), companies
    return "none", _NO_GROUP, set()


def _compare(
    indicator: str,
    row: PeerInput,
    companies: set[str],
    by_company: Mapping[str, list[PeerInput]],
) -> IndicatorComparison:
    """Regras 4 e 5 para um indicador da acao de `row`."""
    own = row.values[indicator]
    if own is None:
        return _EMPTY
    values: list[Decimal] = [own]
    for code in companies:
        if code == row.code_cvm:
            continue
        value = _company_value(by_company[code], indicator)
        if value is not None:
            values.append(value)
    n = len(values)
    if n < MIN_PEERS:
        return _EMPTY
    ordered = sorted(values)
    middle = n // 2
    if n % 2 == 1:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / Decimal(2)
    below = sum(1 for value in values if value < own)
    percentile = (Decimal(below) / Decimal(n - 1)).quantize(PERCENTILE_PLACES)
    return IndicatorComparison(
        median=median.quantize(PLACES[indicator]),
        percentile=percentile,
        count=n,
    )


def _company_value(members: Sequence[PeerInput], indicator: str) -> Decimal | None:
    """O valor do ticker de menor ordem com o indicador nao nulo; `members` vem ordenado."""
    for member in members:
        value = member.values[indicator]
        if value is not None:
            return value
    return None
