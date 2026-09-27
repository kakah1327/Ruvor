"""Infraestrutura comum dos testes de `apps.fundamentals`: fixtures e a fonte falsa.

`fixture_zip`, `empty_zip` e `serve_range` sao funcoes comuns, nao fixtures do pytest, e se
importam por `from tests.fundamentals.conftest import ...`.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path

from django.utils import timezone

from apps.fundamentals.cvm import KINDS, CvmDownload, CvmHead, cvm_url

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "cvm"
FIRST_YEAR = 2016  # RF-03: o intervalo vai de 2016 ao ano corrente
FIRST_YEAR_WITH_CAPITAL = 2020  # `composicao_capital` so existe de 2020 em diante

# Os membros obrigatorios, pelo tipo: o indice (sufixo vazio) e BPA, BPP e DRE nos dois
# escopos. O nome do membro e `{kind}_cia_aberta_{tipo}{ano}.csv`.
REQUIRED_MEMBERS = (
    "",
    "BPA_con_",
    "BPA_ind_",
    "BPP_con_",
    "BPP_ind_",
    "DRE_con_",
    "DRE_ind_",
)
CAPITAL_MEMBER = "composicao_capital_"


def fixture_zip(nome: str) -> bytes:
    """Le `tests/fixtures/cvm/<nome>.zip`; `nome` vem com ou sem a extensao."""
    arquivo = nome if nome.endswith(".zip") else f"{nome}.zip"
    return (FIXTURES_DIR / arquivo).read_bytes()


def empty_zip(kind: str, year: int) -> bytes:
    """Zip valido e vazio de companhias para (`kind`, `year`).

    Os sete membros obrigatorios, e `composicao_capital` a partir de 2020, so com o
    cabecalho — copiado, em bytes, do membro de mesmo tipo do `itr_2024.zip`.
    """
    members = list(REQUIRED_MEMBERS)
    if year >= FIRST_YEAR_WITH_CAPITAL:
        members.append(CAPITAL_MEMBER)
    buffer = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(fixture_zip("itr_2024"))) as source,
        zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        for member in members:
            data = source.read(f"itr_cia_aberta_{member}2024.csv")
            header = data[: data.index(b"\n") + 1]
            target.writestr(f"{kind}_cia_aberta_{member}{year}.csv", header)
    return buffer.getvalue()


class FakeCvm:
    """Fonte de zips alimentada por cenario, no lugar do `CvmClient`.

    Satisfaz estruturalmente a interface `CvmSource` (`head` e `get`). `heads` e `gets`
    mapeiam (tipo, ano) a uma lista consumida em ordem: cada item e a resposta a devolver
    ou uma excecao a levantar. `calls` registra `("head" | "get", tipo, ano)` de cada
    pedido, na ordem, **antes** de qualquer verificacao — uma chamada indevida aparece ali
    mesmo que algo engula o erro. Chave ausente ou lista esgotada e cenario mal montado, e
    levanta `AssertionError`.
    """

    def __init__(
        self,
        heads: dict[tuple[str, int], list[CvmHead | Exception]],
        gets: dict[tuple[str, int], list[CvmDownload | Exception]],
    ) -> None:
        self.heads = {key: list(items) for key, items in heads.items()}
        self.gets = {key: list(items) for key, items in gets.items()}
        self.calls: list[tuple[str, str, int]] = []

    def head(self, kind: str, year: int) -> CvmHead:
        self.calls.append(("head", kind, year))
        assert (kind, year) in self.heads, (
            f"cenario mal montado: ({kind}, {year}) nao tem resposta em FakeCvm.heads"
        )
        assert self.heads[(kind, year)], (
            f"cenario mal montado: os HEAD de ({kind}, {year}) em FakeCvm se esgotaram"
        )
        response = self.heads[(kind, year)].pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def get(self, kind: str, year: int) -> CvmDownload:
        self.calls.append(("get", kind, year))
        assert (kind, year) in self.gets, (
            f"cenario mal montado: ({kind}, {year}) nao tem resposta em FakeCvm.gets"
        )
        assert self.gets[(kind, year)], (
            f"cenario mal montado: os GET de ({kind}, {year}) em FakeCvm se esgotaram"
        )
        response = self.gets[(kind, year)].pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def serve_range(
    fake: FakeCvm,
    now: datetime,
    fixtures: dict[tuple[str, int], bytes],
    generation: int = 1,
) -> None:
    """Acrescenta a `fake` as respostas de uma coleta inteira, de 2016 ao ano de `now`.

    Para cada (tipo, ano) do intervalo, um `HEAD` e um `GET` com status 200: o zip de
    `fixtures`, se houver, senao `empty_zip`. O `Last-Modified` e
    `gen-{generation}-{tipo}-{ano}`: o mesmo `generation` repete o cabecalho (a coleta
    seguinte sai `nao modificado`); outro o muda. O ano corrente e o de `now` no fuso do
    projeto.
    """
    last_year = timezone.localdate(now).year
    for year in range(FIRST_YEAR, last_year + 1):
        for kind in KINDS:
            payload = fixtures.get((kind, year))
            if payload is None:
                payload = empty_zip(kind, year)
            last_modified = f"gen-{generation}-{kind}-{year}"
            fake.heads.setdefault((kind, year), []).append(CvmHead(200, last_modified))
            fake.gets.setdefault((kind, year), []).append(
                CvmDownload(200, last_modified, cvm_url(kind, year), payload)
            )
