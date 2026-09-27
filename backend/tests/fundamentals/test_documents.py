"""`documents_from_zip`: a montagem dos documentos de um zip, sobre as fixtures reais.

Os zips alterados sao montados **aqui**, a partir das fixtures, por `edit_member` — e cada
alteracao e declarada no teste que a faz. As fixtures nao sao editadas.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Callable
from datetime import date

from apps.fundamentals.documents import documents_from_zip
from tests.fundamentals.conftest import fixture_zip

# Os nove codigos das fixtures, normalizados como em `silver.asset.code_cvm`.
CODES = {"9512", "4170", "19348", "906", "23159", "24805", "18627", "1228", "24228"}
EOL = "\r\n"  # o fim de linha dos CSVs da CVM

Fields = list[str]


def edit_member(
    payload: bytes,
    member: str,
    edit: Callable[[Fields, list[Fields]], list[Fields]],
) -> bytes:
    """O zip `payload` com o membro `member` reescrito por `edit(cabecalho, linhas)`.

    As linhas chegam partidas em campos por `;` (as fixtures nao tem `;` dentro de campo),
    em latin-1; `edit` devolve as linhas novas. Os outros membros vao sem mudanca.
    """
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(payload)) as source,
        zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        for info in source.infolist():
            data = source.read(info)
            if info.filename == member:
                lines = data.decode("latin-1").split(EOL)
                assert lines[-1] == "", "membro sem fim de linha no fim"
                header = lines[0].split(";")
                rows = [line.split(";") for line in lines[1:-1]]
                new_rows = edit(header, rows)
                text = EOL.join(";".join(row) for row in [header, *new_rows]) + EOL
                data = text.encode("latin-1")
            target.writestr(info, data)
    return out.getvalue()


def test_rf15_capital_se_liga_pelo_cnpj_do_indice() -> None:
    docs = documents_from_zip(fixture_zip("dfp_2024"), "dfp", CODES)

    (petrobras,) = docs["9512"]
    assert petrobras.code_cvm == "9512"
    assert petrobras.cnpj == "33000167000101"
    assert petrobras.reference_date == date(2024, 12, 31)
    # dfp_cia_aberta_composicao_capital_2024.csv, linha 4: a Petrobras, que so tem o CNPJ
    assert [row["QT_ACAO_TOTAL_CAP_INTEGR"] for row in petrobras.capital] == [
        "13044496930"
    ]


def test_rf10_o_indice_guarda_as_tres_versoes_da_vale() -> None:
    docs = documents_from_zip(fixture_zip("dfp_2024"), "dfp", CODES)

    (vale,) = docs["4170"]
    # dfp_cia_aberta_2024.csv, linhas 5, 6 e 7
    assert [(r["VERSAO"], r["DT_RECEB"]) for r in vale.index_rows] == [
        ("1", "2025-02-19"),
        ("2", "2025-02-21"),
        ("3", "2025-03-17"),
    ]
    # as demonstracoes trazem so a versao vigente
    assert {r["VERSAO"] for r in vale.bpa_con + vale.bpp_con + vale.dre_con} == {"3"}


def test_rf07_codigo_fora_de_codes_nao_aparece() -> None:
    docs = documents_from_zip(fixture_zip("dfp_2024"), "dfp", {"9512", "4170"})

    assert set(docs) == {"9512", "4170"}
    todas = [
        row
        for docs_da_companhia in docs.values()
        for doc in docs_da_companhia
        for rows in (doc.index_rows, doc.bpa_con, doc.dre_ind, doc.capital)
        for row in rows
    ]
    assert todas
    assert {row["DENOM_CIA"] for row in todas} == {
        "PETROLEO BRASILEIRO S.A. PETROBRAS",
        "VALE S.A.",
    }


def test_rf07_o_indice_nao_se_mistura_com_as_demonstracoes() -> None:
    """O nome do indice e sufixo de todos os membros; o de BPA nao pode cair no indice."""
    docs = documents_from_zip(fixture_zip("dfp_2024"), "dfp", CODES)

    (petrobras,) = docs["9512"]
    assert len(petrobras.index_rows) == 1
    assert all("CD_CONTA" not in row for row in petrobras.index_rows)
    assert all("DT_RECEB" in row for row in petrobras.index_rows)
    assert all("CD_CONTA" in row for row in petrobras.bpa_con)
    assert {row["CD_CONTA"][0] for row in petrobras.bpa_con + petrobras.bpa_ind} == {
        "1"
    }
    assert {row["CD_CONTA"][0] for row in petrobras.dre_con + petrobras.dre_ind} == {
        "3"
    }


def test_rf10_so_entra_a_linha_do_ultimo_exercicio() -> None:
    docs = documents_from_zip(fixture_zip("dfp_2024"), "dfp", CODES)

    (petrobras,) = docs["9512"]
    # BPA: as linhas `ÚLTIMO` da Petrobras terminam em 2024-12-31; as `PENÚLTIMO`, em 2023
    assert {row["DT_FIM_EXERC"] for row in petrobras.bpa_con} == {"2024-12-31"}
    assert "ORDEM_EXERC" not in petrobras.bpa_con[0]


def test_registro_com_numero_de_campos_errado_e_descartado_e_contado() -> None:
    """Inserido no teste (declarado), no BPA consolidado do DFP 2024: tres registros da
    Petrobras mal formados — um campo a mais, um a menos, e uma aspa sem par no ultimo,
    que engole o resto do membro. Os tres sao descartados e contados; o resto, intacto.
    """
    member = "dfp_cia_aberta_BPA_con_2024.csv"
    original = fixture_zip("dfp_2024")

    def quebra(header: Fields, rows: list[Fields]) -> list[Fields]:
        petrobras = next(row for row in rows if row[4] == "009512")
        a_mais = [*petrobras, "X"]
        a_menos = petrobras[:-1]
        aspa = [*petrobras[:11], '"Ativo Total', *petrobras[12:]]
        return [a_mais, *rows[:3], a_menos, *rows[3:], aspa]

    docs = documents_from_zip(edit_member(original, member, quebra), "dfp", CODES)
    limpo = documents_from_zip(original, "dfp", CODES)

    assert docs.malformed == {member: 3}
    assert limpo.malformed == {}
    assert docs == limpo
