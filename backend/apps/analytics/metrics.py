"""Calculo puro das metricas de comportamento: janelas, retornos, dividendos e volume.

Funcoes sobre listas de dataclasses proprias, no molde de `conform_prices.py`. Nada aqui
importa modelo, abre transacao ou consulta banco — isso e do `compute`. Quem le
`silver.price` e `silver.corporate_event` e converte para `Bar` e `Dividend` e ele.

As definicoes estao na spec, em "Contratos externos → As definicoes, uma a uma". A que
governa tudo o mais: a janela de N meses e de **pregoes** (`P0..Pn`), e a janela de
retornos e `P1..Pn` — uma observacao a menos.
"""

from __future__ import annotations

import calendar
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
