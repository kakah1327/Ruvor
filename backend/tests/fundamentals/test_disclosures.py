"""A conformacao pura do IPE (M3.2) e as fixtures `ipe_2025.zip` e `ipe_2026.zip`.

Os testes `test_fixtures_*` conferem que cada caso que o `README.md` de
`tests/fixtures/cvm/` registra esta no zip, pelo link que o `recortar.py` imprimiu.
"""

from __future__ import annotations

from collections import Counter

from tests.fundamentals.conftest import (
    CODES,
    IPE_EXTRA_CODES,
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
