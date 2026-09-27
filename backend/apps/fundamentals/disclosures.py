"""A conformacao pura do IPE da CVM: os comunicados de um zip, por companhia (M3.2).

Sem ORM e sem relogio: le o membro `ipe_cia_aberta_<ano>.csv` por `read_rows` e devolve os
documentos das companhias de `codes`. Quem grava em `silver.disclosure` e
`disclosures_importer.py`. As regras:

- RF-03: so as tres categorias de `CATEGORIES`, pela `Categoria` **igual** a chave (sem
  `strip`, sem caixa), e so as companhias de `codes`, pelo `Codigo_CVM` normalizado como no
  M3.1;
- RF-04b: por companhia, linhas de mesmo `Link_Download` iguais em todos os campos contam uma
  vez; com algum campo diferente, o link vai para `conflicts` e **nenhuma** delas entra;
- RF-05: o titulo e o primeiro nao vazio de `Assunto`, `Tipo`, `Especie`, `Categoria`;
- RF-06: registro com numero de campos diferente do cabecalho e contado em `malformed` e
  pulado — de **todas** as companhias do membro, como em `documents.py`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import cast

from apps.fundamentals.documents import normalize_cnpj, normalize_code
from apps.fundamentals.zipdata import read_rows

CATEGORIES: dict[str, str] = {
    "Fato Relevante": "fato_relevante",
    "Comunicado ao Mercado": "comunicado",
    "Aviso aos Acionistas": "aviso_acionistas",
}
TITLE_MAX = 500

# As colunas de onde o titulo sai, na ordem do recuo (RF-05).
TITLE_COLUMNS = ("Assunto", "Tipo", "Especie", "Categoria")


@dataclass(frozen=True)
class ConformedDisclosure:
    code_cvm: str
    cnpj: str
    company_name: str
    year: int
    link: str
    protocol: str
    version: int
    presentation: str
    category: str
    kind: str
    species: str
    title: str
    reference_date: date | None
    delivered_on: date


@dataclass
class DisclosuresByCompany:
    # code_cvm → documentos, sem link repetido
    by_company: dict[str, list[ConformedDisclosure]]
    # registros com número de campos diferente do cabeçalho (RF-06)
    malformed: int
    # code_cvm → links repetidos com campo divergente (RF-04b)
    conflicts: dict[str, list[str]]


def disclosures_from_zip(
    payload: bytes, year: int, codes: set[str]
) -> DisclosuresByCompany:
    """Os comunicados das companhias de `codes` no zip do IPE de `year`.

    `by_company` guarda, por companhia, os documentos na ordem do arquivo, cada link uma
    vez; companhia sem documento aproveitavel nao aparece nele — a que so tem link em
    conflito aparece so em `conflicts`, com os links na ordem em que o conflito surgiu.
    Membro ausente levanta `KeyError`.
    """
    malformed = 0
    # code_cvm → link → a primeira linha lida com aquele link, na ordem do arquivo
    rows_by_company: dict[str, dict[str, dict[str, str]]] = {}
    conflicts: dict[str, list[str]] = {}
    for row in read_rows(payload, f"ipe_cia_aberta_{year}.csv"):
        loose = cast("Mapping[object, object]", row)
        if None in loose or None in loose.values():
            malformed += 1
            continue
        if row["Categoria"] not in CATEGORIES:
            continue
        code = normalize_code(row["Codigo_CVM"])
        if code not in codes:
            continue
        link = row["Link_Download"]
        rows = rows_by_company.setdefault(code, {})
        first = rows.get(link)
        if first is None:
            rows[link] = row
        elif first != row and link not in conflicts.get(code, []):
            conflicts.setdefault(code, []).append(link)

    by_company: dict[str, list[ConformedDisclosure]] = {}
    for code, rows in rows_by_company.items():
        conflicted = set(conflicts.get(code, []))
        documents = [
            _conform(code, year, row)
            for link, row in rows.items()
            if link not in conflicted
        ]
        if documents:
            by_company[code] = documents
    return DisclosuresByCompany(
        by_company=by_company, malformed=malformed, conflicts=conflicts
    )


def title_of(row: Mapping[str, str]) -> str:
    """O titulo do comunicado (RF-05): o primeiro de `TITLE_COLUMNS` nao vazio depois de
    `strip()`; com mais de `TITLE_MAX` caracteres, os 499 primeiros mais `…`."""
    text = ""
    for column in TITLE_COLUMNS:
        text = row[column].strip()
        if text:
            break
    if len(text) > TITLE_MAX:
        return text[: TITLE_MAX - 1] + "…"
    return text


def _conform(code: str, year: int, row: Mapping[str, str]) -> ConformedDisclosure:
    reference = row["Data_Referencia"]
    return ConformedDisclosure(
        code_cvm=code,
        cnpj=normalize_cnpj(row["CNPJ_Companhia"]),
        company_name=row["Nome_Companhia"],
        year=year,
        link=row["Link_Download"],
        protocol=row["Protocolo_Entrega"],
        version=int(row["Versao"]),
        presentation=row["Tipo_Apresentacao"][:2],
        category=CATEGORIES[row["Categoria"]],
        kind=row["Tipo"],
        species=row["Especie"],
        title=title_of(row),
        reference_date=date.fromisoformat(reference) if reference else None,
        delivered_on=date.fromisoformat(row["Data_Entrega"]),
    )
