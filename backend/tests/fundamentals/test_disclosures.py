"""A conformacao pura do IPE (M3.2) e as fixtures `ipe_2025.zip` e `ipe_2026.zip`.

Os testes `test_fixtures_*` conferem que cada caso que o `README.md` de
`tests/fixtures/cvm/` registra esta no zip, pelo link que o `recortar.py` imprimiu. Os
`test_rf*` provam `disclosures_from_zip` e `title_of` (RF-03, RF-04, RF-04b, RF-05, RF-06);
o que a fonte nao traz — link repetido, registro mal formado, titulo so em `Especie` — e
declarado no teste por `edit_member`, sobre linhas reais das fixtures.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import date

from apps.fundamentals.disclosures import (
    CATEGORIES,
    ConformedDisclosure,
    DisclosuresByCompany,
    disclosures_from_zip,
    title_of,
)
from tests.fundamentals.conftest import (
    CODES,
    IPE_EXTRA_CODES,
    edit_member,
    fixture_zip,
    ipe_rows,
)

LINK = (
    "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE"
    "&CodigoInstituicao=1&numProtocolo={}&numSequencia={}&numVersao={}"
)
THREE = {"Fato Relevante", "Comunicado ao Mercado", "Aviso aos Acionistas"}

# Os casos do README, com o link como o `recortar.py` imprimiu.
PETROBRAS_FACT = LINK.format(1569745, 1094451, 1)
LONGEST_SUBJECT = LINK.format(1525123, 1049829, 1)
SAME_DELIVERY = (LINK.format(1337188, 861914, 1), LINK.format(1337189, 861915, 1))
REISSUED = LINK.format(1491850, 1016556, 2)
EMPTY_SUBJECT_NOTICE = LINK.format(1544497, 1069203, 1)  # Comunicado ao Mercado
EMPTY_SUBJECT_SHAREHOLDERS = LINK.format(1497199, 1021905, 1)  # Aviso aos Acionistas
OUTSIDE_CODE = "26190"  # fora do catalogo e de `CODES`
OUTSIDE = (LINK.format(1483373, 1008079, 1), LINK.format(1528345, 1053051, 1))


def rows_by_link(year: int) -> dict[str, dict[str, str]]:
    header, rows = ipe_rows(fixture_zip(f"ipe_{year}"), year)
    by_link = {
        row[header.index("Link_Download")]: dict(zip(header, row)) for row in rows
    }
    assert len(by_link) == len(rows), "link repetido na fixture"
    return by_link


def test_fixtures_ipe_2026_traz_o_fato_relevante_da_petrobras() -> None:
    row = rows_by_link(2026)[PETROBRAS_FACT]
    assert row["Codigo_CVM"] == "9512"
    assert row["Categoria"] == "Fato Relevante"
    assert row["Data_Entrega"] == "2026-09-19"
    assert row["Assunto"] == "Petrobras informa sobre adesão à nova subvenção econômica"


def test_fixtures_ipe_2026_traz_o_assunto_de_761_caracteres() -> None:
    row = rows_by_link(2026)[LONGEST_SUBJECT]
    assert len(row["Assunto"]) == 761
    assert row["Codigo_CVM"] in IPE_EXTRA_CODES
    assert row["Categoria"] in THREE


def test_fixtures_ipe_2025_traz_o_mesmo_protocolo_e_versao_com_dois_links() -> None:
    rows = rows_by_link(2025)
    first, second = (rows[link] for link in SAME_DELIVERY)
    assert first["Codigo_CVM"] == second["Codigo_CVM"] == "9512"
    assert first["Protocolo_Entrega"] == second["Protocolo_Entrega"]
    assert first["Versao"] == second["Versao"]
    assert first["Categoria"] in THREE and second["Categoria"] in THREE


def test_fixtures_ipe_2026_traz_uma_reapresentacao() -> None:
    row = rows_by_link(2026)[REISSUED]
    assert row["Tipo_Apresentacao"].startswith("RE")
    assert int(row["Versao"]) > 1
    assert row["Codigo_CVM"] in CODES
    assert row["Categoria"] in THREE


def test_fixtures_ipe_2026_traz_assunto_vazio_nas_duas_categorias() -> None:
    rows = rows_by_link(2026)
    notice = rows[EMPTY_SUBJECT_NOTICE]
    shareholders = rows[EMPTY_SUBJECT_SHAREHOLDERS]
    assert (notice["Categoria"], notice["Assunto"]) == ("Comunicado ao Mercado", "")
    assert (shareholders["Categoria"], shareholders["Assunto"]) == (
        "Aviso aos Acionistas",
        "",
    )
    assert notice["Codigo_CVM"] in CODES
    assert shareholders["Codigo_CVM"] in IPE_EXTRA_CODES


def test_fixtures_ipe_2026_traz_duas_linhas_de_companhia_fora_do_catalogo() -> None:
    rows = rows_by_link(2026)
    assert OUTSIDE_CODE not in CODES | IPE_EXTRA_CODES
    assert [rows[link]["Codigo_CVM"] for link in OUTSIDE] == [OUTSIDE_CODE] * 2
    assert all(rows[link]["Categoria"] in THREE for link in OUTSIDE)


def test_fixtures_ipe_trazem_as_nove_nas_tres_categorias_e_assembleia() -> None:
    for year in (2025, 2026):
        rows = rows_by_link(year).values()
        three = Counter(row["Codigo_CVM"] for row in rows if row["Categoria"] in THREE)
        assembly = Counter(
            row["Codigo_CVM"] for row in rows if row["Categoria"] == "Assembleia"
        )
        for code in CODES:
            assert 1 <= three[code], (year, code)
            assert assembly[code] == 1, (year, code)


# --- A conformacao (T5) ---

CATALOG = CODES | IPE_EXTRA_CODES  # o catalogo dos testes: as nove e as duas dos casos
Edit = Callable[[list[str], list[list[str]]], list[list[str]]]


def conform(
    year: int, codes: set[str] = CATALOG, edit: Edit | None = None
) -> DisclosuresByCompany:
    payload = fixture_zip(f"ipe_{year}")
    if edit is not None:
        payload = edit_member(payload, f"ipe_cia_aberta_{year}.csv", edit)
    return disclosures_from_zip(payload, year, codes)


def by_link(result: DisclosuresByCompany) -> dict[str, ConformedDisclosure]:
    documents = [doc for docs in result.by_company.values() for doc in docs]
    links = {doc.link: doc for doc in documents}
    assert len(links) == len(documents), "link repetido em by_company"
    return links


def set_field(link: str, column: str, value: str) -> Edit:
    """Troca `column` da linha de `link` por `value`; as outras linhas ficam intocadas."""

    def edit(header: list[str], rows: list[list[str]]) -> list[list[str]]:
        at, where = header.index(column), header.index("Link_Download")
        out = [list(row) for row in rows]
        matches = [row for row in out if row[where] == link]
        assert len(matches) == 1, link
        matches[0][at] = value
        return out

    return edit


def duplicate(link: str, column: str | None = None, value: str = "") -> Edit:
    """Repete a linha de `link` logo depois dela; com `column`, a copia leva `value` ali."""

    def edit(header: list[str], rows: list[list[str]]) -> list[list[str]]:
        where = header.index("Link_Download")
        out: list[list[str]] = []
        for row in rows:
            out.append(row)
            if row[where] == link:
                copy = list(row)
                if column is not None:
                    copy[header.index(column)] = value
                out.append(copy)
        assert len(out) == len(rows) + 1, link
        return out

    return edit


def test_rf03_as_tres_categorias_entram_com_o_valor_da_tabela() -> None:
    assert CATEGORIES == {
        "Fato Relevante": "fato_relevante",
        "Comunicado ao Mercado": "comunicado",
        "Aviso aos Acionistas": "aviso_acionistas",
    }
    for year in (2025, 2026):
        raw = rows_by_link(year)
        expected = {
            link
            for link, row in raw.items()
            if row["Categoria"] in THREE and row["Codigo_CVM"] in CATALOG
        }
        documents = by_link(conform(year))
        assert set(documents) == expected, year
        assert {doc.category for doc in documents.values()} == set(CATEGORIES.values())
        for link, doc in documents.items():
            assert doc.category == CATEGORIES[raw[link]["Categoria"]], link


def test_rf03_categorias_de_fora_nao_entram() -> None:
    for year in (2025, 2026):
        raw = rows_by_link(year)
        outside = {link for link, row in raw.items() if row["Categoria"] not in THREE}
        assembly = {link for link in outside if raw[link]["Categoria"] == "Assembleia"}
        assert len(assembly) == len(CODES), year  # a fixture traz uma por companhia
        assert len(outside) > len(assembly), year  # e as de outra categoria de fora
        assert not outside & set(by_link(conform(year))), year


def test_rf03_categoria_igual_sem_strip_nem_caixa() -> None:
    for value in ("fato relevante", " Fato Relevante", "Fato Relevante "):
        edit = set_field(PETROBRAS_FACT, "Categoria", value)
        documents = by_link(conform(2026, edit=edit))
        assert PETROBRAS_FACT not in documents, repr(value)
        assert EMPTY_SUBJECT_NOTICE in documents  # a vizinha da mesma companhia fica


def test_rf03_companhia_fora_de_codes_nao_entra() -> None:
    result = conform(2026)
    assert not set(OUTSIDE) & set(by_link(result))
    assert OUTSIDE_CODE not in result.by_company
    only_nine = conform(2026, codes=set(CODES))
    assert set(only_nine.by_company) == CODES
    assert LONGEST_SUBJECT not in by_link(only_nine)  # 3077 fora de `codes`
    assert EMPTY_SUBJECT_SHAREHOLDERS not in by_link(only_nine)  # 14451 fora


def test_rf03_codigo_normalizado_como_no_m31() -> None:
    edit = set_field(PETROBRAS_FACT, "Codigo_CVM", "009512")
    documents = by_link(conform(2026, edit=edit))
    assert documents[PETROBRAS_FACT].code_cvm == "9512"


def test_rf04_mesmo_protocolo_e_versao_com_dois_links_sao_dois_documentos() -> None:
    petrobras = [
        doc for doc in conform(2025).by_company["9512"] if doc.link in SAME_DELIVERY
    ]
    assert [doc.link for doc in petrobras] == list(SAME_DELIVERY)
    assert len({(doc.protocol, doc.version) for doc in petrobras}) == 1


def test_rf04_campos_conformados_do_fato_relevante_da_petrobras() -> None:
    assert by_link(conform(2026))[PETROBRAS_FACT] == ConformedDisclosure(
        code_cvm="9512",
        cnpj="33000167000101",
        company_name="PETRÓLEO BRASILEIRO S.A. - PETROBRAS",
        year=2026,
        link=PETROBRAS_FACT,
        protocol="009512IPE190920260100853886-76",
        version=1,
        presentation="AP",
        category="fato_relevante",
        kind="",
        species="",
        title="Petrobras informa sobre adesão à nova subvenção econômica",
        reference_date=date(2026, 9, 19),
        delivered_on=date(2026, 9, 19),
    )


def test_rf04_cnpj_com_14_digitos_e_a_reapresentacao_como_re() -> None:
    for year in (2025, 2026):
        for doc in by_link(conform(year)).values():
            assert len(doc.cnpj) == 14 and doc.cnpj.isdigit(), doc.link
    reissued = by_link(conform(2026))[REISSUED]
    assert (reissued.presentation, reissued.version) == ("RE", 2)


def test_rf04_data_de_referencia_vazia_e_nula() -> None:
    edit = set_field(PETROBRAS_FACT, "Data_Referencia", "")
    document = by_link(conform(2026, edit=edit))[PETROBRAS_FACT]
    assert document.reference_date is None
    assert document.delivered_on == date(2026, 9, 19)


def test_rf04b_linha_duplicada_identica_conta_uma() -> None:
    result = conform(2026, edit=duplicate(PETROBRAS_FACT))
    links = [doc.link for doc in result.by_company["9512"]]
    assert links.count(PETROBRAS_FACT) == 1
    assert result.conflicts == {}
    assert set(by_link(result)) == set(by_link(conform(2026)))


def test_rf04b_duplicada_com_assunto_diferente_e_conflito_sem_documento() -> None:
    edit = duplicate(PETROBRAS_FACT, "Assunto", "Outro assunto")
    result = conform(2026, edit=edit)
    assert result.conflicts == {"9512": [PETROBRAS_FACT]}
    documents = by_link(result)
    assert PETROBRAS_FACT not in documents
    assert set(documents) == set(by_link(conform(2026))) - {PETROBRAS_FACT}


def test_rf04b_duplicada_divergente_so_na_data_tambem_e_conflito() -> None:
    edit = duplicate(PETROBRAS_FACT, "Data_Entrega", "2026-09-20")
    result = conform(2026, edit=edit)
    assert result.conflicts == {"9512": [PETROBRAS_FACT]}
    assert PETROBRAS_FACT not in by_link(result)


def test_rf05_titulo_e_o_assunto() -> None:
    subject = rows_by_link(2026)[PETROBRAS_FACT]["Assunto"]
    assert by_link(conform(2026))[PETROBRAS_FACT].title == subject


def test_rf05_assunto_vazio_recua_para_o_tipo() -> None:
    raw = rows_by_link(2026)
    documents = by_link(conform(2026))
    for link in (EMPTY_SUBJECT_NOTICE, EMPTY_SUBJECT_SHAREHOLDERS):
        assert raw[link]["Assunto"] == "" and raw[link]["Tipo"] != ""
        assert documents[link].title == raw[link]["Tipo"].strip(), link
    assert documents[EMPTY_SUBJECT_NOTICE].title == (
        "Aquisição/Alienação de Participação Acionária (art. 12 da Instr. CVM nº 358)"
    )


def test_rf05_assunto_e_tipo_vazios_recuam_para_a_especie() -> None:
    raw = rows_by_link(2026)[EMPTY_SUBJECT_NOTICE]
    assert raw["Especie"] != ""
    edit = set_field(EMPTY_SUBJECT_NOTICE, "Tipo", "")
    documents = by_link(conform(2026, edit=edit))
    assert documents[EMPTY_SUBJECT_NOTICE].title == raw["Especie"]


def test_rf05_os_tres_vazios_recuam_para_a_categoria() -> None:
    def blank(header: list[str], rows: list[list[str]]) -> list[list[str]]:
        for column in ("Tipo", "Especie"):
            rows = set_field(EMPTY_SUBJECT_NOTICE, column, "")(header, rows)
        return rows

    documents = by_link(conform(2026, edit=blank))
    assert documents[EMPTY_SUBJECT_NOTICE].title == "Comunicado ao Mercado"


def test_rf05_so_espaco_conta_como_vazio() -> None:
    row = {"Assunto": "   ", "Tipo": " Tipo ", "Especie": "", "Categoria": "X"}
    assert title_of(row) == "Tipo"
    row = {"Assunto": "", "Tipo": "", "Especie": "\t", "Categoria": "Fato Relevante"}
    assert title_of(row) == "Fato Relevante"


def test_rf05_assunto_de_761_vira_500_com_reticencias() -> None:
    subject = rows_by_link(2026)[LONGEST_SUBJECT]["Assunto"]
    assert len(subject) == 761
    title = by_link(conform(2026))[LONGEST_SUBJECT].title
    assert len(title) == 500
    assert title == subject.strip()[:499] + "…"


def test_rf05_ate_500_fica_inteiro() -> None:
    base = {"Tipo": "", "Especie": "", "Categoria": "Fato Relevante"}
    assert title_of({**base, "Assunto": "x" * 500}) == "x" * 500
    assert title_of({**base, "Assunto": "x" * 501}) == "x" * 499 + "…"


def test_rf06_registro_com_campo_a_mais_e_descartado_e_contado() -> None:
    def extra(header: list[str], rows: list[list[str]]) -> list[list[str]]:
        where = header.index("Link_Download")
        return [[*row, "x"] if row[where] == PETROBRAS_FACT else row for row in rows]

    result = conform(2026, edit=extra)
    assert result.malformed == 1
    assert set(by_link(result)) == set(by_link(conform(2026))) - {PETROBRAS_FACT}
    assert conform(2026).malformed == 0


def test_rf06_registro_com_campo_a_menos_e_descartado_e_contado() -> None:
    def short(header: list[str], rows: list[list[str]]) -> list[list[str]]:
        where = header.index("Link_Download")
        return [row[:-2] if row[where] == PETROBRAS_FACT else row for row in rows]

    result = conform(2026, edit=short)
    assert result.malformed == 1
    assert set(by_link(result)) == set(by_link(conform(2026))) - {PETROBRAS_FACT}


def test_rf06_registro_mal_formado_de_fora_do_catalogo_tambem_conta() -> None:
    def extra(header: list[str], rows: list[list[str]]) -> list[list[str]]:
        where = header.index("Link_Download")
        return [[*row, "x"] if row[where] == OUTSIDE[0] else row for row in rows]

    result = conform(2026, edit=extra)
    assert result.malformed == 1
    assert set(by_link(result)) == set(by_link(conform(2026)))
