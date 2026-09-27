"""`zipdata`: o hash de conteudo (RF-06) e a leitura de um membro, em latin-1.

Os zips do RF-06 sao montados aqui, no teste, a partir dos mesmos membros: o que muda
entre eles e so a data de cada membro (`ZipInfo.date_time`), que entra nos bytes do zip e
nao no conteudo.
"""

from __future__ import annotations

import hashlib
import io
import zipfile

import pytest

from apps.fundamentals.zipdata import content_sha256, read_rows
from tests.fundamentals.conftest import empty_zip, fixture_zip

MEMBERS = {
    "itr_cia_aberta_2024.csv": b"CD_CVM;DENOM_CIA\r\n009512;PETROLEO\r\n",
    "itr_cia_aberta_DRE_con_2024.csv": b"CD_CVM;VL_CONTA\r\n009512;1.0\r\n",
}


def build_zip(
    members: dict[str, bytes], date_time: tuple[int, int, int, int, int, int]
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(zipfile.ZipInfo(name, date_time=date_time), data)
    return buffer.getvalue()


def test_rf06_datas_de_membro_diferentes_mudam_o_zip_e_nao_o_conteudo() -> None:
    primeiro = build_zip(MEMBERS, (2026, 9, 20, 10, 0, 0))
    segundo = build_zip(MEMBERS, (2026, 9, 27, 11, 30, 0))

    assert hashlib.sha256(primeiro).digest() != hashlib.sha256(segundo).digest()
    assert content_sha256(primeiro) == content_sha256(segundo)


def test_rf06_o_hash_nao_depende_da_ordem_dos_membros_no_zip() -> None:
    invertido = dict(reversed(list(MEMBERS.items())))

    assert content_sha256(build_zip(invertido, (2026, 9, 20, 10, 0, 0))) == (
        content_sha256(build_zip(MEMBERS, (2026, 9, 20, 10, 0, 0)))
    )


def test_rf06_um_byte_mudado_num_membro_muda_o_hash() -> None:
    alterado = dict(MEMBERS)
    alterado["itr_cia_aberta_DRE_con_2024.csv"] = b"CD_CVM;VL_CONTA\r\n009512;2.0\r\n"
    data = (2026, 9, 20, 10, 0, 0)

    assert content_sha256(build_zip(alterado, data)) != (
        content_sha256(build_zip(MEMBERS, data))
    )


def test_rf06_o_nome_do_membro_entra_no_hash() -> None:
    renomeado = {
        "itr_cia_aberta_2024.csv": MEMBERS["itr_cia_aberta_2024.csv"],
        "itr_cia_aberta_DRE_ind_2024.csv": MEMBERS["itr_cia_aberta_DRE_con_2024.csv"],
    }
    data = (2026, 9, 20, 10, 0, 0)

    assert content_sha256(build_zip(renomeado, data)) != (
        content_sha256(build_zip(MEMBERS, data))
    )


def test_rf06_segue_a_formula_da_spec() -> None:
    esperado = hashlib.sha256()
    for name in sorted(MEMBERS):
        esperado.update(name.encode("utf-8") + b"\0" + MEMBERS[name])

    assert content_sha256(build_zip(MEMBERS, (2026, 9, 20, 10, 0, 0))) == (
        esperado.hexdigest()
    )


def test_rf06_corpo_que_nao_e_zip_levanta_badzipfile() -> None:
    with pytest.raises(zipfile.BadZipFile):
        content_sha256(b"<html>manutencao</html>")


def test_rf06_read_rows_le_a_petrobras_em_latin1() -> None:
    linhas = [
        row
        for row in read_rows(fixture_zip("itr_2024"), "itr_cia_aberta_BPP_con_2024.csv")
        if row["CD_CVM"] == "009512" and row["CD_CONTA"] == "2.03"
    ]

    assert linhas, "a Petrobras sumiu do BPP consolidado do itr_2024.zip"
    assert {row["DS_CONTA"] for row in linhas} == {"Patrimônio Líquido Consolidado"}
    assert {row["ORDEM_EXERC"] for row in linhas} <= {"ÚLTIMO", "PENÚLTIMO"}


def test_rf06_read_rows_abre_o_membro_de_nome_exato() -> None:
    payload = fixture_zip("itr_2024")

    indice = list(read_rows(payload, "itr_cia_aberta_2024.csv"))

    assert indice
    assert set(indice[0]) == {
        "CNPJ_CIA",
        "DT_REFER",
        "VERSAO",
        "DENOM_CIA",
        "CD_CVM",
        "CATEG_DOC",
        "ID_DOC",
        "DT_RECEB",
        "LINK_DOC",
    }
    with pytest.raises(KeyError):
        list(read_rows(payload, "cia_aberta_2024.csv"))


def test_rf06_zip_vazio_de_companhias_tem_os_membros_e_so_cabecalho() -> None:
    antes = zipfile.ZipFile(io.BytesIO(empty_zip("dfp", 2019)))
    depois = zipfile.ZipFile(io.BytesIO(empty_zip("itr", 2021)))

    tipos = ("", "BPA_con_", "BPA_ind_", "BPP_con_", "BPP_ind_", "DRE_con_", "DRE_ind_")
    assert sorted(antes.namelist()) == sorted(
        f"dfp_cia_aberta_{tipo}2019.csv" for tipo in tipos
    )
    assert "itr_cia_aberta_composicao_capital_2021.csv" in depois.namelist()
    assert len(depois.namelist()) == 8
    assert (
        list(read_rows(empty_zip("itr", 2021), "itr_cia_aberta_DRE_con_2021.csv")) == []
    )
