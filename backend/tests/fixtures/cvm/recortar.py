"""Gera as fixtures de `tests/fixtures/cvm/` a partir dos zips reais da CVM.

Roda **a mao, com rede** — nunca na suite: o nome nao comeca por `test_`, e a guarda
`sem_rede` recusaria o download. De `backend/`:

    python -m tests.fixtures.cvm.recortar <diretorio de trabalho>

O diretorio de trabalho fica **fora** do repositorio: recebe os zips originais (ate
~33 MB cada), que nao se versionam, e um `.last-modified` ao lado de cada um. Um zip ja
baixado nao se baixa de novo.

Para cada zip de origem, grava um zip novo com **todos** os membros de mesmo nome e mesma
data, cada um com o cabecalho e so as linhas das companhias do recorte — pelo `CD_CVM`, ou
pelo `CNPJ_CIA` nos membros que nao o tem (`composicao_capital` e `parecer`). Os bytes das
linhas sao copiados sem decodificar e recodificar: o latin-1 e o fim de linha ficam como
vieram. Imprime, por fixture, o que o `README.md` da pasta copia.
"""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from apps.fundamentals.cvm import CvmClient, cvm_url
from apps.fundamentals.zipdata import content_sha256

OUT_DIR = Path(__file__).resolve().parent

PETROBRAS = "009512"
VALE = "004170"
ITAU = "019348"
BRADESCO = "000906"
BB_SEGURIDADE = "023159"
VIVARA = "024805"
SANEPAR = "018627"
BNB = "001228"
CAMIL = "024228"
NINE = frozenset(
    {PETROBRAS, VALE, ITAU, BRADESCO, BB_SEGURIDADE, VIVARA, SANEPAR, BNB, CAMIL}
)


@dataclass(frozen=True)
class Cut:
    kind: str
    year: int
    codes: frozenset[str]

    @property
    def name(self) -> str:
        return f"{self.kind}_{self.year}.zip"


CUTS = (
    Cut("itr", 2016, frozenset({BB_SEGURIDADE})),
    Cut("itr", 2019, frozenset({PETROBRAS})),
    Cut("itr", 2024, NINE),
    Cut("dfp", 2024, NINE),
    Cut("itr", 2025, frozenset({PETROBRAS})),
    Cut("dfp", 2025, frozenset({CAMIL})),
)


def download(cut: Cut, work_dir: Path) -> tuple[bytes, str, str]:
    """O zip original, o `Last-Modified` e a data do download; do cache, se houver."""
    original = work_dir / f"{cut.kind}_cia_aberta_{cut.year}.zip"
    sidecar = work_dir / f"{cut.kind}_cia_aberta_{cut.year}.last-modified"
    if original.exists() and sidecar.exists():
        last_modified, downloaded = sidecar.read_text(encoding="utf-8").splitlines()
        return original.read_bytes(), last_modified, downloaded
    response = CvmClient().get(cut.kind, cut.year)
    if response.http_status != 200 or response.payload is None:
        raise SystemExit(f"{response.url}: HTTP {response.http_status}")
    downloaded = date.today().isoformat()
    original.write_bytes(response.payload)
    with sidecar.open("w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(f"{response.last_modified}\n{downloaded}\n")
    return response.payload, str(response.last_modified), downloaded


def records(data: bytes) -> Iterator[tuple[bytes, list[str]]]:
    """Cada registro do CSV: os bytes das linhas fisicas que ele ocupa, e os campos.

    O registro e o que o `csv` do Python le — o mesmo leitor da `zipdata.read_rows` —,
    e nao a linha fisica: o `parecer` tem texto entre aspas com quebra de linha. O leitor
    recebe uma linha fisica por vez, e as consumidas ate ele devolver o registro sao os
    bytes dele. As linhas se separam nos bytes, que so quebram em `\\r` e `\\n`; o
    `str.splitlines` quebraria tambem no `\\x85` do latin-1.
    """
    consumed: list[bytes] = []

    def feed() -> Iterator[str]:
        for line in data.splitlines(keepends=True):
            consumed.append(line)
            yield line.decode("latin-1")

    for row in csv.reader(feed(), delimiter=";"):
        yield b"".join(consumed), row
        consumed.clear()


def cut_member(
    data: bytes, keys: frozenset[str], cnpjs: frozenset[str]
) -> tuple[bytes, int, int]:
    """Cabecalho e os registros do recorte, pelo `CD_CVM` ou, sem ele, pelo `CNPJ_CIA`.

    Devolve tambem quantos registros ficaram e quantos da origem tem numero de campos
    diferente do cabecalho (aspas desbalanceadas na fonte). Um desses que toque uma
    companhia do recorte, em qualquer das linhas fisicas, interrompe: a fixture nao
    pode perder linha real do recorte em silencio.
    """
    rows = records(data)
    header, columns = next(rows)
    if "CD_CVM" in columns:
        position, wanted = columns.index("CD_CVM"), keys
        marks = [f";{key};".encode("latin-1") for key in keys]
    else:
        position, wanted = columns.index("CNPJ_CIA"), cnpjs
        marks = [cnpj.encode("latin-1") for cnpj in cnpjs]
    kept = [header]
    malformed = 0
    for raw, values in rows:
        if len(values) != len(columns):
            malformed += 1
            if any(mark in raw for mark in marks):
                raise SystemExit(
                    f"registro com {len(values)} campos, esperava {len(columns)}, "
                    f"toca o recorte: {raw[:200]!r}"
                )
            continue
        if values[position] in wanted:
            kept.append(raw)
    return b"".join(kept), len(kept) - 1, malformed


def main(work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    for cut in CUTS:
        payload, last_modified, downloaded = download(cut, work_dir)
        index_name = f"{cut.kind}_cia_aberta_{cut.year}.csv"
        report: list[str] = []
        with zipfile.ZipFile(io.BytesIO(payload)) as source:
            names: dict[str, str] = {}
            cnpjs: set[str] = set()
            index_rows = records(source.read(index_name))
            _, index_columns = next(index_rows)
            for _, row in index_rows:
                values = dict(zip(index_columns, row, strict=True))
                if values["CD_CVM"] in cut.codes:
                    names[values["CD_CVM"]] = values["DENOM_CIA"]
                    cnpjs.add(values["CNPJ_CIA"])
            missing = cut.codes - names.keys()
            if missing:
                raise SystemExit(f"{index_name}: sem {sorted(missing)}")
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
                for info in source.infolist():
                    data, kept, malformed = cut_member(
                        source.read(info.filename), cut.codes, frozenset(cnpjs)
                    )
                    member = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                    member.compress_type = zipfile.ZIP_DEFLATED
                    target.writestr(member, data)
                    report.append(
                        f"    {info.filename}: {kept} linhas"
                        + (f", {malformed} mal formadas na origem" if malformed else "")
                    )
        (OUT_DIR / cut.name).write_bytes(buffer.getvalue())
        print(f"{cut.name}")
        print(f"  url: {cvm_url(cut.kind, cut.year)}")
        print(f"  baixado em: {downloaded}")
        print(f"  last-modified: {last_modified}")
        print(f"  content_sha256 do original: {content_sha256(payload)}")
        print(
            f"  bytes do original: {len(payload)}; da fixture: {len(buffer.getvalue())}"
        )
        for code in sorted(names):
            print(f"  {code} {names[code]}")
        print("\n".join(report))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m tests.fixtures.cvm.recortar <diretorio>")
    main(Path(sys.argv[1]))
