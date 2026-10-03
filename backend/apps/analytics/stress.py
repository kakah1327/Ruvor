"""Calculo puro do estresse historico: o ativo e o Ibovespa em cada episodio da D-147.

Molde de `metrics.py`: funcoes sobre listas de `Bar`, sem modelo, transacao ou banco
(D-58, D-59). Importa so a biblioteca padrao e `apps.analytics.metrics` — o V-04 confere
pela arvore sintatica.

As regras estao na spec do M3.3: as pontas da janela pelo "ultimo pregao <= data" (RF-02),
os quatro motivos de "sem dado" na ordem do RF-03, as medidas do RF-04 e o indice medido na
propria serie, independente do ativo (RF-05).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from apps.analytics.metrics import Q10, Bar

# Base mais velha que isto, em dias corridos, e `stale_start` (RF-03): o dobro do maior
# intervalo entre pregoes consecutivos das seis series, que e de 5 dias (o Carnaval).
STALE_START_DAYS = 10


@dataclass(frozen=True)
class Episode:
    code: str
    start: date
    end: date


# A lista curada da D-147, em ordem cronologica. Mudar a lista e decisao nova, e a mesma
# PR muda os nomes em `frontend/src/content/textos.ts` e as listas dos dois testes.
EPISODES: tuple[Episode, ...] = (
    Episode("jbs_2017", date(2017, 5, 17), date(2017, 6, 30)),
    Episode("truckers_2018", date(2018, 5, 18), date(2018, 6, 29)),
    Episode("covid_2020", date(2020, 2, 21), date(2020, 3, 31)),
    Episode("rates_2021", date(2021, 6, 7), date(2022, 7, 14)),
)


@dataclass(frozen=True)
class EpisodeResult:
    """Uma linha de `gold.stress_episode`, menos a `metric` (RF-07).

    Com `missing` preenchido, as medidas do ativo sao nulas; as tres do indice nao
    dependem disso (RF-05).
    """

    episode: str
    start_date: date
    end_date: date
    missing: str | None
    window_start_date: date | None
    window_end_date: date | None
    period_return: Decimal | None
    drawdown: Decimal | None
    drawdown_peak_date: date | None
    drawdown_trough_date: date | None
    recovery_date: date | None
    recovery_sessions: int | None
    benchmark_period_return: Decimal | None
    benchmark_drawdown: Decimal | None
    benchmark_recovery_sessions: int | None


@dataclass(frozen=True)
class _Measures:
    p0: date
    pn: date
    period_return: Decimal
    drawdown: Decimal
    peak_date: date
    trough_date: date
    recovery_date: date | None
    recovery_sessions: int | None


def missing_reason(
    bars: list[Bar], ep: Episode, calendar: list[Bar] | None
) -> str | None:
    """O primeiro motivo que se aplica, na ordem do RF-03, ou `None` com dado.

    `bars[-1]` e o ultimo pregao da serie inteira: `ends_before` so dispara com a serie
    terminando dentro do episodio. O fim do mercado e o ultimo pregao do calendario ate o
    fim do episodio; sem calendario, a propria data de fim.
    """
    base = [b for b in bars if b.date <= ep.start]
    if not base:
        return "starts_after"
    if (ep.start - base[-1].date).days > STALE_START_DAYS:
        return "stale_start"
    market = [b for b in (calendar or []) if b.date <= ep.end]
    market_end = market[-1].date if market else ep.end
    if bars[-1].date < market_end:
        return "ends_before"
    if not any(ep.start < b.date <= ep.end for b in bars):
        return "no_trading"
    return None


def _measure(bars: list[Bar], ep: Episode) -> _Measures:
    """As medidas do RF-04, so chamadas com o motivo nulo.

    Os indices de topo e fundo sao da serie inteira, porque a recuperacao e procurada
    nela, nao so na janela. Topo trocado so por estritamente maior e queda so por
    estritamente menor: no empate ficam as primeiras ocorrencias, como no `max_drawdown`.
    """
    i0 = max(i for i, b in enumerate(bars) if b.date <= ep.start)
    i_n = max(i for i, b in enumerate(bars) if b.date <= ep.end)
    period_return = (bars[i_n].adj_close / bars[i0].adj_close - 1).quantize(Q10)

    peak_value = bars[i0].adj_close
    peak_index = i0
    depth = Decimal(0)
    best_peak = i0
    best_trough = i0
    for i in range(i0, i_n + 1):
        current = bars[i].adj_close
        if current > peak_value:
            peak_value = current
            peak_index = i
        fall = current / peak_value - 1
        if fall < depth:
            depth = fall
            best_peak = peak_index
            best_trough = i
    drawdown = depth.quantize(Q10)

    recovery_date: date | None = None
    recovery_sessions: int | None = None
    if drawdown == 0:
        # Sem queda: topo e fundo em P0 e nada a recuperar. Decide pelo valor quantizado,
        # para a tela ler como "sem queda" exatamente o que esta gravado. E aqui que o
        # calculo diverge do `max_drawdown`, que com profundidade zero procura a
        # recuperacao a partir do primeiro pregao.
        best_peak = best_trough = i0
    else:
        target = bars[best_peak].adj_close
        for j in range(best_trough + 1, len(bars)):
            if bars[j].adj_close >= target:
                recovery_date = bars[j].date
                recovery_sessions = j - best_trough
                break

    return _Measures(
        p0=bars[i0].date,
        pn=bars[i_n].date,
        period_return=period_return,
        drawdown=drawdown,
        peak_date=bars[best_peak].date,
        trough_date=bars[best_trough].date,
        recovery_date=recovery_date,
        recovery_sessions=recovery_sessions,
    )


def compute_stress(
    bars: list[Bar], benchmark: list[Bar] | None, calendar: list[Bar] | None
) -> list[EpisodeResult]:
    """Um resultado por episodio de `EPISODES`, sempre todos, na ordem da lista.

    `bars` nunca e vazia (o `compute` pula o ativo sem preco antes). `benchmark` e o IBOV,
    ou `None` quando o ativo e o proprio IBOV ou o indice nao tem preco. `calendar` e a
    serie do IBOV quando existe, inclusive para o proprio IBOV.

    O indice e avaliado sem calendario (`calendar=None`): com ele como calendario de si
    mesmo, `ends_before` nunca dispararia, e a serie cortada mediria janela parcial.
    """
    results: list[EpisodeResult] = []
    for ep in EPISODES:
        missing = missing_reason(bars, ep, calendar)
        asset = _measure(bars, ep) if missing is None else None

        bench: _Measures | None = None
        if benchmark and missing_reason(benchmark, ep, None) is None:
            bench = _measure(benchmark, ep)

        results.append(
            EpisodeResult(
                episode=ep.code,
                start_date=ep.start,
                end_date=ep.end,
                missing=missing,
                window_start_date=asset.p0 if asset else None,
                window_end_date=asset.pn if asset else None,
                period_return=asset.period_return if asset else None,
                drawdown=asset.drawdown if asset else None,
                drawdown_peak_date=asset.peak_date if asset else None,
                drawdown_trough_date=asset.trough_date if asset else None,
                recovery_date=asset.recovery_date if asset else None,
                recovery_sessions=asset.recovery_sessions if asset else None,
                benchmark_period_return=bench.period_return if bench else None,
                benchmark_drawdown=bench.drawdown if bench else None,
                benchmark_recovery_sessions=bench.recovery_sessions if bench else None,
            )
        )
    return results
