"""Janelas, retornos, dividendos e volume, conferidos a mao (V-05, V-09, V-18, V-18b, V-19).

Nenhum teste aqui toca banco, modelo ou rede: as funcoes de `metrics` recebem listas de
`Bar` e `Dividend` construidas no proprio teste.

**Todo valor esperado esta escrito literalmente abaixo**, com a conta que o produz no
comentario — nenhum e derivado do codigo sob teste, que aprovaria qualquer coisa.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from apps.analytics.metrics import (
    Bar,
    Dividend,
    average_volume,
    dividend_summary,
    months_before,
    total_return,
    window_bars,
    window_returns,
    ytd_bars,
)


def bar(
    d: date,
    close: str,
    adj_close: str,
    volume: int = 1000,
    log_return: str | None = None,
) -> Bar:
    return Bar(
        date=d,
        close=Decimal(close),
        adj_close=Decimal(adj_close),
        volume=volume,
        log_return=None if log_return is None else Decimal(log_return),
    )


# --- months_before: o ajuste de fim de mes -------------------------------------------


def test_months_before_ajusta_dia_inexistente_no_mes_de_destino() -> None:
    # 31 de marco menos 1 mes: fevereiro nao tem dia 31, entao vale o ultimo dia dele.
    assert months_before(date(2026, 3, 31), 1) == date(2026, 2, 28)
    # e 29 no ano bissexto.
    assert months_before(date(2024, 3, 31), 1) == date(2024, 2, 29)
    assert months_before(date(2026, 5, 31), 3) == date(2026, 2, 28)


def test_months_before_atravessa_a_virada_do_ano() -> None:
    assert months_before(date(2026, 1, 15), 12) == date(2025, 1, 15)
    assert months_before(date(2026, 1, 31), 13) == date(2024, 12, 31)
    assert months_before(date(2026, 3, 16), 120) == date(2016, 3, 16)


# --- V-05: retorno por janela e retorno do ano ----------------------------------------

# Serie que atravessa a virada do ano. `close` e `adj_close` divergem de proposito: com
# `close` no lugar do ajustado, nenhum dos dois valores esperados abaixo fecha.
AS_OF = date(2026, 3, 16)
SERIE_VIRADA = [
    bar(date(2025, 12, 29), "95.000000", "100.000000"),
    bar(date(2025, 12, 30), "104.000000", "110.000000", log_return="0.0953101798"),
    bar(date(2026, 1, 2), "109.000000", "115.000000", log_return="0.0444517625"),
    bar(date(2026, 2, 16), "115.000000", "120.000000", log_return="0.0425596144"),
    bar(date(2026, 3, 16), "125.000000", "132.000000", log_return="0.0953101798"),
]


def test_window_bars_comeca_no_ultimo_pregao_em_ou_antes_da_data_inicial() -> None:
    # 2026-03-16 menos 1 mes = 2026-02-16, que e dia de pregao: ele mesmo e o P0.
    janela = window_bars(SERIE_VIRADA, 1, AS_OF)
    assert janela is not None
    assert [b.date for b in janela] == [date(2026, 2, 16), date(2026, 3, 16)]


def test_retorno_de_1m_conferido_a_mao() -> None:
    janela = window_bars(SERIE_VIRADA, 1, AS_OF)
    assert janela is not None
    # 132 / 120 - 1 = 0,1
    assert total_return(janela) == Decimal("0.1000000000")


def test_retorno_do_ano_tem_por_base_o_ultimo_pregao_do_ano_anterior() -> None:
    janela = ytd_bars(SERIE_VIRADA, AS_OF)
    assert janela is not None
    # O P0 e 2025-12-30, ultimo pregao de 2025 -- nao 2026-01-02, o primeiro do ano.
    assert janela[0].date == date(2025, 12, 30)
    # 132 / 110 - 1 = 0,2
    assert total_return(janela) == Decimal("0.2000000000")


def test_ytd_e_nulo_quando_a_serie_comeca_no_ano_corrente() -> None:
    serie = [b for b in SERIE_VIRADA if b.date.year == 2026]
    assert ytd_bars(serie, AS_OF) is None


def test_window_returns_descarta_o_primeiro_pregao_da_janela_e_os_nulos() -> None:
    janela = [
        bar(date(2026, 3, 10), "10.000000", "10.000000", log_return="0.5000000000"),
        bar(date(2026, 3, 11), "10.000000", "10.000000", log_return="0.0100000000"),
        bar(date(2026, 3, 12), "10.000000", "10.000000", log_return=None),
        bar(date(2026, 3, 13), "10.000000", "10.000000", log_return="0.0300000000"),
    ]
    # O 0,5 e de P0 -- mede movimento anterior a janela -- e o nulo nao entra em conta.
    assert window_returns(janela) == [Decimal("0.0100000000"), Decimal("0.0300000000")]


# --- V-09: janela sem historico e nula ------------------------------------------------

# Tres anos de serie: 2023-03-15 a 2026-03-16.
SERIE_TRES_ANOS = [
    bar(date(2023, 3, 15), "50.000000", "50.000000"),
    bar(date(2024, 3, 15), "60.000000", "60.000000", log_return="0.1823215568"),
    bar(date(2025, 3, 14), "70.000000", "70.000000", log_return="0.1541506798"),
    bar(date(2026, 3, 16), "80.000000", "80.000000", log_return="0.1335313926"),
]


def test_janela_de_120m_nao_existe_em_serie_de_tres_anos() -> None:
    # 2026-03-16 menos 120 meses = 2016-03-16; nao ha pregao em ou antes disso.
    assert window_bars(SERIE_TRES_ANOS, 120, AS_OF) is None
    # 60 meses cai em 2021-03-16, tambem antes do primeiro pregao.
    assert window_bars(SERIE_TRES_ANOS, 60, AS_OF) is None


def test_janela_de_12m_existe_na_mesma_serie_e_o_retorno_fecha() -> None:
    janela = window_bars(SERIE_TRES_ANOS, 12, AS_OF)
    assert janela is not None
    # 2026-03-16 menos 12 meses = 2025-03-16; o ultimo pregao em ou antes e 2025-03-14.
    assert [b.date for b in janela] == [date(2025, 3, 14), date(2026, 3, 16)]
    # 80 / 70 - 1 = 0,142857142857... -> dez casas, ROUND_HALF_EVEN
    assert total_return(janela) == Decimal("0.1428571429")


def test_janela_de_36m_alcanca_o_primeiro_pregao_da_serie() -> None:
    janela = window_bars(SERIE_TRES_ANOS, 36, AS_OF)
    assert janela is not None
    assert janela[0].date == date(2023, 3, 15)


# --- V-18: dividendos --------------------------------------------------------------

# Tres pagamentos dentro dos 12 meses anteriores a 2026-03-16 e um fora.
DIVIDENDOS = [
    Dividend(date(2025, 3, 15), Decimal("9.000000")),  # fora: a janela comeca em 03-16
    Dividend(date(2025, 3, 16), Decimal("1.000000")),  # dentro: a borda e inclusiva
    Dividend(date(2025, 9, 10), Decimal("0.500000")),
    Dividend(date(2026, 1, 20), Decimal("0.500000")),
]


def test_dividendos_soma_contagem_e_yield_conferidos_a_mao() -> None:
    # `close` de as_of = 20; `adj_close` seria outro numero, e o yield usa o `close`.
    soma, pagamentos, retorno = dividend_summary(
        DIVIDENDOS, AS_OF, Decimal("20.000000")
    )
    # 1,00 + 0,50 + 0,50 = 2,00 -- o de 2025-03-15 fica de fora
    assert soma == Decimal("2.000000")
    assert pagamentos == 3
    # 2,00 / 20,00 = 0,1
    assert retorno == Decimal("0.1000000000")


def test_yield_divide_pelo_close_que_recebeu() -> None:
    # Mesmos pagamentos, `close` de 16: 2,00 / 16,00 = 0,125
    _, _, retorno = dividend_summary(DIVIDENDOS, AS_OF, Decimal("16.000000"))
    assert retorno == Decimal("0.1250000000")


# --- V-19: quem nao paga grava zero, nao nulo ----------------------------------------


def test_sem_pagamento_nenhum_as_tres_colunas_sao_zero() -> None:
    soma, pagamentos, retorno = dividend_summary([], AS_OF, Decimal("20.000000"))
    assert soma == Decimal("0.000000")
    assert pagamentos == 0
    assert retorno == Decimal("0.0000000000")


def test_pagamento_so_fora_da_janela_tambem_da_zero() -> None:
    fora = [Dividend(date(2025, 3, 15), Decimal("9.000000"))]
    assert dividend_summary(fora, AS_OF, Decimal("20.000000")) == (
        Decimal("0.000000"),
        0,
        Decimal("0.0000000000"),
    )


# --- V-18b: volume medio -------------------------------------------------------------

# Trinta pregoes, volume de 1.000 a 3.900 em passo de 100.
SERIE_TRINTA = [
    bar(
        date(2026, 2, 2) + timedelta(days=i),
        "10.000000",
        "10.000000",
        volume=1000 + 100 * i,
    )
    for i in range(30)
]


def test_volume_medio_de_21_pregoes_conferido_a_mao() -> None:
    # Os ultimos 21 sao os indices 9..29: 1.900 a 3.900. Media = (1.900 + 3.900) / 2
    assert average_volume(SERIE_TRINTA, 21) == Decimal("2900.00")


def test_volume_medio_de_252_pregoes_e_nulo_com_apenas_30() -> None:
    # Nunca a media parcial dos 30 -- falta historico, e o nulo e o do RF-12.
    assert average_volume(SERIE_TRINTA, 252) is None


def test_volume_medio_com_exatamente_os_pregoes_pedidos() -> None:
    # 30 pregoes, media de 1.000 a 3.900 = (1.000 + 3.900) / 2
    assert average_volume(SERIE_TRINTA, 30) == Decimal("2450.00")
