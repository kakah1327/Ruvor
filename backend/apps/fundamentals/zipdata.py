"""Leitura dos zips da CVM: o hash de conteudo e as linhas de um membro, em fluxo.

Puro — sem ORM, sem regra de negocio. Nao sabe o que e companhia, versao ou conta: le
bytes e devolve texto. A conformacao e de `conform.py`.
"""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from collections.abc import Iterator


def content_sha256(payload: bytes) -> str:
    """SHA-256 do conteudo do zip, nao dos bytes dele (RF-06).

    Para cada membro, em ordem de nome: o nome em UTF-8, um byte nulo e os bytes do
    membro. Zip regerado com o mesmo conteudo e outras datas de membro da o mesmo hash.
    Corpo que nao e zip levanta `zipfile.BadZipFile`.
    """
    digest = hashlib.sha256()
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        for name in sorted(zf.namelist()):
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(zf.read(name))
    return digest.hexdigest()


def read_rows(payload: bytes, member_name: str) -> Iterator[dict[str, str]]:
    """As linhas do membro de nome **exato** `member_name`, uma a uma.

    Latin-1, separador `;`, cabecalho na primeira linha. O nome e exato porque o indice
    (`itr_cia_aberta_2024.csv`) e sufixo de todos os outros membros. Membro ausente
    levanta `KeyError`, na primeira iteracao.
    """
    with (
        zipfile.ZipFile(io.BytesIO(payload)) as zf,
        zf.open(member_name) as raw,
        io.TextIOWrapper(raw, encoding="latin-1", newline="") as text,
    ):
        yield from csv.DictReader(text, delimiter=";")
