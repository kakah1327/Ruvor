"""`conform_year`: trimestre isolado, 4o trimestre e acoes, sobre as fixtures reais.

Cada valor esperado foi lido dos CSVs das fixtures e conferido a mao; o comentario ao lado
diz a conta e a linha do CSV de onde veio (a linha 1 e o cabecalho). Os valores do CSV
estao em milhares (`ESCALA_MOEDA = MIL`); o esperado aqui e em reais. O LPA vem em reais
por acao, sem escala; as quantidades de acoes, como vieram. Todo documento passa por
`documents_from_zip`; o que a fonte nao traz e inserido no zip, pelo teste, e declarado
nele.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Literal

from apps.fundamentals.conform import (
    ConformedStatement,
    conform_year,
    infer_share_scale,
    itr_superseded_by_dfp,
)
from apps.fundamentals.documents import DocumentRows, documents_from_zip
from tests.fundamentals.conftest import CODES, Fields, edit_member, fixture_zip

MIL = Decimal(1000)
PETROBRAS = "009512"  # `CD_CVM` como vem no CSV
PETROBRAS_CNPJ = "33.000.167/0001-01"  # `CNPJ_CIA` como vem no CSV
Q1, Q2, Q3, Q4 = (
    date(2024, 3, 31),
    date(2024, 6, 30),
    date(2024, 9, 30),
    date(2024, 12, 31),
)


def documents(
    payload: bytes, kind: Literal["itr", "dfp"], code: str
) -> list[DocumentRows]:
    return documents_from_zip(payload, kind, CODES).get(code, [])


def by_date(statements: list[ConformedStatement]) -> dict[date, ConformedStatement]:
    return {statement.reference_date: statement for statement in statements}


def petrobras_2024(
    itr: bytes | None = None, dfp: bytes | None = None
) -> dict[date, ConformedStatement]:
    """`conform_year` da Petrobras no ano de 2024: ITR e DFP de 2024, sem ITR de 2023."""
    itr = fixture_zip("itr_2024") if itr is None else itr
    dfp = fixture_zip("dfp_2024") if dfp is None else dfp
    return by_date(
        conform_year(documents(itr, "itr", "9512"), documents(dfp, "dfp", "9512"), [])
    )


def dfp_2024(code: str, payload: bytes | None = None) -> ConformedStatement:
    payload = fixture_zip("dfp_2024") if payload is None else payload
    (statement,) = conform_year([], documents(payload, "dfp", code), [])
    return statement


def drop_petrobras(reference: str) -> Callable[[Fields, list[Fields]], list[Fields]]:
    """Edicao que tira do membro as linhas da Petrobras com `DT_REFER == reference`."""

    def edit(header: Fields, rows: list[Fields]) -> list[Fields]:
        code, refer = header.index("CD_CVM"), header.index("DT_REFER")
        return [
            row
            for row in rows
            if not (row[code] == PETROBRAS and row[refer] == reference)
        ]

    return edit


# Os membros do ITR 2024 que `documents_from_zip` le: o indice, as seis demonstracoes e a
# `composicao_capital`.
ITR_2024_MEMBERS = (
    "itr_cia_aberta_2024.csv",
    *(
        f"itr_cia_aberta_{statement}_2024.csv"
        for statement in (
            "BPA_con",
            "BPA_ind",
            "BPP_con",
            "BPP_ind",
            "DRE_con",
            "DRE_ind",
        )
    ),
    "itr_cia_aberta_composicao_capital_2024.csv",
)


def itr_2024_with_petrobras_at_dfp_date() -> bytes:
    """O ITR 2024 com um documento da Petrobras em 2024-12-31, a data do DFP 2024.

    Inserido no teste (declarado — a fonte real nao tem ITR em 2024-12-31): em cada membro
    de `ITR_2024_MEMBERS`, as linhas da Petrobras (pelo `CNPJ_CIA`) de 2024-09-30 copiadas
    com `DT_REFER = 2024-12-31`. As de 2024-09-30 ficam: o 4o trimestre segue tendo o ITR
    de setembro como anterior.
    """

    def copy_to_q4(header: Fields, rows: list[Fields]) -> list[Fields]:
        cnpj, refer = header.index("CNPJ_CIA"), header.index("DT_REFER")
        copies = []
        for row in rows:
            if row[cnpj] == PETROBRAS_CNPJ and row[refer] == Q3.isoformat():
                copy = list(row)
                copy[refer] = Q4.isoformat()
                copies.append(copy)
        assert copies, "sem linha da Petrobras em 2024-09-30"
        return [*rows, *copies]

    payload = fixture_zip("itr_2024")
    for member in ITR_2024_MEMBERS:
        payload = edit_member(payload, member, copy_to_q4)
    return payload


def test_rf13b_itr_na_data_do_dfp_e_descartado_e_vale_o_dfp() -> None:
    itr = documents(itr_2024_with_petrobras_at_dfp_date(), "itr", "9512")
    dfp = documents(fixture_zip("dfp_2024"), "dfp", "9512")
    assert [doc.reference_date for doc in itr] == [Q1, Q2, Q3, Q4]  # o cenario montou

    statements = conform_year(itr, dfp, [])

    assert itr_superseded_by_dfp(itr, dfp) == [Q4]
    assert [s.reference_date for s in statements] == [Q1, Q2, Q3, Q4]  # uma linha so
    q4 = statements[-1]
    assert q4.source == "dfp"
    # os valores do DFP, iguais aos da Petrobras sem o ITR inserido: o balanco do DFP
    # (BPA_con L139) e o 4o trimestre DFP menos o ITR de setembro (DRE_con L127)
    assert q4 == petrobras_2024()[Q4]
    assert q4.total_assets == 1124797000 * MIL
    assert q4.revenue == (490829000 - 369561000) * MIL
    # sem DFP na data, nada e descartado
    assert itr_superseded_by_dfp(itr, []) == []


def test_rf13_petrobras_2024_tres_trimestres_isolados_do_itr() -> None:
    petrobras = petrobras_2024()

    assert [petrobras[q].source for q in (Q1, Q2, Q3, Q4)] == ["itr"] * 3 + ["dfp"]
    assert {petrobras[q].fiscal_year_start for q in petrobras} == {date(2024, 1, 1)}
    # itr_cia_aberta_DRE_con_2024.csv; o 1o trimestre tem um periodo so (L637, L671, L705)
    assert petrobras[Q1].revenue == 117721000 * MIL  # 3.01
    assert petrobras[Q1].ebit == 44027000 * MIL  # 3.05
    assert petrobras[Q1].net_income_parent == 23700000 * MIL  # 3.11.01
    # 2o: o isolado, desde 2024-04-01 (L725, L793, L861) — nao o semestre (L724, 239979000)
    assert petrobras[Q2].revenue == 122258000 * MIL
    assert petrobras[Q2].ebit == 33543000 * MIL
    assert petrobras[Q2].net_income_parent == -2605000 * MIL
    # 3o: o isolado, desde 2024-07-01 (L897, L965, L1033)
    assert petrobras[Q3].revenue == 129582000 * MIL
    assert petrobras[Q3].ebit == 46462000 * MIL
    assert petrobras[Q3].net_income_parent == 32555000 * MIL
    # balanco: a posicao na data, conta 1 do BPA_con (L411, L541, L671)
    assert petrobras[Q1].total_assets == 1067292000 * MIL
    assert petrobras[Q2].total_assets == 1058688000 * MIL
    assert petrobras[Q3].total_assets == 1077849000 * MIL


def test_rf14_petrobras_2024_quarto_trimestre_e_o_dfp_menos_nove_meses() -> None:
    q4 = petrobras_2024()[Q4]

    # dfp_cia_aberta_DRE_con_2024.csv L127, L161, L195 (o ano) menos o acumulado de nove
    # meses do ITR de 2024-09-30, itr_cia_aberta_DRE_con_2024.csv L896, L964, L1032
    assert q4.revenue == (490829000 - 369561000) * MIL
    assert q4.ebit == (137201000 - 124032000) * MIL
    assert q4.net_income_parent == (36606000 - 53650000) * MIL
    # os quatro isolados somam o ano
    petrobras = petrobras_2024()
    assert sum(petrobras[q].revenue or 0 for q in (Q1, Q2, Q3, Q4)) == 490829000 * MIL
    # balanco: o do DFP, BPA_con L139
    assert q4.total_assets == 1124797000 * MIL
    assert q4.fiscal_year_start == date(2024, 1, 1)


def test_rf13_camil_exercicio_de_marco_a_fevereiro() -> None:
    itr = documents(fixture_zip("itr_2024"), "itr", "24228")
    camil = by_date(conform_year(itr, [], []))

    may, aug, nov = date(2024, 5, 31), date(2024, 8, 31), date(2024, 11, 30)
    assert set(camil) == {may, aug, nov}
    assert {s.fiscal_year_start for s in camil.values()} == {date(2024, 3, 1)}
    # itr_cia_aberta_DRE_con_2024.csv, 3.11.01: L2687 (1o tri, periodo unico), L2795
    # (desde 2024-06-01) e L2915 (desde 2024-09-01)
    assert camil[may].net_income_parent == 78493 * MIL
    assert camil[aug].net_income_parent == 118747 * MIL
    assert camil[nov].net_income_parent == 44339 * MIL
    # 3.01: L2641, L2703, L2823
    assert camil[may].revenue == 2899616 * MIL
    assert camil[aug].revenue == 3261560 * MIL
    assert camil[nov].revenue == 3104615 * MIL


def test_rf14_camil_quarto_trimestre_usa_o_itr_do_zip_anterior() -> None:
    dfp = documents(fixture_zip("dfp_2025"), "dfp", "24228")
    itr_prev = documents(fixture_zip("itr_2024"), "itr", "24228")

    (q4,) = conform_year([], dfp, itr_prev)

    assert q4.reference_date == date(2025, 2, 28)
    assert q4.fiscal_year_start == date(2024, 3, 1)
    # dfp_cia_aberta_DRE_con_2025.csv L3, L23, L49 (o exercicio) menos o acumulado do ITR
    # de 2024-11-30, itr_cia_aberta_DRE_con_2024.csv L2822, L2862, L2914 — 90 dias antes
    assert q4.revenue == (12262939 - 9265791) * MIL
    assert q4.ebit == (640999 - 514161) * MIL
    assert q4.net_income_parent == (216950 - 241579) * MIL
    # balanco: o do DFP, dfp_cia_aberta_BPA_con_2025.csv L3
    assert q4.total_assets == 11106595 * MIL
    # so no zip do mesmo ano (o ITR de 2025 nao tem a Camil), o 4o trimestre sai nulo
    (sozinho,) = conform_year([], dfp, [])
    assert sozinho.net_income_parent is None
    assert sozinho.total_assets == 11106595 * MIL


def test_rf14_sem_o_itr_de_setembro_o_quarto_trimestre_e_nulo() -> None:
    """Removido no teste (declarado): o documento de 2024-09-30 da lista de ITR. O ITR
    anterior passa a ser o de 2024-06-30, 184 dias antes — fora de 88 a 93."""
    itr = [
        doc
        for doc in documents(fixture_zip("itr_2024"), "itr", "9512")
        if doc.reference_date != Q3
    ]
    dfp = documents(fixture_zip("dfp_2024"), "dfp", "9512")

    q4 = by_date(conform_year(itr, dfp, []))[Q4]

    assert q4.revenue is None
    assert q4.ebit is None
    assert q4.net_income_parent is None
    assert q4.total_assets == 1124797000 * MIL  # BPA_con L139
    assert q4.equity_parent == (367514000 - 1508000) * MIL  # BPP_con L315 - L363


def test_rf14_escopos_diferentes_anulam_o_quarto_trimestre() -> None:
    """Removido no teste (declarado): as linhas da Petrobras de 2024-09-30 no BPA, BPP e
    DRE consolidados do ITR 2024 — o ITR de setembro passa a ser individual; o DFP segue
    consolidado."""
    itr = fixture_zip("itr_2024")
    for statement in ("BPA_con", "BPP_con", "DRE_con"):
        itr = edit_member(
            itr, f"itr_cia_aberta_{statement}_2024.csv", drop_petrobras("2024-09-30")
        )

    petrobras = petrobras_2024(itr=itr)

    assert petrobras[Q3].scope == "individual"
    assert petrobras[Q3].fiscal_year_start == date(2024, 1, 1)
    assert petrobras[Q4].scope == "consolidated"
    assert petrobras[Q4].revenue is None
    assert petrobras[Q4].ebit is None
    assert petrobras[Q4].net_income_parent is None
    assert petrobras[Q4].total_assets == 1124797000 * MIL  # BPA_con L139


def test_rf13_documento_sem_dre_nao_tem_inicio_de_exercicio() -> None:
    """Removido no teste (declarado): as linhas da Petrobras de 2024-06-30 na DRE
    consolidada e na individual do ITR 2024."""
    itr = fixture_zip("itr_2024")
    for statement in ("DRE_con", "DRE_ind"):
        itr = edit_member(
            itr, f"itr_cia_aberta_{statement}_2024.csv", drop_petrobras("2024-06-30")
        )

    petrobras = petrobras_2024(itr=itr)

    assert petrobras[Q2].fiscal_year_start is None
    assert petrobras[Q2].revenue is None
    assert petrobras[Q2].ebit is None
    assert petrobras[Q2].net_income_parent is None
    assert petrobras[Q2].scope == "consolidated"
    assert petrobras[Q2].total_assets == 1058688000 * MIL  # BPA_con L541
    # os outros trimestres seguem: DRE_con L705 e L1033
    assert petrobras[Q1].net_income_parent == 23700000 * MIL
    assert petrobras[Q3].net_income_parent == 32555000 * MIL


def test_rf15_escala_das_acoes_petrobras_unidade_vale_e_itau_mil() -> None:
    petrobras, vale, itau = dfp_2024("9512"), dfp_2024("4170"), dfp_2024("19348")

    # Petrobras: L = 36606000 mil (DRE_con L195), N = 13044496930 - 155764169
    # (composicao_capital L4), E = 2.84 (DRE_con L203, 3.99.01.01 ON) → 2.8402 por acao
    assert petrobras.shares_scale == 1
    assert petrobras.shares_on == 7442454142 - 222760
    assert petrobras.shares_pn == 5602042788 - 155541409
    # Vale: L = 31592000 mil, N = 4539008 - 270288 (L5), E = 7.39 (L277, 3.99.01.02 ON —
    # a 3.99.01.01 PNA, L275, vale 0 e e pulada) → 7401 por acao: mil
    assert vale.shares_scale == 1000
    assert vale.shares_on == (4539008 - 270288) * 1000
    assert vale.shares_pn == 0
    # Itau: L = 41085000 mil, N = 9776104 - 28031 (L8), E = 4.20 (L517, 3.99.01.01 ON — a
    # mae 3.99.01, L515, vale 8.40 e nao conta) → 4215 por acao: mil
    assert itau.shares_scale == 1000
    assert itau.shares_on == (4958290 - 0) * 1000
    assert itau.shares_pn == (4817814 - 28031) * 1000
    assert petrobras.share_composition and vale.share_composition
    assert itau.share_composition


def test_rf15_petrobras_itr_2025_usa_o_lpa_acumulado() -> None:
    itr = documents(fixture_zip("itr_2025"), "itr", "9512")

    june = by_date(conform_year(itr, [], []))[date(2025, 6, 30)]

    # composicao_capital L3 (v2): 12888732761 integralizadas, 0 em tesouraria
    assert june.shares_scale == 1
    assert june.shares_on == 7442231382
    assert june.shares_pn == 5446501379
    # L acumulado 61861000 mil (DRE_con L226), N = 12888732761: 4.7996 por acao. O LPA
    # acumulado e 4.80 (L242); o isolado, 2.07 (L243), fica fora do fator 2
    lucro, acoes = 61861000 * MIL, 12888732761
    assert infer_share_scale(lucro, acoes, Decimal("4.80")) == 1
    assert infer_share_scale(lucro, acoes, Decimal("2.07")) is None


def test_rf15_lpa_incoerente_da_quantidade_nula() -> None:
    """Inserido no teste (declarado): o LPA 3.99.01.01 da Petrobras na DRE consolidada do
    DFP 2024 (L203) trocado de 2.84 para 100 — incoerente com o lucro nas duas escalas."""

    def incoerente(header: Fields, rows: list[Fields]) -> list[Fields]:
        code, value = header.index("CD_CONTA"), header.index("VL_CONTA")
        for row in rows:
            if row[4] == PETROBRAS and row[code] == "3.99.01.01":
                row[value] = "100.0000000000"
        return rows

    payload = edit_member(
        fixture_zip("dfp_2024"), "dfp_cia_aberta_DRE_con_2024.csv", incoerente
    )
    petrobras = dfp_2024("9512", payload)

    assert petrobras.shares_scale is None
    assert petrobras.shares_on is None
    assert petrobras.shares_pn is None
    assert petrobras.share_composition is True


def test_rf15_antes_de_2020_nao_ha_composicao_do_capital() -> None:
    itr = documents(fixture_zip("itr_2019"), "itr", "9512")

    petrobras = conform_year(itr, [], [])

    assert len(petrobras) == 3
    for statement in petrobras:
        assert statement.share_composition is False
        assert statement.shares_scale is None
        assert statement.shares_on is None
        assert statement.shares_pn is None
    # o resto se conforma: DRE_con L71, 3.11.01
    assert petrobras[0].net_income_parent == 4031000 * MIL


def test_rf15_quantidade_negativa_da_nulo_sem_excecao() -> None:
    """Inserido no teste (declarado): na `composicao_capital` do DFP 2024 (L4), a
    tesouraria total da Petrobras trocada para 20000000000 — mais que as integralizadas."""

    def negativa(header: Fields, rows: list[Fields]) -> list[Fields]:
        cnpj, treasury = header.index("CNPJ_CIA"), header.index("QT_ACAO_TOTAL_TESOURO")
        for row in rows:
            if row[cnpj] == "33.000.167/0001-01":
                row[treasury] = "20000000000"
        return rows

    payload = edit_member(
        fixture_zip("dfp_2024"), "dfp_cia_aberta_composicao_capital_2024.csv", negativa
    )
    petrobras = dfp_2024("9512", payload)

    assert petrobras.shares_scale is None
    assert petrobras.shares_on is None
    assert petrobras.shares_pn is None
    assert petrobras.share_composition is True
    assert infer_share_scale(36606000 * MIL, -1, Decimal("2.84")) is None


def test_rf12_plano_por_documento() -> None:
    """Inserido no teste (declarado): a 3.01 da Petrobras de 2024-06-30 na DRE consolidada
    do ITR 2024 (L724 e L725) com a descricao "Receitas da Intermediação Financeira"."""

    def banco(header: Fields, rows: list[Fields]) -> list[Fields]:
        refer, code = header.index("DT_REFER"), header.index("CD_CONTA")
        label = header.index("DS_CONTA")
        for row in rows:
            if (
                row[4] == PETROBRAS
                and row[refer] == "2024-06-30"
                and row[code] == "3.01"
            ):
                row[label] = "Receitas da Intermediação Financeira"
        return rows

    itr = edit_member(fixture_zip("itr_2024"), "itr_cia_aberta_DRE_con_2024.csv", banco)
    petrobras = petrobras_2024(itr=itr)

    assert petrobras[Q2].account_plan == "bank"
    assert petrobras[Q2].revenue is None
    assert petrobras[Q2].ebit is None
    # o lucro nao e "so `general`": DRE_con L861
    assert petrobras[Q2].net_income_parent == -2605000 * MIL
    for q in (Q1, Q3, Q4):
        assert petrobras[q].account_plan == "general"
        assert petrobras[q].revenue is not None
    # DRE_con L637, L897; o 4o, DFP L127 - ITR L896
    assert petrobras[Q1].revenue == 117721000 * MIL
    assert petrobras[Q3].revenue == 129582000 * MIL
    assert petrobras[Q4].revenue == (490829000 - 369561000) * MIL
