"""`conform_accounts`: as contas de um documento, sobre as fixtures reais.

Cada valor esperado foi lido dos CSVs das fixtures e conferido a mao; o comentario ao lado
diz a conta e a linha do CSV de onde veio (a linha 1 e o cabecalho). Os valores do CSV
estao em milhares (`ESCALA_MOEDA = MIL`) salvo na Vivara (`UNIDADE`); o esperado aqui e em
reais. Todo documento passa por `documents_from_zip`; o que a fonte nao traz e inserido
no zip, pelo teste, e declarado nele.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Literal

import pytest

from apps.fundamentals.conform import Accounts, conform_accounts
from apps.fundamentals.documents import DocumentRows, documents_from_zip
from tests.fundamentals.conftest import CODES, Fields, edit_member, fixture_zip

MIL = Decimal(1000)
JAN_2024 = date(2024, 1, 1)


def document(
    payload: bytes, kind: Literal["itr", "dfp"], code: str, reference: date
) -> DocumentRows:
    docs = documents_from_zip(payload, kind, CODES)
    (doc,) = [d for d in docs[code] if d.reference_date == reference]
    return doc


def dfp_2024(code: str, payload: bytes | None = None) -> Accounts:
    payload = fixture_zip("dfp_2024") if payload is None else payload
    return conform_accounts(document(payload, "dfp", code, date(2024, 12, 31)))


def test_rf08_petrobras_plano_geral() -> None:
    petrobras = dfp_2024("9512")

    assert petrobras.scope == "consolidated"
    # DRE_con L127, 3.01 "Receita de Venda de Bens e/ou Servicos"
    assert petrobras.account_plan == "general"
    # BPA_con L139, conta 1
    assert petrobras.total_assets == 1124797000 * MIL
    # BPA_con L143 (1.01.01) + L145 (1.01.02), filhas fixas de 1.01 "Ativo Circulante"
    assert petrobras.cash == (20254000 + 26397000) * MIL
    # BPP_con L171 (2.01.04) + L239 (2.02.01): os niveis 3, com o arrendamento — nao os
    # niveis 4 de mesma descricao (2.01.04.01, L173, 15887000)
    assert petrobras.gross_debt == (68783000 + 304684000) * MIL
    # BPP_con L315 (2.03) - L363 (2.03.09, nao controladores)
    assert petrobras.equity_parent == (367514000 - 1508000) * MIL
    # DRE_con L127 (3.01), L161 (3.05), L195 (3.11.01 sob 3.11)
    assert petrobras.revenue == {JAN_2024: 490829000 * MIL}
    assert petrobras.ebit == {JAN_2024: 137201000 * MIL}
    assert petrobras.net_income_parent == {JAN_2024: 36606000 * MIL}
    assert petrobras.missing == []
    # dfp_cia_aberta_2024.csv L4
    assert petrobras.version == 1
    assert petrobras.received_date == date(2025, 2, 26)
    assert petrobras.name == "PETROLEO BRASILEIRO S.A. PETROBRAS"
    assert petrobras.cnpj == "33000167000101"


def test_rf08_bradesco_banco_forma_a() -> None:
    bradesco = dfp_2024("906")

    # DRE_con L363, 3.01 "Receitas de Intermediacao Financeira"
    assert bradesco.account_plan == "bank"
    # BPA_con L545, conta 1
    assert bradesco.total_assets == 2069506045 * MIL
    # BPP_con L921, 2.07.01 "Patrimonio Liquido Atribuido ao Controlador" sob 2.07 (L919)
    assert bradesco.equity_parent == 168409653 * MIL
    # DRE_con L427, 3.11.01 "Atribuido aos Socios..." sob 3.11 (L425) "Lucro ou Prejuizo
    # Liquido Consolidado do Periodo"
    assert bradesco.net_income_parent == {JAN_2024: 17252900 * MIL}
    # so `general`: nulos pelo plano, e por isso fora de `missing`
    assert bradesco.cash is None
    assert bradesco.gross_debt is None
    assert bradesco.revenue == {JAN_2024: None}
    assert bradesco.ebit == {JAN_2024: None}
    assert bradesco.missing == []


def test_rf08_itau_banco_forma_b() -> None:
    itau = dfp_2024("19348")

    # DRE_con L445, 3.01 "Receitas da Intermediacao Financeira"
    assert itau.account_plan == "bank"
    # BPA_con L627, conta 1
    assert itau.total_assets == 2854475000 * MIL
    # BPP_con L1021 (2.08 "Patrimonio Liquido Consolidado") - L1073 (2.08.09)
    assert itau.equity_parent == (221284000 - 10194000) * MIL
    # DRE_con L509, 3.09.01 sob 3.09 (L507) "Lucro/Prejuizo Consolidado do Periodo"
    assert itau.net_income_parent == {JAN_2024: 41085000 * MIL}
    assert itau.missing == []


def test_rf08_bb_seguridade_2024_nao_controladores_nao_fixa() -> None:
    bbse = dfp_2024("23159")

    # DRE_con L3, 3.01 "Receitas das Atividades Seguradoras/Resseguradoras"
    assert bbse.account_plan == "insurance"
    # BPA_con L3, conta 1
    assert bbse.total_assets == 21615587 * MIL
    # BPP_con L85 (2.03) - L143 (2.03.09, ST_CONTA_FIXA = N, valor 0)
    assert bbse.equity_parent == (9695421 - 0) * MIL
    # DRE_con L113, 3.13.01 sob 3.13 (L111) "Lucro/Prejuizo Consolidado do Periodo"
    assert bbse.net_income_parent == {JAN_2024: 8703353 * MIL}
    assert bbse.missing == []


def test_rf08_sanepar_individual_geral() -> None:
    sanepar = dfp_2024("18627")

    # DRE_ind L605, 3.01 "Receita de Venda de Bens e/ou Servicos"
    assert sanepar.account_plan == "general"
    # BPA_ind L987, conta 1
    assert sanepar.total_assets == 20508000 * MIL
    # BPA_ind L991 (1.01.01) + L997 (1.01.02, valor 0)
    assert sanepar.cash == (1800757 + 0) * MIL
    # BPP_ind L1473 (2.01.04) + L1553 (2.02.01)
    assert sanepar.gross_debt == (584638 + 6046697) * MIL
    # BPP_ind L1637, 2.03 "Patrimonio Liquido", nivel 1
    assert sanepar.equity_parent == 10828707 * MIL
    # DRE_ind L605 (3.01), L633 (3.05), L657 (3.11 "Lucro/Prejuizo do Periodo", nivel 1)
    assert sanepar.revenue == {JAN_2024: 6848219 * MIL}
    assert sanepar.ebit == {JAN_2024: 2376613 * MIL}
    assert sanepar.net_income_parent == {JAN_2024: 1545347 * MIL}
    assert sanepar.missing == []


def test_rf08_bnb_individual_banco() -> None:
    bnb = dfp_2024("1228")

    # DRE_ind L3, 3.01 "Receitas de Intermediacao Financeira"
    assert bnb.account_plan == "bank"
    # BPA_ind L3, conta 1
    assert bnb.total_assets == 69962975 * MIL
    # BPP_ind L63, 2.07 "Patrimonio Liquido", nivel 1
    assert bnb.equity_parent == 13951273 * MIL
    # DRE_ind L61, 3.11 "Lucro ou Prejuizo Liquido do Periodo", nivel 1
    assert bnb.net_income_parent == {JAN_2024: 2342566 * MIL}
    assert bnb.missing == []


def test_rf09_sanepar_e_bnb_sem_consolidado_usam_o_individual() -> None:
    assert dfp_2024("18627").scope == "individual"
    assert dfp_2024("1228").scope == "individual"
    assert dfp_2024("9512").scope == "consolidated"


def test_rf11_unidade_nao_multiplica_e_mil_multiplica() -> None:
    vivara = dfp_2024("24805")

    # Vivara, ESCALA_MOEDA = UNIDADE: os valores do CSV, em reais, sem multiplicar
    assert vivara.total_assets == Decimal(4273730310)  # BPA_con L397
    assert vivara.cash == Decimal(278153431 + 4529633)  # BPA_con L401 + L405
    assert vivara.gross_debt == Decimal(113369653 + 285191051)  # BPP_con L671 + L745
    assert vivara.equity_parent == Decimal(2496942987 - 0)  # BPP_con L823 - L881
    assert vivara.revenue == {JAN_2024: Decimal(2577113417)}  # DRE_con L285
    assert vivara.ebit == {JAN_2024: Decimal(683585305)}  # DRE_con L319
    assert vivara.net_income_parent == {JAN_2024: Decimal(653393946)}  # DRE_con L349
    # Petrobras, ESCALA_MOEDA = MIL: BPA_con L139, 1124797000 mil
    assert dfp_2024("9512").total_assets == Decimal(1124797000000)


def test_rf11_escala_desconhecida_levanta() -> None:
    """Inserido no teste (declarado): `ESCALA_MOEDA = MILHAO` nas linhas da Petrobras do
    BPA consolidado do DFP 2024."""

    def milhao(header: Fields, rows: list[Fields]) -> list[Fields]:
        scale = header.index("ESCALA_MOEDA")
        return [
            [*row[:scale], "MILHAO", *row[scale + 1 :]] if row[4] == "009512" else row
            for row in rows
        ]

    payload = edit_member(
        fixture_zip("dfp_2024"), "dfp_cia_aberta_BPA_con_2024.csv", milhao
    )
    with pytest.raises(ValueError, match="ESCALA_MOEDA MILHAO"):
        dfp_2024("9512", payload)


def test_rf12_bb_seguridade_2016_e_seguradora_por_receitas_das_operacoes() -> None:
    docs = documents_from_zip(fixture_zip("itr_2016"), "itr", CODES)

    contas = [conform_accounts(doc) for doc in docs["23159"]]
    # DRE_con L3, L140 e L428: 3.01 "Receitas das Operacoes" nos tres trimestres
    assert [c.account_plan for c in contas] == ["insurance"] * 3
    # BPP_con L253 (2.03) - L309 (2.03.09, fixa em 2016, valor 0), em 2016-06-30
    assert contas[1].equity_parent == (7985981 - 0) * MIL
    # DRE_con L400 e L401: 3.13.01, acumulado e isolado
    assert contas[1].net_income_parent == {
        date(2016, 1, 1): 2044398 * MIL,
        date(2016, 4, 1): 1086714 * MIL,
    }


def test_rf12_descricao_nova_da_3_01_e_plano_desconhecido() -> None:
    """Inserido no teste (declarado): a 3.01 da Petrobras na DRE consolidada do DFP 2024
    com uma descricao fora da tabela."""

    def nova(header: Fields, rows: list[Fields]) -> list[Fields]:
        code, label = header.index("CD_CONTA"), header.index("DS_CONTA")
        for row in rows:
            if row[4] == "009512" and row[code] == "3.01":
                row[label] = "Receitas de Atividade Nova"
        return rows

    payload = edit_member(
        fixture_zip("dfp_2024"), "dfp_cia_aberta_DRE_con_2024.csv", nova
    )
    petrobras = dfp_2024("9512", payload)

    assert petrobras.account_plan == "unknown"
    # os campos "so `general`" saem nulos, sem contar como ausentes
    assert petrobras.revenue == {JAN_2024: None}
    assert petrobras.ebit == {JAN_2024: None}
    assert petrobras.cash is None
    assert petrobras.gross_debt is None
    assert petrobras.missing == []
    # os outros se conformam: BPP_con L315 - L363; DRE_con L195
    assert petrobras.equity_parent == (367514000 - 1508000) * MIL
    assert petrobras.net_income_parent == {JAN_2024: 36606000 * MIL}


def test_rf08_codigo_diferente_com_a_mesma_descricao_anula_o_campo() -> None:
    """Inserido no teste (declarado): na Petrobras, no BPP consolidado do DFP 2024, uma
    conta 2.01.99 "Empréstimos e Financiamentos", fixa, sob a mesma mae 2.01 — copia da
    linha `ÚLTIMO` da 2.01.04 (L171) com outro codigo."""

    def outra(header: Fields, rows: list[Fields]) -> list[Fields]:
        code = header.index("CD_CONTA")
        (loans,) = [
            row
            for row in rows
            if row[4] == "009512" and row[code] == "2.01.04" and row[8] == "ÚLTIMO"
        ]
        return [*rows, [*loans[:code], "2.01.99", *loans[code + 1 :]]]

    payload = edit_member(
        fixture_zip("dfp_2024"), "dfp_cia_aberta_BPP_con_2024.csv", outra
    )
    petrobras = dfp_2024("9512", payload)

    assert petrobras.gross_debt is None
    assert petrobras.missing == ["gross_debt"]
    # o resto do documento segue: BPP_con L315 - L363
    assert petrobras.equity_parent == (367514000 - 1508000) * MIL


def test_rf08_linhas_repetidas_dao_os_mesmos_valores() -> None:
    """Inserido no teste (declarado): cada linha da Petrobras das seis demonstracoes do
    DFP 2024 repetida, identica, logo abaixo da original; o indice, com uma entrada so."""

    def repete(header: Fields, rows: list[Fields]) -> list[Fields]:
        out: list[Fields] = []
        for row in rows:
            out.append(row)
            if row[4] == "009512":
                out.append(list(row))
        return out

    payload = fixture_zip("dfp_2024")
    for statement in ("BPA_con", "BPP_con", "DRE_con", "BPA_ind", "BPP_ind", "DRE_ind"):
        member = f"dfp_cia_aberta_{statement}_2024.csv"
        payload = edit_member(payload, member, repete)
    repetida = document(payload, "dfp", "9512", date(2024, 12, 31))
    original = dfp_2024("9512")

    assert len(repetida.bpa_con) == 2 * len(
        document(fixture_zip("dfp_2024"), "dfp", "9512", date(2024, 12, 31)).bpa_con
    )
    assert conform_accounts(repetida) == original
    assert original.missing == []


def test_rf10_a_v1_inserida_perde_para_a_v2() -> None:
    """Inserido no teste (declarado): no ITR 2025, uma v1 da Petrobras de 2025-06-30 nas
    tres demonstracoes consolidadas e na `composicao_capital` — copia das linhas `ÚLTIMO`
    da v2 com `VERSAO = 1` e todos os valores trocados. O indice ja traz a v1 e a v2 (L3 e
    L4), com o mesmo `DT_RECEB`."""

    def v1(header: Fields, rows: list[Fields]) -> list[Fields]:
        version = header.index("VERSAO")
        value = header.index(
            "VL_CONTA" if "VL_CONTA" in header else "QT_ACAO_TOTAL_CAP_INTEGR"
        )
        inserted = [
            [*row[:version], "1", *row[version + 1 : value], "999", *row[value + 1 :]]
            for row in rows
            if row[1] == "2025-06-30" and row[version] == "2" and "PENÚLTIMO" not in row
        ]
        assert inserted
        return [*inserted, *rows]

    payload = fixture_zip("itr_2025")
    for statement in ("BPA_con", "BPP_con", "DRE_con", "composicao_capital"):
        payload = edit_member(payload, f"itr_cia_aberta_{statement}_2025.csv", v1)
    petrobras = conform_accounts(document(payload, "itr", "9512", date(2025, 6, 30)))

    assert petrobras.version == 2
    assert petrobras.received_date == date(2025, 8, 7)  # itr_cia_aberta_2025.csv L4
    # os valores absolutos da v2 real, linhas `ÚLTIMO` — os `PENÚLTIMO` sao de 2024-12-31
    assert petrobras.total_assets == 1174890000 * MIL  # BPA_con L133
    assert petrobras.equity_parent == (401782000 - 2560000) * MIL  # BPP_con L393 - L441
    # DRE_con L226 (acumulado, desde 2025-01-01) e L227 (isolado, desde 2025-04-01)
    assert petrobras.net_income_parent == {
        date(2025, 1, 1): 61861000 * MIL,
        date(2025, 4, 1): 26652000 * MIL,
    }
    # composicao_capital L3: a v2
    assert [
        (r["VERSAO"], r["QT_ACAO_TOTAL_CAP_INTEGR"]) for r in petrobras.capital
    ] == [("2", "12888732761")]


def test_rf10_vale_recebe_o_dt_receb_da_v3() -> None:
    vale = dfp_2024("4170")

    # dfp_cia_aberta_2024.csv L5, L6 e L7: v1 em 2025-02-19, v2 em 2025-02-21, v3 em
    # 2025-03-17; as demonstracoes so tem a v3
    assert vale.version == 3
    assert vale.received_date == date(2025, 3, 17)


# RF-08b


def set_values(
    cd_cvm: str, refer: str, values: dict[tuple[str, str], str | None]
) -> Callable[[Fields, list[Fields]], list[Fields]]:
    """Edicao das linhas `ÚLTIMO` de `cd_cvm` em `refer`: `(CD_CONTA, DT_INI_EXERC)` →
    novo `VL_CONTA`, ou `None` para tirar a linha. Toda chave tem de casar uma linha."""

    def edit(header: Fields, rows: list[Fields]) -> list[Fields]:
        code, start = header.index("CD_CONTA"), header.index("DT_INI_EXERC")
        order, value = header.index("ORDEM_EXERC"), header.index("VL_CONTA")
        seen: set[tuple[str, str]] = set()
        out: list[Fields] = []
        for row in rows:
            key = (row[code], row[start])
            if (
                row[4] == cd_cvm
                and row[1] == refer
                and row[order] == "ÚLTIMO"
                and key in values
            ):
                seen.add(key)
                new = values[key]
                if new is None:
                    continue
                row[value] = new
            out.append(row)
        assert seen == set(values), set(values) - seen
        return out

    return edit


def dfp_2024_dre(code: str, values: dict[tuple[str, str], str | None]) -> Accounts:
    cd_cvm = code.zfill(6)
    payload = edit_member(
        fixture_zip("dfp_2024"),
        "dfp_cia_aberta_DRE_con_2024.csv",
        set_values(cd_cvm, "2024-12-31", values),
    )
    return dfp_2024(code, payload)


def test_rf08b_filhas_zeradas_vale_a_mae() -> None:
    """Inserido no teste (declarado): na Petrobras, DRE consolidada do DFP 2024, a 3.11.01
    (L195) e a 3.11.02 (L197) trocadas para 0; a mae 3.11 (L193) fica em 37009000."""
    petrobras = dfp_2024_dre(
        "9512",
        {("3.11.01", "2024-01-01"): "0.0000000000", ("3.11.02", "2024-01-01"): "0"},
    )

    assert petrobras.net_income_parent == {JAN_2024: 37009000 * MIL}
    assert petrobras.missing == []


def test_rf08b_filha_dos_nao_controladores_ausente_conta_como_zero() -> None:
    """Inserido no teste (declarado): na Petrobras, DRE consolidada do DFP 2024, a 3.11.01
    (L195) trocada para 0 e a linha `ÚLTIMO` da 3.11.02 (L197) tirada."""
    petrobras = dfp_2024_dre(
        "9512", {("3.11.01", "2024-01-01"): "0", ("3.11.02", "2024-01-01"): None}
    )

    assert petrobras.net_income_parent == {JAN_2024: 37009000 * MIL}


def test_rf08b_filhas_que_nao_somam_zero_seguem_a_filha() -> None:
    """Inserido no teste (declarado): na Petrobras, DRE consolidada do DFP 2024, so a
    3.11.01 (L195) trocada para 0; a 3.11.02 (L197) segue em 403000."""
    petrobras = dfp_2024_dre("9512", {("3.11.01", "2024-01-01"): "0"})

    assert petrobras.net_income_parent == {JAN_2024: Decimal(0)}
    # sem edicao, as filhas nao somam 0: a 3.11.01 (L195)
    assert dfp_2024("9512").net_income_parent == {JAN_2024: 36606000 * MIL}


def test_rf08b_mae_e_filhas_zeradas_da_zero() -> None:
    """Inserido no teste (declarado): na Petrobras, DRE consolidada do DFP 2024, a 3.11
    (L193), a 3.11.01 (L195) e a 3.11.02 (L197) trocadas para 0."""
    petrobras = dfp_2024_dre(
        "9512",
        {
            ("3.11", "2024-01-01"): "0",
            ("3.11.01", "2024-01-01"): "0",
            ("3.11.02", "2024-01-01"): "0",
        },
    )

    assert petrobras.net_income_parent == {JAN_2024: Decimal(0)}
    assert petrobras.missing == []


def test_rf08b_banco_com_aos_socios_nao_controladores() -> None:
    """Inserido no teste (declarado): no Bradesco, DRE consolidada do DFP 2024, a 3.11.01
    "Atribuído aos Sócios da Empresa Controladora" (L427) e a 3.11.02 "Atribuído aos
    Sócios não Controladores" (L429) trocadas para 0; a mae 3.11 (L425) fica."""
    bradesco = dfp_2024_dre(
        "906",
        {("3.11.01", "2024-01-01"): "0", ("3.11.02", "2024-01-01"): "0"},
    )

    assert bradesco.net_income_parent == {JAN_2024: 17542153 * MIL}


def test_rf08b_banco_controladora_zero_e_nao_controladores_nao_zero() -> None:
    """Inserido no teste (declarado): no Bradesco, DRE consolidada do DFP 2024, so a
    3.11.01 (L427) trocada para 0; a 3.11.02 "Atribuído aos Sócios não Controladores"
    (L429) segue em 289253 e a mae 3.11 (L425) em 17542153. As filhas nao somam 0 — o que
    so se ve se a grafia com "não" minusculo for achada."""
    bradesco = dfp_2024_dre("906", {("3.11.01", "2024-01-01"): "0"})

    assert bradesco.net_income_parent == {JAN_2024: Decimal(0)}
    assert bradesco.missing == []


def test_rf08b_filha_dos_nao_controladores_repetida_segue_o_rf08() -> None:
    """Inserido no teste (declarado): na Petrobras, DRE consolidada do DFP 2024, a 3.11.01
    (L195) e a 3.11.02 (L197) trocadas para 0, e uma 3.11.03 "Atribuído a Sócios Não
    Controladores" sob a mesma mae 3.11 — copia da linha `ÚLTIMO` da 3.11.02 ja zerada,
    com outro codigo. A filha dos nao controladores repetida: o RF-08b nao se aplica, e
    vale a filha da controladora, 0 — nao a mae (L193, 37009000)."""

    def repete(header: Fields, rows: list[Fields]) -> list[Fields]:
        code = header.index("CD_CONTA")
        (minority,) = [
            row
            for row in rows
            if row[4] == "009512" and row[code] == "3.11.02" and row[8] == "ÚLTIMO"
        ]
        return [*rows, [*minority[:code], "3.11.03", *minority[code + 1 :]]]

    member = "dfp_cia_aberta_DRE_con_2024.csv"
    payload = edit_member(
        fixture_zip("dfp_2024"),
        member,
        set_values(
            "009512",
            "2024-12-31",
            {("3.11.01", "2024-01-01"): "0", ("3.11.02", "2024-01-01"): "0"},
        ),
    )
    payload = edit_member(payload, member, repete)
    petrobras = dfp_2024("9512", payload)

    assert petrobras.net_income_parent == {JAN_2024: Decimal(0)}


def test_rf08b_mae_zero_com_filhas_opostas_segue_a_filha() -> None:
    """Inserido no teste (declarado): na Petrobras, DRE consolidada do DFP 2024, a mae 3.11
    (L193) trocada para 0 e a 3.11.02 (L197) para -36606000; a 3.11.01 (L195) segue em
    36606000. As filhas somam 0, mas a mae tambem e 0: vale a filha da controladora."""
    petrobras = dfp_2024_dre(
        "9512",
        {("3.11", "2024-01-01"): "0", ("3.11.02", "2024-01-01"): "-36606000"},
    )

    assert petrobras.net_income_parent == {JAN_2024: 36606000 * MIL}
    assert petrobras.missing == []


def test_rf08b_vale_por_periodo() -> None:
    """Inserido no teste (declarado): na Petrobras, DRE consolidada do ITR 2024, em
    2024-06-30, so o periodo isolado (desde 2024-04-01) da 3.11.01 (L861) e da 3.11.02
    (L865) trocado para 0. A mae isolada 3.11 (L857) vale -2515000; o acumulado (desde
    2024-01-01) segue a filha, L860."""
    payload = edit_member(
        fixture_zip("itr_2024"),
        "itr_cia_aberta_DRE_con_2024.csv",
        set_values(
            "009512",
            "2024-06-30",
            {("3.11.01", "2024-04-01"): "0", ("3.11.02", "2024-04-01"): "0"},
        ),
    )
    petrobras = conform_accounts(document(payload, "itr", "9512", date(2024, 6, 30)))

    assert petrobras.net_income_parent == {
        JAN_2024: 21095000 * MIL,
        date(2024, 4, 1): -2515000 * MIL,
    }
