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

O IPE (M3.2) tem modo proprio, que grava **so** `ipe_2025.zip` e `ipe_2026.zip`:

    python -m tests.fixtures.cvm.recortar <diretorio de trabalho> --only ipe

Sem `--only`, grava as seis fixtures de ITR e DFP, como antes: a CVM regera os zips dos
anos recentes, e regera-las junto mudaria as fixtures do M3.1. O recorte do IPE e **por
registro**, nao por companhia (uma companhia grande tem centenas de linhas por ano): as
linhas saem de regras fixas, em `ipe_cases`, e cada caso imprime o `Codigo_CVM` e o link.
Um caso le o catalogo (`silver.asset`) do banco configurado, por isso o modo IPE roda no
`worker`, com o banco de pe e o catalogo importado.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from apps.fundamentals.cvm import IPE, CvmClient, cvm_url
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


# --- IPE (M3.2) ---------------------------------------------------------------------

IPE_YEARS = (2025, 2026)
# As tres categorias que o M3.2 conforma (RF-03), na ordem do rodizio de `nine_rows`.
THREE = ("Fato Relevante", "Comunicado ao Mercado", "Aviso aos Acionistas")
ASSEMBLY = "Assembleia"  # a categoria de fora mais frequente (6.762 linhas em 2026)
PER_COMPANY = 5  # linhas das tres categorias, por companhia e por ano
PETROBRAS_FACT_DATE = "2026-09-19"  # o fato relevante da V-06
LONGEST_SUBJECT = 761  # o maior `Assunto` das tres categorias em 2026, pela spec
FIELDS = 13  # colunas do IPE


def ipe_code(code: str) -> str:
    """O `Codigo_CVM` do IPE vem sem zeros a esquerda; o `CD_CVM` do ITR, com seis."""
    return str(int(code))


NINE_IPE = frozenset(ipe_code(code) for code in NINE)


@dataclass(frozen=True)
class IpeRow:
    """Um registro do IPE: a posicao no arquivo, os bytes e os campos pelo cabecalho."""

    index: int
    raw: bytes
    values: dict[str, str]

    @property
    def code(self) -> str:
        return self.values["Codigo_CVM"]

    @property
    def category(self) -> str:
        return self.values["Categoria"]

    @property
    def link(self) -> str:
        return self.values["Link_Download"]


@dataclass(frozen=True)
class IpeCase:
    """Um caso do recorte: o motivo e as linhas que ele poe na fixture."""

    reason: str
    rows: tuple[IpeRow, ...]


def ipe_rows(data: bytes) -> tuple[bytes, list[IpeRow], int]:
    """O cabecalho, os registros bem formados e quantos vieram mal formados."""
    rows = records(data)
    header, columns = next(rows)
    kept: list[IpeRow] = []
    malformed = 0
    for index, (raw, values) in enumerate(rows):
        if len(values) != len(columns):
            malformed += 1
            continue
        kept.append(IpeRow(index, raw, dict(zip(columns, values, strict=True))))
    return header, kept, malformed


def catalog_codes() -> frozenset[str]:
    """Os `code_cvm` do catalogo, como `apps.fundamentals.importer._catalog` os le."""
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    from apps.assets.models import Asset

    codes = Asset.objects.filter(kind=Asset.Kind.STOCK).values_list(
        "code_cvm", flat=True
    )
    catalog = frozenset(code for code in codes if code)
    if not catalog:
        raise SystemExit("silver.asset sem companhias: importe o catalogo antes")
    return catalog


def only(rows: list[IpeRow], what: str, count: int = 1) -> tuple[IpeRow, ...]:
    """Exatamente `count` linhas; outra quantidade interrompe (a fonte mudou)."""
    if len(rows) != count:
        raise SystemExit(f"{what}: {len(rows)} linhas, esperava {count}")
    return tuple(rows)


def nine_rows(rows: list[IpeRow], code: str) -> tuple[IpeRow, ...]:
    """Ate `PER_COMPANY` linhas das tres categorias, em rodizio entre elas e na ordem do
    arquivo; a primeira de `Assembleia`; e a primeira de outra categoria de fora."""
    mine = [row for row in rows if row.code == code]
    queues = [[row for row in mine if row.category == category] for category in THREE]
    chosen: list[IpeRow] = []
    while len(chosen) < PER_COMPANY and any(queues):
        for queue in queues:
            if queue and len(chosen) < PER_COMPANY:
                chosen.append(queue.pop(0))
    assembly = [row for row in mine if row.category == ASSEMBLY]
    other = [row for row in mine if row.category not in (*THREE, ASSEMBLY)]
    return tuple(chosen + assembly[:1] + other[:1])


def ipe_cases(year: int, rows: list[IpeRow], catalog: frozenset[str]) -> list[IpeCase]:
    """As regras do recorte. Toda regra que pede uma linha so e da fonte, nunca de memoria."""
    three = [row for row in rows if row.category in THREE]
    cases = [
        IpeCase(f"{code}: as tres categorias, Assembleia e outra de fora", picked)
        for code in sorted(NINE_IPE, key=int)
        if (picked := nine_rows(rows, code))
    ]
    if year == 2025:
        pairs: dict[tuple[str, str], list[IpeRow]] = {}
        for row in three:
            if row.code in NINE_IPE:
                key = (row.values["Protocolo_Entrega"], row.values["Versao"])
                pairs.setdefault(key, []).append(row)
        repeated = [group for group in pairs.values() if len(group) > 1]
        if not repeated:
            raise SystemExit(
                "2025: nenhum (Protocolo_Entrega, Versao) repetido nas nove"
            )
        cases.append(
            IpeCase(
                "(Protocolo_Entrega, Versao) com dois links (RF-04)",
                only(repeated[0], "o primeiro (protocolo, versao) repetido", 2),
            )
        )
    if year == 2026:
        cases.append(
            IpeCase(
                "fato relevante da Petrobras de 2026-09-19 (V-06)",
                only(
                    [
                        row
                        for row in three
                        if row.code == "9512"
                        and row.category == "Fato Relevante"
                        and row.values["Data_Entrega"] == PETROBRAS_FACT_DATE
                    ],
                    "fato relevante da Petrobras",
                ),
            )
        )
        for category in ("Comunicado ao Mercado", "Aviso aos Acionistas"):
            empty = [
                row
                for row in three
                if row.category == category and row.values["Assunto"] == ""
            ]
            # uma das nove, se houver; senao, a primeira do catalogo
            pick = [row for row in empty if row.code in NINE_IPE] or [
                row for row in empty if row.code in catalog
            ]
            if not pick:
                raise SystemExit(f"2026: nenhum {category} com Assunto vazio")
            cases.append(IpeCase(f"Assunto vazio em {category} (RF-05)", (pick[0],)))
        longest = max(three, key=lambda row: len(row.values["Assunto"]))
        if len(longest.values["Assunto"]) != LONGEST_SUBJECT:
            raise SystemExit(
                f"2026: o maior Assunto tem {len(longest.values['Assunto'])} caracteres"
            )
        cases.append(
            IpeCase(f"Assunto de {LONGEST_SUBJECT} caracteres (RF-05)", (longest,))
        )
        reissued = [
            row
            for row in three
            if row.code in NINE_IPE
            and row.values["Tipo_Apresentacao"].startswith("RE")
            and int(row.values["Versao"]) > 1
        ]
        if not reissued:
            raise SystemExit("2026: nenhuma reapresentacao RE nas nove")
        cases.append(IpeCase("reapresentacao RE, Versao > 1", (reissued[0],)))
        outside = [row for row in three if row.code not in catalog | NINE_IPE]
        if not outside:
            raise SystemExit("2026: nenhuma companhia fora do catalogo")
        code = outside[0].code
        cases.append(
            IpeCase(
                "companhia fora do catalogo e das nove (RF-03)",
                tuple(row for row in outside if row.code == code)[:2],
            )
        )
    return cases


def check_plain(row: IpeRow) -> None:
    """A linha escolhida precisa ser uma linha fisica sem aspas: `edit_member` e
    `ipe_rows` da `conftest` a partem por `;`."""
    raw = row.raw
    if (
        b'"' in raw
        or raw.count(b";") != FIELDS - 1
        or not raw.endswith(b"\r\n")
        or raw.count(b"\n") != 1
    ):
        raise SystemExit(f"linha nao partivel por ';': {raw[:200]!r}")


def main_ipe(work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    catalog = catalog_codes()
    for year in IPE_YEARS:
        cut = Cut(IPE, year, frozenset())
        payload, last_modified, downloaded = download(cut, work_dir)
        member_name = f"{IPE}_cia_aberta_{year}.csv"
        with zipfile.ZipFile(io.BytesIO(payload)) as source:
            names = source.namelist()
            if names != [member_name]:
                raise SystemExit(f"{cut.name}: membros {names}")
            info = source.getinfo(member_name)
            header, rows, malformed = ipe_rows(source.read(info))
        cases = ipe_cases(year, rows, catalog)
        chosen = {row.index: row for case in cases for row in case.rows}
        for row in chosen.values():
            check_plain(row)
        data = header + b"".join(chosen[index].raw for index in sorted(chosen))
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
            member = zipfile.ZipInfo(member_name, date_time=info.date_time)
            member.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(member, data)
        (OUT_DIR / cut.name).write_bytes(buffer.getvalue())
        print(f"{cut.name}")
        print(f"  url: {cvm_url(IPE, year)}")
        print(f"  baixado em: {downloaded}")
        print(f"  last-modified: {last_modified}")
        print(f"  content_sha256 do original: {content_sha256(payload)}")
        print(
            f"  bytes do original: {len(payload)}; da fixture: {len(buffer.getvalue())}"
        )
        print(
            f"  linhas do original: {len(rows)}"
            + (f", {malformed} mal formadas" if malformed else "")
            + f"; da fixture: {len(chosen)}"
        )
        for case in cases:
            print(f"  {case.reason}: {len(case.rows)} linhas")
            for row in case.rows:
                print(
                    f"    {row.code} | {row.values['Nome_Companhia']} | {row.category}"
                    f" | {row.values['Tipo_Apresentacao'][:2]} v{row.values['Versao']}"
                    f" | Assunto {len(row.values['Assunto'])} | {row.link}"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m tests.fixtures.cvm.recortar")
    parser.add_argument(
        "work_dir", type=Path, help="diretorio de trabalho, fora do repo"
    )
    parser.add_argument("--only", choices=[IPE], help="so as fixtures do IPE")
    arguments = parser.parse_args()
    if arguments.only == IPE:
        main_ipe(arguments.work_dir)
    else:
        main(arguments.work_dir)
