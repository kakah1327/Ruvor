"""O calculo puro conferido a mao: V-05, V-06, V-07, V-08, V-08b, V-09, V-10, V-10b,
V-10c, V-11, V-11b, V-18, V-18b, V-18c e V-19.

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
    annualized_volatility,
    average_volume,
    beta_and_correlation,
    compute,
    dividend_summary,
    histogram,
    max_drawdown,
    months_before,
    skewness_and_kurtosis,
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


# --- V-06: volatilidade, assimetria e curtose conferidas a mao ------------------------
#
# Uma serie so para os tres, com a conta inteira escrita aqui. Os quatro retornos:
#
#     -0,01   0,00   0,01   0,04        media = 0,01
#     desvios em torno da media: -0,02  -0,01   0,00   0,03
#
# Volatilidade (desvio **amostral**, divisor n-1, vezes a raiz de 252):
#     variancia = (4 + 1 + 0 + 9)e-4 / 3 = 14e-4 / 3
#     vol = raiz(14e-4 / 3 * 252) = raiz(0,1176) = 0,342928563989645...
#
# Assimetria g1 (momento de ordem 3 com divisor **n**, sobre `pstdev` ao cubo):
#     m3 = (-8 - 1 + 0 + 27)e-6 / 4 = 4,5e-6
#     pstdev = raiz(14e-4 / 4) = raiz(3,5e-4) = 0,018708286933869708...
#     g1 = 4,5e-6 / (3,5e-4)^1,5 = 4,5e-6 / 6,547900426854395e-6 = 0,687243193489...
#
# Curtose excedente g2 (momento de ordem 4 com divisor n, menos 3):
#     m4 = (16 + 1 + 0 + 81)e-8 / 4 = 2,45e-7
#     g2 = 2,45e-7 / (3,5e-4)^2 - 3 = 2,45e-7 / 1,225e-7 - 3 = 2 - 3 = -1  (exato)
#
# Os divisores divergem de proposito: amostral na volatilidade, populacional nos
# momentos. Com `stdev` no lugar de `pstdev`, g1 daria 0,4463775481 -- fora da
# tolerancia por oito ordens de grandeza.
RETORNOS_V06 = [
    Decimal("-0.0100000000"),
    Decimal("0.0000000000"),
    Decimal("0.0100000000"),
    Decimal("0.0400000000"),
]
# O resultado passa por `float`, entao a comparacao e por tolerancia declarada: uma
# unidade da ultima casa gravada, que e a decima.
TOLERANCIA = Decimal("0.0000000001")


def test_volatilidade_anualizada_conferida_a_mao() -> None:
    valor = annualized_volatility(RETORNOS_V06)
    assert valor is not None
    # raiz(0,1176) = 0,342928563989645...  -- com a raiz de 12 daria 0,0748331477
    assert abs(valor - Decimal("0.3429285640")) <= TOLERANCIA


def test_volatilidade_exige_duas_observacoes() -> None:
    assert annualized_volatility([Decimal("0.0100000000")]) is None
    assert annualized_volatility([]) is None


def test_assimetria_e_curtose_conferidas_a_mao() -> None:
    assimetria, curtose = skewness_and_kurtosis(RETORNOS_V06)
    assert assimetria is not None
    assert curtose is not None
    assert abs(assimetria - Decimal("0.6872431935")) <= TOLERANCIA
    # A curtose e a **excedente**: zero e a normal, e aqui a conta da -1 exato.
    assert abs(curtose - Decimal("-1.0000000000")) <= TOLERANCIA


def test_assimetria_e_curtose_exigem_quatro_observacoes() -> None:
    assert skewness_and_kurtosis(RETORNOS_V06[:3]) == (None, None)


def test_assimetria_e_curtose_sem_dispersao_nenhuma_sao_nulas() -> None:
    # Desvio zero: a forma da distribuicao nao esta definida, e dividir levantaria.
    assert skewness_and_kurtosis([Decimal("0.0100000000")] * 5) == (None, None)


# --- Cenario longo: uma serie que de fato alcanca os 60 meses -------------------------
#
# A janela estatistica de 60 meses precisa **existir**: `k` pregoes consecutivos curtos
# a deixariam nula, e `statistical_observations` viria `None` em vez de `k-1`. Dai as
# datas espalhadas ao longo de cinco anos.
#
# A serie comeca **antes** de `P0`, de proposito: sem isso o `log_return` de `P0` seria
# nulo, o filtro o removeria de qualquer jeito, e incluir `P0` na janela de retornos
# deixaria de mudar qualquer contagem.

AS_OF_LONGO = date(2026, 3, 16)  # a janela de 60m comeca em 2021-03-16
ANTES_DE_P0 = date(2021, 3, 1)  # anterior a P0, e portanto fora da janela
DATA_P0 = date(2021, 3, 10)  # ultimo pregao em ou antes de 2021-03-16: e o P0


def datas_de_retorno(quantidade: int) -> list[date]:
    """`quantidade` datas de pregao dentro da janela, a ultima sendo `AS_OF_LONGO`."""
    passo = [date(2021, 4, 1) + timedelta(days=55 * i) for i in range(quantidade - 1)]
    return [*passo, AS_OF_LONGO]


def serie_longa(
    retornos: list[str | None], retorno_de_p0: str | None = "0.0100000000"
) -> list[Bar]:
    """Pregao anterior, `P0` e um pregao por retorno, nas datas de `datas_de_retorno`."""
    datas = datas_de_retorno(len(retornos))
    serie = [
        bar(ANTES_DE_P0, "10.000000", "10.000000"),
        bar(DATA_P0, "10.000000", "10.000000", log_return=retorno_de_p0),
    ]
    serie += [
        bar(d, "10.000000", "10.000000", log_return=r)
        for d, r in zip(datas, retornos, strict=True)
    ]
    return serie


def serie_indice(pares: list[tuple[date, str | None]]) -> list[Bar]:
    return [bar(d, "10.000000", "10.000000", log_return=r) for d, r in pares]


def pares_de_datas(
    datas: list[date], retornos: list[str]
) -> list[tuple[date, str | None]]:
    return [(d, r) for d, r in zip(datas, retornos, strict=True)]


def retornos_do_indice(quantidade: int) -> list[str]:
    """0,0010 a 0,00`quantidade`0 -- variados, para que o emparelhamento errado apareca."""
    return [f"0.0{i:03d}0000000" for i in range(1, quantidade + 1)]


def dobrados(retornos: list[str]) -> list[str | None]:
    return [str(Decimal(r) * 2) for r in retornos]


# --- V-07: o ativo que e o indice vezes dois ------------------------------------------


def test_beta_de_ativo_que_e_o_dobro_do_indice_da_dois_e_correlacao_um() -> None:
    retornos = retornos_do_indice(31)
    datas = datas_de_retorno(31)
    indice = serie_indice(pares_de_datas(datas, retornos))
    ativo = serie_longa(dobrados(retornos))
    beta, correlacao, observacoes = beta_and_correlation(ativo, indice, AS_OF_LONGO)
    assert observacoes == 31
    # A resposta e analitica: a regressao de 2x contra x tem inclinacao 2, e a
    # correlacao de duas series proporcionais e 1. Com os argumentos de
    # `linear_regression` invertidos, o beta daria 0,5.
    assert beta == Decimal("2.0000000000")
    assert correlacao == Decimal("1.0000000000")


def test_correlacao_imperfeita_nao_e_um_nem_r2_nem_covariancia() -> None:
    # A relacao proporcional acima nao separa correlacao de R2 nem de
    # correlation(ativo, ativo): os tres valem 1 ali. Aqui nao valem.
    #
    # O indice tem os 30 retornos de 0,001 a 0,030, e o ativo os mesmos **com o
    # primeiro e o ultimo trocados de lugar**. Em desvios em torno da media:
    #     Sxx = Syy = n(n^2 - 1)/12 * 1e-6 = 2247,5e-6
    #     Sxy = Sxx - (0,030 - 0,001)^2 = (2247,5 - 841)e-6 = 1406,5e-6
    #     correlacao = Sxy / raiz(Sxx * Syy) = 1406,5 / 2247,5 = 0,6258064516129...
    #     beta       = Sxy / Sxx           = o mesmo numero, porque Sxx = Syy
    # Nenhum dos tres enganos da isso: R2 daria 0,3916337149, a covariancia
    # 0,0000485 e correlation(ativo, ativo) daria 1.
    retornos = retornos_do_indice(30)
    datas = datas_de_retorno(30)
    trocados: list[str | None] = [*retornos]
    trocados[0], trocados[29] = trocados[29], trocados[0]
    indice = serie_indice(pares_de_datas(datas, retornos))
    ativo = serie_longa(trocados)
    beta, correlacao, observacoes = beta_and_correlation(ativo, indice, AS_OF_LONGO)
    assert observacoes == 30
    assert correlacao is not None
    assert abs(correlacao - Decimal("0.6258064516")) <= TOLERANCIA
    assert beta is not None
    assert abs(beta - Decimal("0.6258064516")) <= TOLERANCIA


def test_sem_indice_a_tripla_e_toda_nula() -> None:
    ativo = serie_longa(dobrados(retornos_do_indice(31)))
    assert beta_and_correlation(ativo, None, AS_OF_LONGO) == (None, None, None)


def test_janela_inexistente_anula_tambem_a_contagem() -> None:
    # Tres anos de serie: a janela de 60m nao existe, e ai nem a contagem ha.
    assert beta_and_correlation(SERIE_TRES_ANOS, SERIE_TRES_ANOS, AS_OF) == (
        None,
        None,
        None,
    )


def test_menos_de_trinta_pares_anula_o_numero_mas_grava_a_contagem_real() -> None:
    retornos = retornos_do_indice(31)
    datas = datas_de_retorno(31)
    # O indice so negocia em 29 das 31 datas do ativo: abaixo do minimo de 30.
    indice = serie_indice(pares_de_datas(datas, retornos)[:29])
    ativo = serie_longa(dobrados(retornos))
    beta, correlacao, observacoes = beta_and_correlation(ativo, indice, AS_OF_LONGO)
    assert beta is None
    assert correlacao is None
    # A contagem real, nunca nula: o minimo diz que o numero nao merece confianca,
    # nao que ele seja desconhecido.
    assert observacoes == 29


# --- V-08: emparelhamento por data, com orfaos dos dois lados -------------------------


def test_emparelhamento_por_data_deixa_de_fora_os_orfaos_dos_dois_lados() -> None:
    retornos = retornos_do_indice(32)
    datas = datas_de_retorno(32)
    ativo = serie_longa(dobrados(retornos))
    orfaos_do_indice: list[tuple[date, str | None]] = [
        (date(2023, 6, 1), "0.9000000000"),
        (date(2024, 6, 3), "-0.9000000000"),
    ]
    # Guarda do cenario: as duas datas do indice nao podem existir no ativo.
    assert all(d not in datas for d, _ in orfaos_do_indice)
    # E o ativo tem a primeira data de retorno, que o indice nao tem.
    pares = pares_de_datas(datas, retornos)[1:]
    indice = serie_indice(sorted(pares + orfaos_do_indice))
    beta, correlacao, observacoes = beta_and_correlation(ativo, indice, AS_OF_LONGO)
    # 32 datas de retorno do ativo, menos a que o indice nao tem: 31 pares. Os dois
    # orfaos do indice nao acrescentam nada.
    assert observacoes == 31
    # Emparelhado por posicao, o alinhamento se perde e nem o beta nem a correlacao
    # fecham: aqui eles fecham porque cada par e da mesma data.
    assert beta == Decimal("2.0000000000")
    assert correlacao == Decimal("1.0000000000")


# --- V-08b: o log_return nulo do indice sai do emparelhamento -------------------------


def test_primeiro_pregao_nulo_do_indice_dentro_da_janela_desconta_o_par() -> None:
    retornos = retornos_do_indice(31)
    datas = datas_de_retorno(31)
    ativo = serie_longa(dobrados(retornos))
    # O indice comeca dentro da janela, e no seu primeiro pregao o log_return e nulo --
    # e assim que `silver.price` grava toda serie.
    pares: list[tuple[date, str | None]] = [(datas[0], None)]
    pares += pares_de_datas(datas, retornos)[1:]
    indice = serie_indice(pares)
    beta, _, observacoes = beta_and_correlation(ativo, indice, AS_OF_LONGO)
    # 31 datas de retorno do ativo, menos o par de log_return nulo: 30.
    assert observacoes == 30
    # E o beta e o da serie **sem** aquele par.
    assert beta == Decimal("2.0000000000")


def test_o_p0_do_ativo_nao_entra_no_emparelhamento_nem_quando_o_indice_negocia() -> (
    None
):
    # O cenario e o mesmo do teste acima, com uma diferenca que existe so para que a
    # mutacao morda: o indice **negocia** na data de `P0`, com log_return nao nulo, e o
    # `P0` do ativo tambem tem log_return nao nulo (a serie comeca antes dele). Incluir
    # `P0` na janela de retornos acrescentaria um par, e a contagem abaixo mudaria.
    retornos = retornos_do_indice(31)
    datas = datas_de_retorno(31)
    ativo = serie_longa(dobrados(retornos), retorno_de_p0="0.0100000000")
    pares: list[tuple[date, str | None]] = [
        (DATA_P0, "0.5000000000"),
        (datas[0], None),
    ]
    pares += pares_de_datas(datas, retornos)[1:]
    indice = serie_indice(pares)
    beta, _, observacoes = beta_and_correlation(ativo, indice, AS_OF_LONGO)
    assert observacoes == 30
    assert beta == Decimal("2.0000000000")


def test_o_q0_do_indice_nao_e_descartado_por_ser_q0() -> None:
    # O indice comeca na primeira data de retorno do ativo, com log_return **nao nulo**:
    # esse par vale. Janelar o indice e aplicar-lhe `window_returns` o descartaria.
    retornos = retornos_do_indice(30)
    datas = datas_de_retorno(30)
    ativo = serie_longa(dobrados(retornos))
    indice = serie_indice(pares_de_datas(datas, retornos))
    _, _, observacoes = beta_and_correlation(ativo, indice, AS_OF_LONGO)
    assert observacoes == 30


# --- V-10, V-10b, V-10c: a maior queda ------------------------------------------------


def serie_de_quedas(precos: list[str]) -> list[Bar]:
    return [
        bar(date(2026, 1, 5) + timedelta(days=i), p, p) for i, p in enumerate(precos)
    ]


def test_queda_nao_recuperada_tem_data_e_duracao_nulas() -> None:
    serie = serie_de_quedas(["100", "120", "90", "95"])
    queda = max_drawdown(serie)
    # 90 / 120 - 1 = -0,25
    assert queda.depth == Decimal("-0.2500000000")
    assert queda.peak_date == date(2026, 1, 6)
    assert queda.trough_date == date(2026, 1, 7)
    # 95 nunca alcanca os 120 do topo: as duas colunas de recuperacao ficam nulas, e
    # isso e informacao, nao ausencia.
    assert queda.recovery_date is None
    assert queda.recovery_sessions is None


def test_queda_recuperada_com_as_cinco_colunas_a_mao() -> None:
    # indices:      0    1    2*    3    4    5*   6    7    8*
    serie = serie_de_quedas(
        ["100", "110", "120", "110", "100", "60", "80", "100", "125"]
    )
    queda = max_drawdown(serie)
    # 60 / 120 - 1 = -0,5
    assert queda.depth == Decimal("-0.5000000000")
    assert queda.peak_date == date(2026, 1, 7)  # indice 2
    assert queda.trough_date == date(2026, 1, 10)  # indice 5
    assert queda.recovery_date == date(2026, 1, 13)  # indice 8, o primeiro >= 120
    # Fundo no indice 5, recuperacao no 8: exclusivo na origem, inclusivo no destino.
    assert queda.recovery_sessions == 3


def test_plato_no_topo_e_empate_na_profundidade_ficam_com_a_primeira_ocorrencia() -> (
    None
):
    # indices:      0*    1      2*    3      4      5
    serie = serie_de_quedas(["100", "100", "80", "100", "100", "80"])
    queda = max_drawdown(serie)
    # Duas quedas de 80 / 100 - 1 = -0,2, e o maximo repetido em quatro pregoes.
    assert queda.depth == Decimal("-0.2000000000")
    assert queda.peak_date == date(2026, 1, 5)  # indice 0, nao o 1 nem o 4
    assert queda.trough_date == date(2026, 1, 7)  # indice 2, nao o 5
    assert queda.recovery_date == date(2026, 1, 8)  # indice 3
    assert queda.recovery_sessions == 1


def test_serie_que_so_sobe_tem_queda_zero_e_nunca_nulo() -> None:
    serie = serie_de_quedas(["100", "110", "120"])
    queda = max_drawdown(serie)
    # Sobre serie nao vazia a maior queda sempre existe, nem que seja zero -- e
    # `depth`, `peak_date` e `trough_date` nunca sao nulos.
    assert queda.depth == Decimal("0.0000000000")
    assert queda.peak_date == date(2026, 1, 5)
    assert queda.trough_date == date(2026, 1, 5)


# --- V-11: os 42 baldes -------------------------------------------------------------


def test_histograma_tem_sempre_42_baldes_em_ordem_com_as_duas_pontas_abertas() -> None:
    baldes = histogram([])
    assert [b.index for b in baldes] == list(range(42))
    assert baldes[0].lower is None
    assert baldes[0].upper == Decimal("-0.10")
    assert baldes[1].lower == Decimal("-0.10")
    assert baldes[1].upper == Decimal("-0.095")
    assert baldes[40].lower == Decimal("0.095")
    assert baldes[40].upper == Decimal("0.10")
    assert baldes[41].lower == Decimal("0.10")
    assert baldes[41].upper is None
    # Janela estatistica inexistente: os 42 existem, todos com contagem zero.
    assert [b.count for b in baldes] == [0] * 42


def test_histograma_fecha_a_esquerda_e_abre_a_direita() -> None:
    baldes = histogram(
        [
            Decimal("-0.1500000000"),  # balde 0, a ponta aberta da esquerda
            Decimal("-0.1000000000"),  # balde 1: o limite inferior pertence ao balde
            Decimal("-0.0950000000"),  # balde 2, pelo mesmo motivo
            Decimal("0.0000000000"),  # balde 21: [0,000; 0,005)
            Decimal("0.0049999999"),  # balde 21 tambem
            Decimal("0.0990000000"),  # balde 40: [0,095; 0,100)
            Decimal("0.1000000000"),  # balde 41: o superior nao pertence ao 40
            Decimal("0.2000000000"),  # balde 41, a ponta aberta da direita
        ]
    )
    contagens = {b.index: b.count for b in baldes if b.count}
    assert contagens == {0: 1, 1: 1, 2: 1, 21: 2, 40: 1, 41: 2}
    assert sum(b.count for b in baldes) == 8


# --- V-11, V-11b: o `compute` que monta tudo -----------------------------------------


def test_compute_soma_dos_baldes_igual_as_observacoes_com_a_janela_existindo() -> None:
    retornos = retornos_do_indice(31)
    metricas = compute(serie_longa(dobrados(retornos)), [], None)
    assert len(metricas.histogram) == 42
    assert [b.index for b in metricas.histogram] == list(range(42))
    assert metricas.statistical_observations == 31
    assert sum(b.count for b in metricas.histogram) == 31


def test_compute_janela_de_retornos_tem_uma_observacao_a_menos_que_a_de_pregoes() -> (
    None
):
    retornos: list[str | None] = list(retornos_do_indice(31))
    metricas = compute(serie_longa(retornos), [], None)
    # A janela de pregoes tem k = 32 (P0 mais os 31): as observacoes sao k-1 = 31.
    janela = window_bars(serie_longa(retornos), 60, AS_OF_LONGO)
    assert janela is not None
    assert len(janela) == 32
    assert metricas.statistical_observations == 31


def test_compute_um_log_return_nulo_na_janela_tira_mais_uma_observacao() -> None:
    retornos: list[str | None] = list(retornos_do_indice(31))
    retornos[10] = None
    metricas = compute(serie_longa(retornos), [], None)
    # k = 32 pregoes, um log_return nulo dentro de P1..Pn: k-2 = 30.
    assert metricas.statistical_observations == 30
    assert sum(b.count for b in metricas.histogram) == 30


def test_compute_janela_estatistica_inexistente_anula_sete_colunas_e_zera_os_baldes() -> (
    None
):
    metricas = compute(SERIE_TRES_ANOS, [], SERIE_TRES_ANOS)
    # Nulo, nunca `0`: "nao da para calcular" nao e "calculei sobre zero observacoes".
    assert metricas.statistical_observations is None
    assert metricas.volatility["60m"] is None
    assert metricas.skewness is None
    assert metricas.excess_kurtosis is None
    assert metricas.beta_60m is None
    assert metricas.correlation_60m is None
    assert metricas.benchmark_observations is None
    # Os 42 baldes existem assim mesmo, e a soma vale 0 -- que nao e igual a NULL.
    assert len(metricas.histogram) == 42
    assert sum(b.count for b in metricas.histogram) == 0


def test_compute_monta_a_linha_inteira() -> None:
    retornos = retornos_do_indice(31)
    datas = datas_de_retorno(31)
    ativo = serie_longa(dobrados(retornos))
    indice = serie_indice(pares_de_datas(datas, retornos))
    metricas = compute(
        ativo, [Dividend(date(2026, 1, 20), Decimal("1.000000"))], indice
    )
    assert metricas.as_of_date == AS_OF_LONGO
    assert metricas.first_price_date == ANTES_DE_P0
    assert metricas.price_count == 33  # o anterior, o P0 e os 31 pregoes de retorno
    assert set(metricas.returns) == {
        "1m",
        "3m",
        "6m",
        "12m",
        "36m",
        "60m",
        "120m",
        "ytd",
    }
    assert set(metricas.volatility) == {"12m", "60m"}
    # 120 meses antes de 2026-03-16 e 2016-03-16: nao ha pregao em ou antes disso.
    assert metricas.returns["120m"] is None
    assert metricas.returns["60m"] == Decimal("0.0000000000")  # adj_close constante
    assert metricas.beta_60m == Decimal("2.0000000000")
    assert metricas.benchmark_observations == 31
    # 1,00 / 10,00 = 0,1. Aqui `close == adj_close`, entao este teste NAO distingue
    # as duas escolhas de divisor -- quem prova que o divisor e o `close` e o V-18c.
    assert metricas.dividends_12m == Decimal("1.000000")
    assert metricas.dividend_payments_12m == 1
    assert metricas.dividend_yield_12m == Decimal("0.1000000000")
    # 33 pregoes: a media de 21 existe, a de 252 nao.
    assert metricas.avg_volume_21d == Decimal("1000.00")
    assert metricas.avg_volume_252d is None
    assert metricas.drawdown.depth == Decimal("0.0000000000")


# --- V-18c: o divisor do *yield* e o `close`, provado pela chamada dentro de `compute` -

# A escolha `close` x `adj_close` **nao mora** em `dividend_summary`: ela recebe
# `as_of_close` pronto e nao tem como observar de onde o chamador o tirou. Todo teste que
# a chame direto passa o divisor a mao e aprovaria as duas escolhas. O unico lugar onde a
# escolha existe e a chamada dentro de `compute` -- e so uma serie com `close != adj_close`
# a alcanca.

AS_OF_DIVIDENDO = date(2026, 3, 16)
SERIE_CLOSE_DIVERGENTE = [
    bar(date(2025, 3, 10), "20.000000", "16.000000"),
    bar(date(2025, 9, 15), "24.000000", "19.200000", log_return="0.1823215568"),
    bar(AS_OF_DIVIDENDO, "25.000000", "20.000000", log_return="0.0408219945"),
]


def test_v18c_o_compute_divide_o_yield_pelo_close_e_nao_pelo_ajustado() -> None:
    # Os dois pagamentos caem dentro dos 12 meses anteriores a 2026-03-16.
    dividendos = [
        Dividend(date(2025, 12, 10), Decimal("0.500000")),
        Dividend(date(2026, 2, 10), Decimal("1.000000")),
    ]

    metricas = compute(SERIE_CLOSE_DIVERGENTE, dividendos, None)

    assert metricas.as_of_date == AS_OF_DIVIDENDO
    assert metricas.dividends_12m == Decimal("1.500000")
    assert metricas.dividend_payments_12m == 2
    # 0,50 + 1,00 = 1,50, sobre o `close` de as_of: 1,50 / 25,00 = 0,06. Pelo `adj_close`
    # o divisor seria 20,00 e o resultado 0,075 -- e e esse par de numeros que separa as
    # duas escolhas.
    assert metricas.dividend_yield_12m == Decimal("0.0600000000")
