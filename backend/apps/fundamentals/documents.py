"""Montagem dos documentos de um zip da CVM: as linhas de cada (companhia, `DT_REFER`).

E o unico lugar que le as demonstracoes de um zip para a conformacao: os testes da
conformacao e o importer passam por `documents_from_zip`. Le o indice, as seis
demonstracoes (BPA, BPP e DRE, `_con` e `_ind`) e a `composicao_capital`, cada membro uma
vez, em fluxo, e **ja na leitura** descarta:

- linha de companhia fora de `codes` (RF-07) — sem isso, o ITR inteiro nao cabe na memoria;
- linha de demonstracao que nao e `ORDEM_EXERC = ULTIMO` (RF-10). O filtro mora so aqui;
- as colunas que a conformacao nao usa;
- registro cujo numero de campos difere do cabecalho — CSV mal formado na origem (aspas
  desbalanceadas, campo a mais ou a menos). Nunca e aceito em silencio: e contado, por
  membro, em `DocumentsByCompany.malformed`, para o importer relatar.

`composicao_capital` nao tem `CD_CVM`: liga-se a companhia pelo CNPJ **do indice**, so
digitos.
"""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal, cast

from apps.fundamentals.zipdata import read_rows

# As colunas guardadas. Nas demonstracoes, todas menos `GRUPO_DFP`, `MOEDA` (sempre
# `REAL`) e `ORDEM_EXERC` (ja filtrada); BPA e BPP nao tem `DT_INI_EXERC`.
STATEMENT_COLUMNS = (
    "CD_CVM",
    "CNPJ_CIA",
    "DENOM_CIA",
    "DT_REFER",
    "VERSAO",
    "ESCALA_MOEDA",
    "DT_INI_EXERC",
    "DT_FIM_EXERC",
    "CD_CONTA",
    "DS_CONTA",
    "VL_CONTA",
    "ST_CONTA_FIXA",
)
INDEX_COLUMNS = ("CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM", "DT_RECEB")
CAPITAL_COLUMNS = (
    "CNPJ_CIA",
    "DT_REFER",
    "VERSAO",
    "DENOM_CIA",
    "QT_ACAO_ORDIN_CAP_INTEGR",
    "QT_ACAO_PREF_CAP_INTEGR",
    "QT_ACAO_TOTAL_CAP_INTEGR",
    "QT_ACAO_ORDIN_TESOURO",
    "QT_ACAO_PREF_TESOURO",
    "QT_ACAO_TOTAL_TESOURO",
)

# O campo de `DocumentRows` e o tipo da demonstracao no nome do membro.
STATEMENTS = (
    ("bpa_con", "BPA_con"),
    ("bpp_con", "BPP_con"),
    ("dre_con", "DRE_con"),
    ("bpa_ind", "BPA_ind"),
    ("bpp_ind", "BPP_ind"),
    ("dre_ind", "DRE_ind"),
)
CURRENT_PERIOD = "ÚLTIMO"


@dataclass(frozen=True)
class DocumentRows:
    """As linhas de um documento: uma companhia, um `DT_REFER`, um zip."""

    code_cvm: str  # normalizado: str(int(CD_CVM))
    cnpj: str  # do indice, so digitos
    reference_date: date
    kind: Literal["itr", "dfp"]
    index_rows: list[dict[str, str]]  # linhas do indice desta companhia e DT_REFER
    bpa_con: list[dict[str, str]]
    bpp_con: list[dict[str, str]]
    dre_con: list[dict[str, str]]
    bpa_ind: list[dict[str, str]]
    bpp_ind: list[dict[str, str]]
    dre_ind: list[dict[str, str]]
    capital: list[
        dict[str, str]
    ]  # composicao_capital desta companhia (por CNPJ) e DT_REFER


class DocumentsByCompany(dict[str, list[DocumentRows]]):
    """`code_cvm` normalizado → documentos da companhia, por `reference_date` crescente.

    `malformed` conta, por nome de membro, os registros descartados por terem numero de
    campos diferente do cabecalho — de **todas** as companhias do membro, nao so das de
    `codes`: um registro quebrado pode ter engolido linhas de qualquer uma. So membros com
    descarte aparecem.
    """

    malformed: dict[str, int]

    def __init__(self) -> None:
        super().__init__()
        self.malformed = {}


def normalize_code(code_cvm: str) -> str:
    """`CD_CVM` sem zeros a esquerda, o formato de `silver.asset.code_cvm`."""
    return str(int(code_cvm))


def normalize_cnpj(cnpj: str) -> str:
    """CNPJ so com digitos, o formato de `silver.asset.cnpj`."""
    return re.sub(r"\D", "", cnpj)


def documents_from_zip(
    payload: bytes, kind: Literal["itr", "dfp"], codes: set[str]
) -> DocumentsByCompany:
    """Os documentos das companhias de `codes` no zip `payload`, do tipo `kind`.

    Membro obrigatorio ausente (o indice ou uma das seis demonstracoes) levanta
    `KeyError`; `composicao_capital` e opcional (nao existe antes de 2020).
    """
    result = DocumentsByCompany()
    names = _member_names(payload, kind)

    # O indice primeiro: e dele o CNPJ que liga a `composicao_capital`.
    index: dict[tuple[str, str], list[dict[str, str]]] = {}
    cnpj_by_code: dict[str, str] = {}
    for row in _rows(payload, names["index"], result.malformed):
        code = normalize_code(row["CD_CVM"])
        if code not in codes:
            continue
        index.setdefault((code, row["DT_REFER"]), []).append(_keep(row, INDEX_COLUMNS))
        cnpj_by_code.setdefault(code, normalize_cnpj(row["CNPJ_CIA"]))

    statements: dict[tuple[str, str], dict[str, list[dict[str, str]]]] = {}
    for field, statement in STATEMENTS:
        for row in _rows(payload, names[statement], result.malformed):
            if row["ORDEM_EXERC"] != CURRENT_PERIOD:
                continue
            code = normalize_code(row["CD_CVM"])
            if code not in codes:
                continue
            by_field = statements.setdefault((code, row["DT_REFER"]), {})
            by_field.setdefault(field, []).append(_keep(row, STATEMENT_COLUMNS))

    capital: dict[tuple[str, str], list[dict[str, str]]] = {}
    if "capital" in names:
        code_by_cnpj = {cnpj: code for code, cnpj in cnpj_by_code.items()}
        for row in _rows(payload, names["capital"], result.malformed):
            capital_code = code_by_cnpj.get(normalize_cnpj(row["CNPJ_CIA"]))
            if capital_code is None:
                continue
            capital.setdefault((capital_code, row["DT_REFER"]), []).append(
                _keep(row, CAPITAL_COLUMNS)
            )

    for code, reference in sorted(set(index) | set(statements)):
        by_field = statements.get((code, reference), {})
        cnpj = cnpj_by_code.get(code)
        if cnpj is None:  # sem linha no indice: o CNPJ da propria demonstracao
            first = next(rows[0] for rows in by_field.values())
            cnpj = normalize_cnpj(first["CNPJ_CIA"])
        result.setdefault(code, []).append(
            DocumentRows(
                code_cvm=code,
                cnpj=cnpj,
                reference_date=date.fromisoformat(reference),
                kind=kind,
                index_rows=index.get((code, reference), []),
                bpa_con=by_field.get("bpa_con", []),
                bpp_con=by_field.get("bpp_con", []),
                dre_con=by_field.get("dre_con", []),
                bpa_ind=by_field.get("bpa_ind", []),
                bpp_ind=by_field.get("bpp_ind", []),
                dre_ind=by_field.get("dre_ind", []),
                capital=capital.get((code, reference), []),
            )
        )
    return result


def _member_names(payload: bytes, kind: str) -> dict[str, str]:
    """Os nomes exatos dos membros, pelo ano do indice (`<kind>_cia_aberta_<ano>.csv`)."""
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        members = set(zf.namelist())
    pattern = re.compile(rf"{kind}_cia_aberta_(\d{{4}})\.csv")
    years = sorted(m.group(1) for name in members if (m := pattern.fullmatch(name)))
    if len(years) != 1:
        raise KeyError(f"indice {kind}_cia_aberta_<ano>.csv: {len(years)} no zip")
    year = years[0]
    names = {"index": f"{kind}_cia_aberta_{year}.csv"}
    for _, statement in STATEMENTS:
        names[statement] = f"{kind}_cia_aberta_{statement}_{year}.csv"
    capital = f"{kind}_cia_aberta_composicao_capital_{year}.csv"
    if capital in members:
        names["capital"] = capital
    return names


def _rows(
    payload: bytes, member: str, malformed: dict[str, int]
) -> Iterator[dict[str, str]]:
    """As linhas bem formadas de `member`; as outras, contadas em `malformed[member]`.

    O `DictReader` poe campo a mais sob a chave `None` e completa campo a menos com o
    valor `None`: qualquer dos dois e registro com numero de campos diferente do
    cabecalho.
    """
    for row in read_rows(payload, member):
        loose = cast("Mapping[object, object]", row)
        if None in loose or None in loose.values():
            malformed[member] = malformed.get(member, 0) + 1
            continue
        yield row


def _keep(row: dict[str, str], columns: tuple[str, ...]) -> dict[str, str]:
    return {column: row[column] for column in columns if column in row}
