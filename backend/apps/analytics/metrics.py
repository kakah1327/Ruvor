"""Calculo puro das metricas de comportamento: janelas, retornos, estatistica e queda.

Funcoes sobre listas de dataclasses proprias, no molde de `conform_prices.py`. Nada aqui
importa modelo, abre transacao ou consulta banco — isso e do `compute`. Quem le
`silver.price` e `silver.corporate_event` e converte para `Bar` e `Dividend` e ele.

As definicoes estao na spec, em "Contratos externos → As definicoes, uma a uma". A que
governa tudo o mais: a janela de N meses e de **pregoes** (`P0..Pn`), e a janela de
retornos e `P1..Pn` — uma observacao a menos.
"""

from __future__ import annotations

import calendar
import math
import statistics
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

IBOV_TICKER = "IBOV"
TRADING_DAYS_YEAR = 252
RETURN_WINDOWS = (1, 3, 6, 12, 36, 60, 120)
STATISTICAL_WINDOW = 60
VOLATILITY_WINDOWS = (12, 60)

HIST_LOWER = Decimal("-0.10")
HIST_UPPER = Decimal("0.10")
HIST_WIDTH = Decimal("0.005")
HIST_BINS = 42

MIN_VOLATILITY_OBS = 2
MIN_MOMENT_OBS = 4
MIN_BETA_OBS = 30

# Quantizacao de saida. `Q6` e so de `dividends_12m`, cuja coluna e Decimal(18,6);
# quantizar a dez casas ali seria contrato incoerente consigo mesmo. O modo de
# arredondamento e o padrao do contexto, ROUND_HALF_EVEN.
Q10 = Decimal("0.0000000001")
Q6 = Decimal("0.000001")
Q2 = Decimal("0.01")


@dataclass(frozen=True)
class Bar:
    """Um pregao vindo de `silver.price`.

    Nao e o `Bar` de `conform_prices.py`: nome igual, campos diferentes, modulos
    distintos.
    """

    date: date
    close: Decimal
    adj_close: Decimal
    volume: int
    log_return: Decimal | None


@dataclass(frozen=True)
class Dividend:
    """Um pagamento vindo de `silver.corporate_event`.

    `amount` nao e anulavel: quem monta a lista filtra `amount IS NULL`, porque
    pagamento sem valor nao e pagamento que se possa somar.
    """

    date: date
    amount: Decimal


@dataclass(frozen=True)
class HistogramBin:
    """Um balde do histograma de retornos. `lower` e nulo so no indice 0, e `upper` so
    no indice 41 — sao as duas pontas abertas."""

    index: int
    lower: Decimal | None
    upper: Decimal | None
    count: int


def months_before(d: date, months: int) -> date:
    """`d` menos `months` meses de calendario.

    Quando o dia nao existe no mes de destino, usa o ultimo dia daquele mes: 31 de
    marco menos 1 mes da 28 ou 29 de fevereiro, conforme o ano.
    """
    total = d.year * 12 + (d.month - 1) - months
    year, month = divmod(total, 12)
    month += 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def window_bars(bars: list[Bar], months: int, as_of: date) -> list[Bar] | None:
    """A janela de pregoes de N meses: do ultimo pregao em ou antes da data inicial
    ate `as_of`, inclusive nos dois extremos.

    Sem pregao em ou antes da data inicial, a janela nao existe e a coluna vira nula
    (RF-12) — dai o `None`, que nao se confunde com janela vazia.
    """
    start = months_before(as_of, months)
    eligible = [b for b in bars if b.date <= as_of]
    first = None
    for i, bar in enumerate(eligible):
        if bar.date <= start:
            first = i
    if first is None:
        return None
    return eligible[first:]


def ytd_bars(bars: list[Bar], as_of: date) -> list[Bar] | None:
    """A janela do ano: do **ultimo pregao do ano anterior** ao de `as_of` ate `as_of`.

    Nao do primeiro pregao do ano corrente: o retorno do ano mede o movimento desde o
    fechamento do ano anterior.
    """
    eligible = [b for b in bars if b.date <= as_of]
    first = None
    for i, bar in enumerate(eligible):
        if bar.date.year < as_of.year:
            first = i
    if first is None:
        return None
    return eligible[first:]


def window_returns(window: list[Bar]) -> list[Decimal]:
    """P1..Pn: o log_return de P0 mede movimento anterior a janela e fica de fora.

    Nulo e descartado: `statistics.stdev` sobre lista com None levanta, e a contagem
    precisa refletir o que de fato entrou.
    """
    return [b.log_return for b in window[1:] if b.log_return is not None]


def total_return(window: list[Bar]) -> Decimal:
    """`adj_close` do ultimo pregao da janela sobre o do primeiro, menos 1.

    `adj_close`, nunca `close`: ele ja incorpora dividendo e desdobramento, e e o
    retorno que o investidor teve (RF-05). Exato em `Decimal`, quantizado so aqui.
    """
    return (window[-1].adj_close / window[0].adj_close - 1).quantize(Q10)


def dividend_summary(
    dividends: list[Dividend], as_of: date, as_of_close: Decimal
) -> tuple[Decimal, int, Decimal]:
    """Soma, quantidade e retorno em dividendos dos 12 meses anteriores a `as_of`.

    O *yield* divide pelo `close` de `as_of`, **nunca** pelo `adj_close`: o ajustado ja
    desconta o dividendo, e usa-lo faria a acao parecer pagar mais do que pagou.

    Ausencia de pagamento e **zero**, nao nulo: aqui da para calcular, e o resultado e
    zero. As tres colunas sao nao anulaveis.
    """
    start = months_before(as_of, 12)
    paid = [d for d in dividends if start <= d.date <= as_of]
    if not paid:
        return Decimal(0).quantize(Q6), 0, Decimal(0).quantize(Q10)
    total = sum((d.amount for d in paid), Decimal(0))
    return total.quantize(Q6), len(paid), (total / as_of_close).quantize(Q10)


def average_volume(bars: list[Bar], sessions: int) -> Decimal | None:
    """Media aritmetica do `volume` dos ultimos `sessions` pregoes.

    Menos pregoes que o pedido e nulo (RF-12), nunca a media parcial do que houver.
    """
    if len(bars) < sessions:
        return None
    window = bars[-sessions:]
    total = sum(b.volume for b in window)
    return (Decimal(total) / Decimal(sessions)).quantize(Q2)


@dataclass(frozen=True)
class Drawdown:
    """A maior queda da serie inteira de `adj_close`.

    `depth`, `peak_date` e `trough_date` sao **sempre** preenchidos: sobre serie nao
    vazia a maior queda sempre existe, nem que seja `0`. So a recuperacao pode faltar,
    e faltar ali e informacao, nao lacuna.
    """

    depth: Decimal
    peak_date: date
    trough_date: date
    recovery_date: date | None
    recovery_sessions: int | None


@dataclass(frozen=True)
class Metrics:
    """Tudo o que uma linha de `gold.behavior_metric` carrega, mais os 42 baldes.

    `returns` e `volatility` sao dicionarios de chave fechada — "1m".."120m" e "ytd";
    "12m" e "60m" — e quem os desmonta em coluna e o `compute` do outro modulo.
    """

    as_of_date: date
    first_price_date: date
    price_count: int
    returns: dict[str, Decimal | None]
    volatility: dict[str, Decimal | None]
    drawdown: Drawdown
    beta_60m: Decimal | None
    correlation_60m: Decimal | None
    benchmark_observations: int | None
    skewness: Decimal | None
    excess_kurtosis: Decimal | None
    statistical_observations: int | None
    dividends_12m: Decimal
    dividend_payments_12m: int
    dividend_yield_12m: Decimal
    avg_volume_21d: Decimal | None
    avg_volume_252d: Decimal | None
    histogram: list[HistogramBin]


def annualized_volatility(returns: list[Decimal]) -> Decimal | None:
    """Desvio padrao **amostral** dos log-retornos, vezes a raiz de 252.

    `stdev`, divisor `n-1` — ao contrario de `skewness_and_kurtosis`, que usa o
    populacional. A divergencia e a convencao de cada um e nao deve ser uniformizada.
    Abaixo de duas observacoes, nulo.
    """
    if len(returns) < MIN_VOLATILITY_OBS:
        return None
    deviation = statistics.stdev([float(r) for r in returns])
    return Decimal(str(deviation * math.sqrt(TRADING_DAYS_YEAR))).quantize(Q10)


def max_drawdown(bars: list[Bar]) -> Drawdown:
    """Desempate: topo e fundo sao as PRIMEIRAS ocorrencias; recuperacao e o primeiro
    pregao ESTRITAMENTE posterior ao fundo que alcanca o topo; recovery_sessions conta
    exclusivo na origem e inclusivo no destino (fundo 5, recuperacao 8 -> 3).
    """
    peak_value = bars[0].adj_close
    peak_index = 0
    depth = Decimal(0)
    best_peak = 0
    best_trough = 0
    for i, current in enumerate(bars):
        if current.adj_close > peak_value:
            # Estritamente maior: num plato o topo continua sendo o primeiro pregao.
            peak_value = current.adj_close
            peak_index = i
        fall = current.adj_close / peak_value - 1
        if fall < depth:
            # Estritamente menor: no empate de profundidade fica a primeira queda.
            depth = fall
            best_peak = peak_index
            best_trough = i
    recovery_date: date | None = None
    recovery_sessions: int | None = None
    target = bars[best_peak].adj_close
    for i in range(best_trough + 1, len(bars)):
        if bars[i].adj_close >= target:
            recovery_date = bars[i].date
            recovery_sessions = i - best_trough
            break
    return Drawdown(
        depth=depth.quantize(Q10),
        peak_date=bars[best_peak].date,
        trough_date=bars[best_trough].date,
        recovery_date=recovery_date,
        recovery_sessions=recovery_sessions,
    )


def skewness_and_kurtosis(
    returns: list[Decimal],
) -> tuple[Decimal | None, Decimal | None]:
    """Os estimadores enviesados `g1` e `g2`.

    Momento central de ordem 3 e 4 com divisor **n** — e por isso `fmean` deles —,
    divididos pelo desvio padrao **populacional** (`pstdev`, divisor `n`) elevado a 3 e
    a 4; a curtose subtrai 3, de modo que zero e a normal. Abaixo de quatro
    observacoes, nulos — e tambem com desvio zero, em que a forma nao esta definida.
    """
    if len(returns) < MIN_MOMENT_OBS:
        return None, None
    values = [float(r) for r in returns]
    mean = statistics.fmean(values)
    deviation = statistics.pstdev(values)
    if deviation == 0:
        return None, None
    third = statistics.fmean([(v - mean) ** 3 for v in values])
    fourth = statistics.fmean([(v - mean) ** 4 for v in values])
    skewness = third / deviation**3
    excess_kurtosis = fourth / deviation**4 - 3
    return (
        Decimal(str(skewness)).quantize(Q10),
        Decimal(str(excess_kurtosis)).quantize(Q10),
    )


def _bin_bounds(index: int) -> tuple[Decimal | None, Decimal | None]:
    """Os limites do balde `index`. Nulo so nas duas pontas abertas."""
    if index == 0:
        return None, HIST_LOWER
    if index == HIST_BINS - 1:
        return HIST_UPPER, None
    lower = HIST_LOWER + HIST_WIDTH * (index - 1)
    return lower, lower + HIST_WIDTH


def histogram(returns: list[Decimal]) -> list[HistogramBin]:
    """Os 42 baldes, sempre todos e sempre em ordem de indice.

    Quarenta baldes de largura 0,005 de -0,10 a +0,10, mais uma ponta aberta de cada
    lado. Intervalo fechado a esquerda e aberto a direita. Lista vazia — janela
    estatistica inexistente — devolve os 42 com contagem zero, nunca zero baldes.
    """
    counts = [0] * HIST_BINS
    for value in returns:
        if value < HIST_LOWER:
            counts[0] += 1
        elif value >= HIST_UPPER:
            counts[HIST_BINS - 1] += 1
        else:
            counts[1 + int((value - HIST_LOWER) / HIST_WIDTH)] += 1
    bins: list[HistogramBin] = []
    for index, count in enumerate(counts):
        lower, upper = _bin_bounds(index)
        bins.append(HistogramBin(index=index, lower=lower, upper=upper, count=count))
    return bins


def beta_and_correlation(
    asset_bars: list[Bar], benchmark_bars: list[Bar] | None, as_of: date
) -> tuple[Decimal | None, Decimal | None, int | None]:
    """Beta e correlacao com o indice, na janela estatistica, emparelhados por data.

    As duas series **nao sao simetricas**. A janela de retornos e a do ATIVO — `P1..Pn`,
    ja sem `P0` e ja sem nulo —, e o benchmark e covariavel, entra por data: o par vale
    quando o indice tem, NAQUELA data, `log_return` nao nulo. O `Q0` do benchmark nao e
    descartado por ser `Q0`, so por ausencia ou por nulo.

    Sem indice, ou com a janela inexistente, a tripla e toda nula. Com a janela
    existindo e menos de 30 pares, beta e correlacao sao nulos mas a contagem e a real:
    o minimo diz que o numero nao merece confianca, nao que seja desconhecido.
    """
    if benchmark_bars is None:
        return None, None, None
    window = window_bars(asset_bars, STATISTICAL_WINDOW, as_of)
    if window is None:
        return None, None, None
    benchmark_returns = {b.date: b.log_return for b in benchmark_bars}
    index_values: list[float] = []
    asset_values: list[float] = []
    for current in window[1:]:
        # `window[1:]` pelo mesmo motivo de `window_returns`, que nao serve aqui por
        # devolver `Decimal` sem a data de que o emparelhamento precisa.
        if current.log_return is None:
            continue
        counterpart = benchmark_returns.get(current.date)
        if counterpart is None:
            continue
        index_values.append(float(counterpart))
        asset_values.append(float(current.log_return))
    observations = len(asset_values)
    if observations < MIN_BETA_OBS:
        return None, None, observations
    slope = statistics.linear_regression(index_values, asset_values).slope
    coefficient = statistics.correlation(index_values, asset_values)
    return (
        Decimal(str(slope)).quantize(Q10),
        Decimal(str(coefficient)).quantize(Q10),
        observations,
    )


def compute(
    bars: list[Bar], dividends: list[Dividend], benchmark: list[Bar] | None
) -> Metrics:
    """Monta o `Metrics` do ativo. `bars` nunca chega vazio — o guarda e do chamador.

    `as_of` sai daqui uma vez so e e passado adiante: deriva-lo dentro de cada funcao
    convidaria a divergencia no dia em que a regra mudasse.
    """
    as_of = bars[-1].date
    returns: dict[str, Decimal | None] = {}
    for months in RETURN_WINDOWS:
        window = window_bars(bars, months, as_of)
        returns[f"{months}m"] = None if window is None else total_return(window)
    year_window = ytd_bars(bars, as_of)
    returns["ytd"] = None if year_window is None else total_return(year_window)

    volatility: dict[str, Decimal | None] = {}
    for months in VOLATILITY_WINDOWS:
        window = window_bars(bars, months, as_of)
        volatility[f"{months}m"] = (
            None if window is None else annualized_volatility(window_returns(window))
        )

    statistical_window = window_bars(bars, STATISTICAL_WINDOW, as_of)
    statistical_returns = (
        [] if statistical_window is None else window_returns(statistical_window)
    )
    # Nulo, nunca `0`: a janela inexistente e "nao da para calcular" (RF-12), e o
    # histograma sai com os 42 baldes zerados, cuja soma e `0` e nao e igual a NULL.
    statistical_observations = (
        None if statistical_window is None else len(statistical_returns)
    )
    skewness, excess_kurtosis = skewness_and_kurtosis(statistical_returns)
    beta, correlation, benchmark_observations = beta_and_correlation(
        bars, benchmark, as_of
    )
    dividends_12m, payments_12m, yield_12m = dividend_summary(
        dividends, as_of, bars[-1].close
    )
    return Metrics(
        as_of_date=as_of,
        first_price_date=bars[0].date,
        price_count=len(bars),
        returns=returns,
        volatility=volatility,
        drawdown=max_drawdown(bars),
        beta_60m=beta,
        correlation_60m=correlation,
        benchmark_observations=benchmark_observations,
        skewness=skewness,
        excess_kurtosis=excess_kurtosis,
        statistical_observations=statistical_observations,
        dividends_12m=dividends_12m,
        dividend_payments_12m=payments_12m,
        dividend_yield_12m=yield_12m,
        avg_volume_21d=average_volume(bars, 21),
        avg_volume_252d=average_volume(bars, 252),
        histogram=histogram(statistical_returns),
    )
