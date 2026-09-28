"""`compare_all`: o grupo de pares, a mediana e o percentil, puros (RF-11 a RF-14).

Sem banco. Cada cenario monta as linhas de indicador a mao; o esperado de cada numero e
conferido no comentario ao lado. Os nomes de setor, subsetor e segmento sao curtos de
proposito: o que importa e a tupla, nao o texto.
"""

from __future__ import annotations

from decimal import Decimal

from apps.fundamentals.peers import (
    INDICATORS,
    Comparison,
    IndicatorComparison,
    PeerInput,
    compare_all,
)

EMPTY = IndicatorComparison(None, None, None)


def row(
    ticker: str,
    code_cvm: str,
    tupla: tuple[str | None, str | None, str | None],
    **values: str | None,
) -> PeerInput:
    """Uma linha de indicador; indicador nao citado e nulo."""
    sector, subsector, segment = tupla
    return PeerInput(
        ticker=ticker,
        code_cvm=code_cvm,
        sector=sector,
        subsector=subsector,
        segment=segment,
        values={
            indicator: None
            if values.get(indicator) is None
            else Decimal(str(values[indicator]))
            for indicator in INDICATORS
        },
    )


def assert_no_group(comparison: Comparison) -> None:
    assert comparison.level == "none"
    assert comparison.group == (None, None, None)
    assert dict(comparison.indicators) == {indicator: EMPTY for indicator in INDICATORS}


SUG = ("S", "U", "G")


# --- RF-11: o grupo, pela tupla -------------------------------------------------------------


def test_rf11_segmento_de_tres_fica_no_segmento() -> None:
    # Um quarto no mesmo subsetor, noutro segmento, nao entra: o grupo e o segmento de 3.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", SUG, roe="3"),
            row("DDDD3", "4", ("S", "U", "H"), roe="100"),
        ]
    )
    for ticker in ("AAAA3", "BBBB3", "CCCC3"):
        assert result[ticker].level == "segment"
        assert result[ticker].group == ("S", "U", "G")
        assert result[ticker].indicators["roe"].count == 3
    # BBBB3: 1, 2, 3 -> mediana 2 (o 100 do outro segmento ficaria em 2,5).
    assert result["BBBB3"].indicators["roe"].median == Decimal("2")
    # DDDD3: segmento de 1, subsetor de 4 -> sobe.
    assert result["DDDD3"].level == "subsector"
    assert result["DDDD3"].group == ("S", "U", None)
    assert result["DDDD3"].indicators["roe"].count == 4


def test_rf11_segmento_de_dois_sobe_para_o_subsetor_de_tres() -> None:
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", ("S", "U", "H"), roe="3"),
        ]
    )
    for ticker in ("AAAA3", "BBBB3", "CCCC3"):
        assert result[ticker].level == "subsector"
        assert result[ticker].group == ("S", "U", None)
        assert result[ticker].indicators["roe"].count == 3
    # AAAA3: 1, 2, 3 -> mediana 2, nenhum abaixo de 1 -> percentil 0.
    assert result["AAAA3"].indicators["roe"] == IndicatorComparison(
        Decimal("2"), Decimal("0"), 3
    )


def test_rf11_subsetor_de_dois_fica_sem_grupo() -> None:
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
        ]
    )
    assert_no_group(result["AAAA3"])
    assert_no_group(result["BBBB3"])


def test_rf11_segmento_de_mesmo_nome_noutro_subsetor_nao_se_mistura() -> None:
    # Segmento "G" em U1 (AAAA, BBBB) e em U2 (DDDD, EEEE): 2 + 2, nunca 4.
    # U1 tem ainda CCCC, noutro segmento -> subsetor de 3; U2 fica em 2 -> sem grupo.
    result = compare_all(
        [
            row("AAAA3", "1", ("S", "U1", "G"), roe="1"),
            row("BBBB3", "2", ("S", "U1", "G"), roe="2"),
            row("CCCC3", "3", ("S", "U1", "H"), roe="3"),
            row("DDDD3", "4", ("S", "U2", "G"), roe="4"),
            row("EEEE3", "5", ("S", "U2", "G"), roe="5"),
        ]
    )
    for ticker in ("AAAA3", "BBBB3"):
        assert result[ticker].level == "subsector"
        assert result[ticker].group == ("S", "U1", None)
        assert result[ticker].indicators["roe"].count == 3
    assert_no_group(result["DDDD3"])
    assert_no_group(result["EEEE3"])


def test_rf11_segmento_nulo_comeca_no_subsetor() -> None:
    # Tres companhias sem segmento no mesmo subsetor: o nivel e o subsetor, nunca um
    # "segmento nulo".
    result = compare_all(
        [
            row("AAAA3", "1", ("S", "U", None), roe="1"),
            row("BBBB3", "2", ("S", "U", None), roe="2"),
            row("CCCC3", "3", ("S", "U", None), roe="3"),
        ]
    )
    for ticker in ("AAAA3", "BBBB3", "CCCC3"):
        assert result[ticker].level == "subsector"
        assert result[ticker].group == ("S", "U", None)
        assert result[ticker].indicators["roe"].count == 3


def test_rf11_segmento_nulo_entra_no_subsetor_dos_outros() -> None:
    # AAAA sem segmento; BBBB e CCCC num segmento de 2: o subsetor tem as tres.
    result = compare_all(
        [
            row("AAAA3", "1", ("S", "U", None), roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", SUG, roe="3"),
        ]
    )
    for ticker in ("AAAA3", "BBBB3", "CCCC3"):
        assert result[ticker].level == "subsector"
        assert result[ticker].group == ("S", "U", None)
        assert result[ticker].indicators["roe"].count == 3


def test_rf11_setor_nulo_fica_sem_grupo() -> None:
    result = compare_all(
        [
            row("AAAA3", "1", (None, "U", "G"), roe="1"),
            row("BBBB3", "2", (None, "U", "G"), roe="2"),
            row("CCCC3", "3", (None, "U", "G"), roe="3"),
        ]
    )
    for ticker in ("AAAA3", "BBBB3", "CCCC3"):
        assert_no_group(result[ticker])


def test_rf11_subsetor_nulo_fica_sem_grupo() -> None:
    result = compare_all(
        [
            row("AAAA3", "1", ("S", None, "G"), roe="1"),
            row("BBBB3", "2", ("S", None, "G"), roe="2"),
            row("CCCC3", "3", ("S", None, "G"), roe="3"),
        ]
    )
    for ticker in ("AAAA3", "BBBB3", "CCCC3"):
        assert_no_group(result[ticker])


def test_rf11_companhia_de_dois_tickers_conta_uma_vez_no_tamanho_do_grupo() -> None:
    # Segmento G: companhia 1 (AAAA3, AAAA4) e companhia 2 -> 3 tickers, 2 companhias.
    # Nao fica no segmento; sobe para o subsetor, que tem a companhia 3 -> 3 companhias.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1"),
            row("AAAA4", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", ("S", "U", "H"), roe="3"),
        ]
    )
    for ticker in ("AAAA3", "AAAA4", "BBBB3"):
        assert result[ticker].level == "subsector"
        assert result[ticker].group == ("S", "U", None)
        assert result[ticker].indicators["roe"].count == 3


def test_rf11_classificacao_da_companhia_e_a_do_menor_ticker() -> None:
    # AAAA4 esta noutro segmento no catalogo, mas a companhia 1 se classifica por AAAA3.
    result = compare_all(
        [
            row("AAAA4", "1", ("S", "U", "X"), roe="1"),
            row("AAAA3", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", SUG, roe="3"),
        ]
    )
    for ticker in ("AAAA3", "AAAA4", "BBBB3", "CCCC3"):
        assert result[ticker].level == "segment"
        assert result[ticker].group == ("S", "U", "G")
        assert result[ticker].indicators["roe"].count == 3


# --- RF-12: um valor por companhia ----------------------------------------------------------


def test_rf12_dois_tickers_um_com_pe_outro_sem_conta_uma_vez() -> None:
    # Companhia 1: AAAA3 sem pe, AAAA4 com pe 5 -> entra uma vez, com 5.
    # Para BBBB3: valores 5, 1, 2 -> n 3, mediana 2, nenhum abaixo de 1 -> percentil 0.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, pe=None),
            row("AAAA4", "1", SUG, pe="5"),
            row("BBBB3", "2", SUG, pe="1"),
            row("CCCC3", "3", SUG, pe="2"),
        ]
    )
    assert result["BBBB3"].indicators["pe"] == IndicatorComparison(
        Decimal("2"), Decimal("0"), 3
    )
    # CCCC3: valores 5, 1, 2 -> um abaixo de 2 -> 1/2.
    assert result["CCCC3"].indicators["pe"] == IndicatorComparison(
        Decimal("2"), Decimal("0.5"), 3
    )
    # AAAA3 nao tem pe: as tres nulas, mesmo com a outra acao da companhia tendo.
    assert result["AAAA3"].indicators["pe"] == EMPTY
    # AAAA4: o proprio 5, o maior -> percentil 1.
    assert result["AAAA4"].indicators["pe"] == IndicatorComparison(
        Decimal("2"), Decimal("1"), 3
    )


def test_rf12_companhia_de_dois_tickers_com_valor_nos_dois() -> None:
    # Companhia 1: AAAA3 pe 10, AAAA4 pe 20. Para as outras, vale o de AAAA3 (10), uma vez.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, pe="10"),
            row("AAAA4", "1", SUG, pe="20"),
            row("BBBB3", "2", SUG, pe="1"),
            row("CCCC3", "3", SUG, pe="2"),
        ]
    )
    # BBBB3: 10, 1, 2 -> mediana 2, n 3, percentil 0.
    assert result["BBBB3"].indicators["pe"] == IndicatorComparison(
        Decimal("2"), Decimal("0"), 3
    )
    # AAAA4: vale o proprio 20, nao o 10 da irma -> 20, 1, 2 -> mediana 2, percentil 1.
    assert result["AAAA4"].indicators["pe"] == IndicatorComparison(
        Decimal("2"), Decimal("1"), 3
    )
    # AAAA3: 10, 1, 2 -> mediana 2, percentil 1.
    assert result["AAAA3"].indicators["pe"] == IndicatorComparison(
        Decimal("2"), Decimal("1"), 3
    )


# --- RF-13: mediana, percentil, contagem ----------------------------------------------------


def test_rf13_n_impar() -> None:
    # 1, 2, 3, acao em 2 -> mediana 2, um abaixo / (3 - 1) = 0,5.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", SUG, roe="3"),
        ]
    )
    assert result["BBBB3"].indicators["roe"] == IndicatorComparison(
        Decimal("2"), Decimal("0.5"), 3
    )


def test_rf13_n_par_media_dos_dois_centrais() -> None:
    # 1, 2, 3, 4 -> mediana (2 + 3) / 2 = 2,5 -- com a propria acao; sem ela, em 4, seria 2.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, pe="1"),
            row("BBBB3", "2", SUG, pe="2"),
            row("CCCC3", "3", SUG, pe="3"),
            row("DDDD3", "4", SUG, pe="4"),
        ]
    )
    # DDDD3 em 4, o maximo: tres abaixo / 3 = 1.
    assert result["DDDD3"].indicators["pe"] == IndicatorComparison(
        Decimal("2.5"), Decimal("1"), 4
    )
    # BBBB3 em 2: um abaixo / 3 = 0,3333 (quatro casas).
    assert result["BBBB3"].indicators["pe"] == IndicatorComparison(
        Decimal("2.5"), Decimal("0.3333"), 4
    )


def test_rf13_empate_conta_so_os_estritamente_menores() -> None:
    # 1, 2, 2, acao em 2 -> um abaixo / 2 = 0,5, nao 1.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", SUG, roe="2"),
        ]
    )
    assert result["BBBB3"].indicators["roe"] == IndicatorComparison(
        Decimal("2"), Decimal("0.5"), 3
    )
    assert result["CCCC3"].indicators["roe"] == IndicatorComparison(
        Decimal("2"), Decimal("0.5"), 3
    )


def test_rf13_acao_no_minimo_e_zero_e_no_maximo_e_um() -> None:
    # 1, 2, 10: mediana 2 com a propria acao em 10 (sem ela, 1,5).
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1"),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", SUG, roe="10"),
        ]
    )
    assert result["AAAA3"].indicators["roe"] == IndicatorComparison(
        Decimal("2"), Decimal("0"), 3
    )
    assert result["CCCC3"].indicators["roe"] == IndicatorComparison(
        Decimal("2"), Decimal("1"), 3
    )


def test_rf13_n_dois_com_grupo_de_tres_companhias_e_nulo() -> None:
    # Grupo de 3 companhias, mas CCCC sem pe -> n = 2 para pe: nulo. O roe, com 3, nao.
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe="1", pe="1"),
            row("BBBB3", "2", SUG, roe="2", pe="2"),
            row("CCCC3", "3", SUG, roe="3", pe=None),
        ]
    )
    assert result["AAAA3"].level == "segment"
    assert result["AAAA3"].indicators["pe"] == EMPTY
    assert result["BBBB3"].indicators["pe"] == EMPTY
    assert result["AAAA3"].indicators["roe"] == IndicatorComparison(
        Decimal("2"), Decimal("0"), 3
    )


def test_rf13_acao_sem_o_indicador_e_nula() -> None:
    result = compare_all(
        [
            row("AAAA3", "1", SUG, roe=None),
            row("BBBB3", "2", SUG, roe="2"),
            row("CCCC3", "3", SUG, roe="3"),
            row("DDDD3", "4", SUG, roe="4"),
        ]
    )
    assert result["AAAA3"].level == "segment"
    assert result["AAAA3"].indicators["roe"] == EMPTY
    # E as outras seguem com n = 3, sem ela.
    assert result["BBBB3"].indicators["roe"] == IndicatorComparison(
        Decimal("3"), Decimal("0"), 3
    )


# --- RF-14: Decimal, quantizado as casas das colunas ----------------------------------------


def test_rf14_mediana_e_percentil_sao_decimal_nas_casas_da_coluna() -> None:
    rows = [
        row("AAAA3", "1", SUG, **dict.fromkeys(INDICATORS, "1")),
        row("BBBB3", "2", SUG, **dict.fromkeys(INDICATORS, "2")),
        row("CCCC3", "3", SUG, **dict.fromkeys(INDICATORS, "3.00000000005")),
        row("DDDD3", "4", SUG, **dict.fromkeys(INDICATORS, "4")),
    ]
    result = compare_all(rows)
    exponents = {
        "roe": -10,
        "net_margin": -10,
        "ebit_margin": -10,
        "net_debt_to_equity": -10,
        "pe": -6,
        "pb": -6,
    }
    for ticker in ("AAAA3", "BBBB3", "CCCC3", "DDDD3"):
        for indicator in INDICATORS:
            comparison = result[ticker].indicators[indicator]
            assert type(comparison.median) is Decimal
            assert type(comparison.percentile) is Decimal
            assert type(comparison.count) is int
            assert comparison.median.as_tuple().exponent == exponents[indicator]
            assert comparison.percentile.as_tuple().exponent == -4
    # Mediana (2 + 3,00000000005) / 2 = 2,500000000025: a 10 casas, 2,5000000000; a 6, 2,500000.
    assert result["AAAA3"].indicators["roe"].median == Decimal("2.5000000000")
    assert result["AAAA3"].indicators["pe"].median == Decimal("2.500000")
