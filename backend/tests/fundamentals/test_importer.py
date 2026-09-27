"""`run_import_fundamentals` contra a `FakeCvm`: coleta, anos a conformar, transacao por
(companhia, ano), reconformacao e o relatorio (RF-02 a RF-05, RF-07, RF-11, RF-14, RF-16 a
RF-19, RF-27).

Todo teste grava no banco de teste, dentro da transacao por teste do pytest-django — o
`atomic()` por companhia vira *savepoint*. O catalogo e montado no teste: um `Asset` de
`kind = stock` com o `code_cvm` de cada companhia das fixtures que o teste quer conformar.

Duas propriedades da `serve_range` que os testes de varias coletas levam em conta: ela
**acrescenta** as filas da `FakeCvm`, e o `GET` de um arquivo que sai `nao modificado` fica
na fila, sem consumo. Por isso as substituicoes de um (tipo, ano) numa coleta sao feitas no
**ultimo** item das filas, o que a `serve_range` acabou de acrescentar. Toda alteracao sobre
uma fixture — membro removido, escala trocada, `DENOM_CIA` trocado, registro quebrado — e
declarada no teste que a faz.
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from collections.abc import Callable
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from apps.assets.models import Asset, CollectionRun
from apps.fundamentals import importer, zipdata
from apps.fundamentals.conform import ConformedStatement
from apps.fundamentals.cvm import CvmClientError, CvmDownload, CvmHead, cvm_url
from apps.fundamentals.importer import (
    SOURCE,
    FundamentalsImportFailed,
    ImportReport,
    YearCounts,
    run_import_fundamentals,
)
from apps.fundamentals.models import Company, CvmFile, FinancialStatement
from tests.fundamentals.conftest import (
    FakeCvm,
    Fields,
    edit_member,
    fixture_zip,
    serve_range,
)
from tests.fundamentals.test_conform_periods import (
    itr_2024_with_petrobras_at_dfp_date,
)

pytestmark = pytest.mark.django_db

SP = ZoneInfo("America/Sao_Paulo")
NOW_2025 = datetime(2025, 9, 30, 12, 0, tzinfo=SP)  # intervalo 2016..2025: 20 arquivos
NOW_2026 = datetime(2026, 9, 26, 12, 0, tzinfo=SP)  # intervalo 2016..2026: 22 arquivos
LATER = datetime(2025, 10, 7, 12, 0, tzinfo=SP)
LATEST = datetime(2025, 10, 14, 12, 0, tzinfo=SP)

PETROBRAS, VALE, ITAU, CAMIL = "9512", "4170", "19348", "24228"
NINE = ("9512", "4170", "19348", "906", "23159", "24805", "18627", "1228", "24228")

# As fixtures nos seus (tipo, ano). `serve_range` serve zip vazio nos demais.
ALL_FIXTURES = {
    ("itr", 2016): "itr_2016",
    ("itr", 2019): "itr_2019",
    ("itr", 2024): "itr_2024",
    ("dfp", 2024): "dfp_2024",
    ("itr", 2025): "itr_2025",
    ("dfp", 2025): "dfp_2025",
}


def fixtures(*keys: tuple[str, int]) -> dict[tuple[str, int], bytes]:
    """As fixtures de `keys`; sem argumento, todas."""
    chosen = keys or tuple(ALL_FIXTURES)
    return {key: fixture_zip(ALL_FIXTURES[key]) for key in chosen}


def clock(moment: datetime) -> Callable[[], datetime]:
    return lambda: moment


def add_stock(code_cvm: str | None, ticker: str | None = None) -> Asset:
    """Um `Asset` de `kind = stock` no catalogo, com o `code_cvm` dado."""
    now = timezone.now()
    ticker = ticker or f"X{code_cvm}"
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        code_cvm=code_cvm,
        created_at=now,
        updated_at=now,
    )


def importing(
    fake: FakeCvm,
    now: datetime,
    *,
    full: bool = False,
    reconform: list[int] | None = None,
) -> ImportReport:
    """A execucao, devolvendo o relatorio tambem quando ela termina `failed`."""
    try:
        return run_import_fundamentals(
            fake, full=full, reconform=reconform, now=clock(now)
        )
    except FundamentalsImportFailed as exc:
        return exc.report


def lines(report: ImportReport) -> list[str]:
    return report.render().splitlines()


def runs() -> list[CollectionRun]:
    return list(CollectionRun.objects.filter(source=SOURCE).order_by("pk"))


def year_prefixes(report: ImportReport, label: str) -> list[str]:
    """Os `"{label} {A}"` das linhas de resumo de ano, na ordem."""
    pattern = re.compile(rf"^({label} \d{{4}}): \d+ companhias, ")
    return [m.group(1) for line in lines(report) if (m := pattern.match(line))]


def statement_years(code_cvm: str) -> set[int]:
    return {
        d.year
        for d in FinancialStatement.objects.filter(
            company__code_cvm=code_cvm
        ).values_list("reference_date", flat=True)
    }


def gets(calls: list[tuple[str, str, int]]) -> list[tuple[str, int]]:
    return [(kind, year) for verb, kind, year in calls if verb == "get"]


def without_member(payload: bytes, member: str) -> bytes:
    """Modificacao declarada: o zip sem o membro `member`."""
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(payload)) as source,
        zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        assert member in source.namelist(), member
        for info in source.infolist():
            if info.filename != member:
                target.writestr(info, source.read(info))
    return out.getvalue()


def redated(payload: bytes) -> bytes:
    """Modificacao declarada: o mesmo conteudo, com outra data em todo membro."""
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(payload)) as source,
        zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        for info in source.infolist():
            fresh = zipfile.ZipInfo(info.filename, date_time=(2001, 2, 3, 4, 5, 6))
            fresh.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(fresh, source.read(info))
    return out.getvalue()


def set_column(
    column: str, value: str, code: str
) -> Callable[[Fields, list[Fields]], list[Fields]]:
    """Edicao que poe `value` em `column` nas linhas de `CD_CVM == code` (seis digitos)."""

    def edit(header: Fields, rows: list[Fields]) -> list[Fields]:
        cd_cvm, target = header.index("CD_CVM"), header.index(column)
        for row in rows:
            if row[cd_cvm] == code:
                row[target] = value
        return rows

    return edit


def replace_last(
    fake: FakeCvm,
    key: tuple[str, int],
    head: CvmHead | Exception | None = None,
    get: CvmDownload | Exception | None = None,
) -> None:
    """Troca a resposta que a `serve_range` acabou de acrescentar para `key`."""
    if head is not None:
        fake.heads[key][-1] = head
    if get is not None:
        fake.gets[key][-1] = get


# RF-02


def test_rf02_coleta_ok_cria_a_collection_run() -> None:
    add_stock(PETROBRAS)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures())

    run_import_fundamentals(fake, now=clock(NOW_2025))

    (run,) = runs()
    assert run.source == "cvm-dados-abertos"
    assert run.status == CollectionRun.Status.OK
    assert run.error == ""
    assert run.finished_at == NOW_2025


def test_rf02_arquivo_falho_torna_a_coleta_failed() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {})
    replace_last(fake, ("itr", 2019), head=CvmClientError("rede fora"))

    with pytest.raises(FundamentalsImportFailed) as caught:
        run_import_fundamentals(fake, now=clock(NOW_2025))

    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "itr 2019"
    assert "itr 2019: FALHOU (CvmClientError: rede fora)" in lines(caught.value.report)
    # CvmClientError nao deixa linha; os outros 19 arquivos deixaram
    assert not CvmFile.objects.filter(kind="itr", year=2019).exists()
    assert CvmFile.objects.count() == 19


def test_rf02_companhia_falha_torna_a_coleta_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_stock(PETROBRAS)
    add_stock(VALE)
    real = importer.write_company_year

    def failing(
        code_cvm: str,
        year: int,
        conformed: list[ConformedStatement],
        run: CollectionRun,
        now: datetime,
    ) -> YearCounts:
        if code_cvm == PETROBRAS and year == 2024:
            raise RuntimeError("escrita quebrada")
        return real(code_cvm, year, conformed, run, now)

    monkeypatch.setattr("apps.fundamentals.importer.write_company_year", failing)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures(("itr", 2024), ("dfp", 2024)))

    report = importing(fake, NOW_2025)

    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "ano 2024 9512"
    assert "ano 2024: FALHOU 9512 (RuntimeError: escrita quebrada)" in lines(report)
    assert run.finished_at is not None


def test_rf02_falha_no_nivel_do_ano() -> None:
    add_stock(PETROBRAS)
    # declarado: o DFP 2024 sem o membro DRE_con. O DFP so e lido no proprio ano; o ITR
    # 2024, lido tambem em 2025 como ano anterior, fica intacto
    broken = without_member(fixture_zip("dfp_2024"), "dfp_cia_aberta_DRE_con_2024.csv")
    served = fixtures(("itr", 2024), ("itr", 2025))
    served[("dfp", 2024)] = broken
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, served)

    report = importing(fake, NOW_2025)

    text = lines(report)
    (line,) = [t for t in text if t.startswith("ano 2024:")]
    assert line.startswith("ano 2024: FALHOU (KeyError: ")
    assert "dfp_cia_aberta_DRE_con_2024.csv" in line
    # o ano 2024 nao conformou nada; o 2025 conformou
    assert statement_years(PETROBRAS) == {2025}
    assert any(t.startswith("ano 2025: 1 companhias, ") for t in text)
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "ano 2024"
    assert run.finished_at is not None


# RF-03


def test_rf03_carga_inicial_pede_os_22_arquivos_em_ordem() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2026, {})

    report = run_import_fundamentals(fake, now=clock(NOW_2026))

    expected: list[tuple[str, str, int]] = []
    for year in range(2016, 2027):
        for kind in ("itr", "dfp"):
            expected += [("head", kind, year), ("get", kind, year)]
    assert fake.calls == expected
    assert len(expected) == 44
    assert lines(report)[-1] == (
        "coleta: 22 arquivos, 22 novos, 0 inalterados, 0 nao modificados, "
        "0 ausentes, 0 falhos"
    )


# RF-04


def test_rf04_so_baixa_o_arquivo_de_last_modified_diferente() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {})
    run_import_fundamentals(fake, now=clock(NOW_2025))
    # coleta 2: todos com o Last-Modified visto, menos o DFP 2020
    serve_range(fake, NOW_2025, {})
    same_content = fake.gets[("dfp", 2020)][-1]
    assert isinstance(same_content, CvmDownload)
    replace_last(
        fake,
        ("dfp", 2020),
        head=CvmHead(200, "gen-2-dfp-2020"),
        get=CvmDownload(200, "gen-2-dfp-2020", same_content.url, same_content.payload),
    )
    mark = len(fake.calls)

    report = run_import_fundamentals(fake, now=clock(NOW_2025))

    assert gets(fake.calls[mark:]) == [("dfp", 2020)]
    assert len(fake.calls[mark:]) == 21  # 20 HEAD e um GET
    text = lines(report)
    assert "dfp 2019: nao modificado" in text
    assert any(
        re.fullmatch(r"dfp 2020: baixado, \d+ bytes, inalterado", t) for t in text
    )


def test_rf04_head_sem_last_modified_baixa() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {})
    run_import_fundamentals(fake, now=clock(NOW_2025))
    serve_range(fake, NOW_2025, {})
    replace_last(fake, ("itr", 2018), head=CvmHead(200, None))
    mark = len(fake.calls)

    run_import_fundamentals(fake, now=clock(NOW_2025))

    assert gets(fake.calls[mark:]) == [("itr", 2018)]


def test_rf04_full_baixa_todos() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {})
    run_import_fundamentals(fake, now=clock(NOW_2025))
    serve_range(fake, NOW_2025, {})
    mark = len(fake.calls)

    report = run_import_fundamentals(fake, full=True, now=clock(NOW_2025))

    assert len(gets(fake.calls[mark:])) == 20
    assert lines(report)[-1] == (
        "coleta: 20 arquivos, 0 novos, 20 inalterados, 0 nao modificados, "
        "0 ausentes, 0 falhos"
    )


def test_rf04_404_do_ano_corrente_e_ausente_e_nao_falha() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2026, {})
    replace_last(fake, ("dfp", 2026), head=CvmHead(404, None))
    replace_last(
        fake,
        ("itr", 2026),
        get=CvmDownload(404, None, cvm_url("itr", 2026), None),
    )

    report = run_import_fundamentals(fake, now=clock(NOW_2026))  # nao levanta

    text = lines(report)
    assert "itr 2026: ausente" in text
    assert "dfp 2026: ausente" in text
    assert text[-1] == (
        "coleta: 22 arquivos, 20 novos, 0 inalterados, 0 nao modificados, "
        "2 ausentes, 0 falhos"
    )
    (run,) = runs()
    assert run.status == CollectionRun.Status.OK
    # o GET com 404 grava a linha, sem payload nem hash; o HEAD com 404 nao deixa linha
    (row,) = CvmFile.objects.filter(kind="itr", year=2026)
    assert (row.http_status, row.content_sha256, row.payload) == (404, None, None)
    assert not CvmFile.objects.filter(kind="dfp", year=2026).exists()


def test_rf04_404_de_outro_ano_e_falha() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {})
    replace_last(fake, ("itr", 2019), head=CvmHead(404, None))
    replace_last(
        fake, ("dfp", 2019), get=CvmDownload(404, None, cvm_url("dfp", 2019), None)
    )

    report = importing(fake, NOW_2025)

    text = lines(report)
    assert "itr 2019: FALHOU (UnexpectedStatus: HEAD devolveu 404)" in text
    assert "dfp 2019: FALHOU (UnexpectedStatus: GET devolveu 404)" in text
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "itr 2019, dfp 2019"
    (row,) = CvmFile.objects.filter(kind="dfp", year=2019)
    assert (row.http_status, row.content_sha256, row.payload) == (404, None, None)


def test_rf04_zip_ruim_nao_conta_como_visto() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {})
    replace_last(
        fake,
        ("itr", 2020),
        get=CvmDownload(200, "gen-1-itr-2020", cvm_url("itr", 2020), b"nao e zip"),
    )
    first = importing(fake, NOW_2025)
    assert "itr 2020: FALHOU (BadZipFile: File is not a zip file)" in lines(first)
    (bad,) = CvmFile.objects.filter(kind="itr", year=2020)
    assert (bad.http_status, bad.content_sha256, bad.payload) == (200, None, None)

    # coleta 2: o mesmo Last-Modified, e o zip ruim nao e o ultimo visto
    serve_range(fake, NOW_2025, {})
    mark = len(fake.calls)
    second = run_import_fundamentals(fake, now=clock(NOW_2025))

    assert gets(fake.calls[mark:]) == [("itr", 2020)]
    assert any(
        re.fullmatch(r"itr 2020: baixado, \d+ bytes, novo", t) for t in lines(second)
    )


def test_rf04_ano_corrente_lido_uma_vez_na_virada_do_ano() -> None:
    """O relogio vira o ano no meio da execucao: a primeira leitura e 2025-12-31 23:59 e
    as seguintes, 2026-01-01. O intervalo e o 404 do ano corrente sao os de 2025 — o ano
    lido uma vez so. Declarado: o HEAD do ITR 2025 responde 404."""
    fake = FakeCvm({}, {})
    first = datetime(2025, 12, 31, 23, 59, tzinfo=SP)
    serve_range(fake, first, {})
    replace_last(fake, ("itr", 2025), head=CvmHead(404, None))
    moments = iter([first])

    def turning() -> datetime:
        return next(moments, datetime(2026, 1, 1, 0, 1, tzinfo=SP))

    report = run_import_fundamentals(fake, now=turning)  # nao levanta

    text = lines(report)
    assert "itr 2025: ausente" in text
    assert text[-1] == (
        "coleta: 20 arquivos, 19 novos, 0 inalterados, 0 nao modificados, "
        "1 ausentes, 0 falhos"
    )
    assert not any(year == 2026 for _, _, year in fake.calls)
    (run,) = runs()
    assert run.status == CollectionRun.Status.OK


# RF-05


def corrupted_member(payload: bytes, member: str) -> bytes:
    """Modificacao declarada: o zip com o primeiro byte comprimido de `member` trocado por
    `0xff` — bloco *deflate* de tipo invalido, e a leitura do membro levanta `zlib.error`.
    O diretorio do zip fica intacto: o zip abre, o membro nao se le."""
    with zipfile.ZipFile(io.BytesIO(payload)) as source:
        info = source.getinfo(member)
    assert info.compress_type == zipfile.ZIP_DEFLATED
    data = bytearray(payload)
    offset = info.header_offset
    name_len = int.from_bytes(data[offset + 26 : offset + 28], "little")
    extra_len = int.from_bytes(data[offset + 28 : offset + 30], "little")
    data[offset + 30 + name_len + extra_len] = 0xFF
    return bytes(data)


def test_rf05_membro_corrompido_e_arquivo_falho_sem_payload_nem_hash() -> None:
    corrupted = corrupted_member(
        fixture_zip("itr_2024"), "itr_cia_aberta_DRE_con_2024.csv"
    )
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {("itr", 2024): corrupted})

    report = importing(fake, NOW_2025)

    assert (
        "itr 2024: FALHOU (error: Error -3 while decompressing data: invalid block type)"
        in lines(report)
    )
    (row,) = CvmFile.objects.filter(kind="itr", year=2024)
    assert (row.http_status, row.content_sha256, row.payload) == (200, None, None)
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "itr 2024"


def test_rf05_eof_na_leitura_do_zip_e_arquivo_falho(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Declarado: o hash de conteudo do ITR 2024 levanta `EOFError` — o que o `zipfile`
    levanta quando o membro acaba antes do tamanho declarado."""
    real = zipdata.content_sha256
    target = fixture_zip("itr_2024")

    def truncated(payload: bytes) -> str:
        if payload == target:
            raise EOFError("membro truncado")
        return real(payload)

    monkeypatch.setattr("apps.fundamentals.importer.content_sha256", truncated)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {("itr", 2024): target})

    report = importing(fake, NOW_2025)

    assert "itr 2024: FALHOU (EOFError: membro truncado)" in lines(report)
    (row,) = CvmFile.objects.filter(kind="itr", year=2024)
    assert (row.http_status, row.content_sha256, row.payload) == (200, None, None)
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED


def test_rf05_linha_por_get_e_payload_so_quando_o_conteudo_e_novo() -> None:
    original = fixture_zip("itr_2024")
    regenerated = redated(original)
    assert hashlib.sha256(original).digest() != hashlib.sha256(regenerated).digest()
    size = len(original)
    fake = FakeCvm({}, {})

    # coleta 1: baixa e grava com payload
    serve_range(fake, NOW_2025, {("itr", 2024): original})
    first = run_import_fundamentals(fake, now=clock(NOW_2025))
    assert f"itr 2024: baixado, {size} bytes, novo" in lines(first)

    # coleta 2: Last-Modified novo, o mesmo conteudo com outras datas de membro
    serve_range(fake, NOW_2025, {("itr", 2024): original})
    replace_last(
        fake,
        ("itr", 2024),
        head=CvmHead(200, "gen-2-itr-2024"),
        get=CvmDownload(200, "gen-2-itr-2024", cvm_url("itr", 2024), regenerated),
    )
    second = run_import_fundamentals(fake, now=clock(NOW_2025))
    assert f"itr 2024: baixado, {len(regenerated)} bytes, inalterado" in lines(second)

    rows = list(CvmFile.objects.filter(kind="itr", year=2024).order_by("pk"))
    assert len(rows) == 2
    assert rows[0].payload is not None and bytes(rows[0].payload) == original
    assert rows[1].payload is None
    assert rows[0].content_sha256 == rows[1].content_sha256 is not None
    assert rows[1].last_modified == "gen-2-itr-2024"

    # coleta 3: o Last-Modified da 2 — so o HEAD. Um GET esgotaria a fila e reprovaria
    serve_range(fake, NOW_2025, {})
    replace_last(fake, ("itr", 2024), head=CvmHead(200, "gen-2-itr-2024"))
    fake.gets[("itr", 2024)].pop()
    mark = len(fake.calls)
    third = run_import_fundamentals(fake, now=clock(NOW_2025))

    assert "itr 2024: nao modificado" in lines(third)
    assert ("get", "itr", 2024) not in fake.calls[mark:]
    assert CvmFile.objects.filter(kind="itr", year=2024).count() == 2


# RF-07


def test_rf07_so_o_catalogo_entra_em_silver_company() -> None:
    add_stock(PETROBRAS)
    add_stock(VALE)
    add_stock(None, "SEMCVM3")  # acao sem code_cvm nao entra no catalogo
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures(("dfp", 2024)))  # as nove companhias

    run_import_fundamentals(fake, now=clock(NOW_2025))

    assert set(Company.objects.values_list("code_cvm", flat=True)) == {PETROBRAS, VALE}
    assert statement_years(ITAU) == set()


# RF-11


def test_rf11_escala_milhao_faz_a_companhia_falhar_no_ano() -> None:
    add_stock(PETROBRAS)
    add_stock(VALE)
    # declarado: ESCALA_MOEDA = MILHAO em toda linha da Petrobras na DRE consolidada
    dfp = edit_member(
        fixture_zip("dfp_2024"),
        "dfp_cia_aberta_DRE_con_2024.csv",
        set_column("ESCALA_MOEDA", "MILHAO", "009512"),
    )
    served = fixtures(("itr", 2024))
    served[("dfp", 2024)] = dfp
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, served)

    report = importing(fake, NOW_2025)

    assert "ano 2024: FALHOU 9512 (ValueError: ESCALA_MOEDA MILHAO)" in lines(report)
    assert statement_years(PETROBRAS) == set()
    assert statement_years(VALE) == {2024}
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED


# RF-14


def test_rf14_importer_le_o_itr_do_ano_anterior() -> None:
    add_stock(CAMIL)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures(("itr", 2024), ("dfp", 2025)))

    run_import_fundamentals(fake, now=clock(NOW_2025))

    q4 = FinancialStatement.objects.get(
        company__code_cvm=CAMIL, reference_date=date(2025, 2, 28)
    )
    assert q4.source == "dfp"
    assert q4.revenue is not None
    assert q4.net_income_parent is not None


# RF-16


def test_rf16_escrita_falha_numa_companhia_reverte_so_ela(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for code in (PETROBRAS, VALE, ITAU):
        add_stock(code)
    real = importer.write_company_year
    attempts: list[tuple[str, int]] = []

    def vale_breaks(
        code_cvm: str,
        year: int,
        conformed: list[ConformedStatement],
        run: CollectionRun,
        now: datetime,
    ) -> YearCounts:
        attempts.append((code_cvm, year))
        counts = real(code_cvm, year, conformed, run, now)
        if code_cvm == VALE:  # pela companhia, nao pela ordem das chamadas
            assert FinancialStatement.objects.filter(company__code_cvm=VALE).exists()
            raise RuntimeError("falha depois de gravar")
        return counts

    monkeypatch.setattr("apps.fundamentals.importer.write_company_year", vale_breaks)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures(("itr", 2024), ("dfp", 2024)))

    report = importing(fake, NOW_2025)

    assert not Company.objects.filter(code_cvm=VALE).exists()
    assert not FinancialStatement.objects.filter(company__code_cvm=VALE).exists()
    assert statement_years(PETROBRAS) == {2024}
    assert statement_years(ITAU) == {2024}
    assert "ano 2024: FALHOU 4170 (RuntimeError: falha depois de gravar)" in lines(
        report
    )
    assert not any(t.startswith("novas ") for t in lines(report))
    assert attempts.count((VALE, 2024)) == 1
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED


# RF-17


def test_rf17_a_conforma_o_ano_alterado_e_o_seguinte() -> None:
    add_stock(PETROBRAS)
    served = fixtures(("itr", 2019), ("itr", 2024), ("dfp", 2024))
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, served)
    run_import_fundamentals(fake, now=clock(NOW_2025))

    # coleta 2: so o ITR 2024 muda — declarado: sem a ultima linha da DRE consolidada
    changed = edit_member(
        fixture_zip("itr_2024"),
        "itr_cia_aberta_DRE_con_2024.csv",
        lambda header, rows: rows[:-1],
    )
    serve_range(fake, NOW_2025, served)
    replace_last(
        fake,
        ("itr", 2024),
        head=CvmHead(200, "gen-2-itr-2024"),
        get=CvmDownload(200, "gen-2-itr-2024", cvm_url("itr", 2024), changed),
    )
    report = run_import_fundamentals(fake, now=clock(NOW_2025))

    assert year_prefixes(report, "ano") == ["ano 2024", "ano 2025"]
    assert year_prefixes(report, "novas") == []


def test_rf17_carga_inicial_sem_novas_e_conta_sem_documento_na_cvm() -> None:
    for code in (*NINE, "99901", "99902"):  # os dois ultimos, fora das fixtures
        add_stock(code)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures())

    report = run_import_fundamentals(fake, now=clock(NOW_2025))

    assert "catalogo: 0 companhias novas, 2 sem documento na cvm" in lines(report)
    assert year_prefixes(report, "novas") == []


def test_rf17_b_companhia_nova_com_arquivos_nao_modificados() -> None:
    add_stock(VALE)
    served = fixtures(("itr", 2019), ("itr", 2024), ("dfp", 2024))
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, served)
    run_import_fundamentals(fake, now=clock(NOW_2025))
    assert not Company.objects.filter(code_cvm=PETROBRAS).exists()

    add_stock(PETROBRAS, "PETR4")  # entra no catalogo depois da carga
    serve_range(fake, NOW_2025, served)  # mesmo generation: tudo `nao modificado`
    mark = len(fake.calls)
    report = run_import_fundamentals(fake, now=clock(NOW_2025))

    assert gets(fake.calls[mark:]) == []
    assert statement_years(PETROBRAS) == {2019, 2024}
    assert year_prefixes(report, "ano") == []
    assert year_prefixes(report, "novas") == [f"novas {y}" for y in range(2016, 2026)]
    text = lines(report)
    assert any(t.startswith("novas 2019: 1 companhias, ") for t in text)
    assert any(t.startswith("novas 2024: 1 companhias, ") for t in text)
    assert "catalogo: 1 companhias novas, 0 sem documento na cvm" in text


def test_rf17_b_com_a_na_mesma_coleta() -> None:
    served = fixtures(("itr", 2019), ("itr", 2024), ("dfp", 2024))  # ITR 2025 vazio
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, served, generation=1)
    run_import_fundamentals(fake, now=clock(NOW_2025))  # Petrobras fora do catalogo

    add_stock(PETROBRAS, "PETR4")
    served[("itr", 2025)] = fixture_zip("itr_2025")  # o ITR 2025 real: payload novo
    serve_range(fake, NOW_2025, served, generation=2)
    report = run_import_fundamentals(fake, now=clock(NOW_2025))

    # o historico inteiro: o ano corrente por (a), os outros por (b)
    assert statement_years(PETROBRAS) == {2019, 2024, 2025}
    assert year_prefixes(report, "ano") == ["ano 2025"]
    assert year_prefixes(report, "novas") == [f"novas {y}" for y in range(2016, 2025)]
    text = lines(report)
    assert any(t.startswith("ano 2025: 1 companhias, ") for t in text)
    assert any(t.startswith("novas 2019: 1 companhias, ") for t in text)
    assert any(t.startswith("novas 2024: 1 companhias, ") for t in text)
    assert "catalogo: 1 companhias novas, 0 sem documento na cvm" in text


def test_rf17_codigo_fora_da_cvm_e_sem_documento() -> None:
    add_stock(PETROBRAS)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures(("itr", 2024)))
    run_import_fundamentals(fake, now=clock(NOW_2025))

    add_stock("99999")  # codigo que a CVM nao conhece
    serve_range(fake, NOW_2025, fixtures(("itr", 2024)))
    report = run_import_fundamentals(fake, now=clock(NOW_2025))

    assert "catalogo: 0 companhias novas, 1 sem documento na cvm" in lines(report)
    assert year_prefixes(report, "novas") == []
    assert not Company.objects.filter(code_cvm="99999").exists()


def test_rf17_reconform_conforma_da_bronze_sem_chamar_a_cvm() -> None:
    add_stock(PETROBRAS)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures(("itr", 2024), ("dfp", 2024)))
    run_import_fundamentals(fake, now=clock(NOW_2025))
    FinancialStatement.objects.all().delete()
    Company.objects.all().delete()

    empty = FakeCvm({}, {})
    report = run_import_fundamentals(empty, reconform=[2024], now=clock(LATER))

    assert empty.calls == []
    assert statement_years(PETROBRAS) == {2024}
    assert lines(report) == [line for line in lines(report) if line.startswith("ano ")]
    assert year_prefixes(report, "ano") == ["ano 2024"]

    everything = run_import_fundamentals(empty, reconform=[], now=clock(LATEST))
    assert empty.calls == []
    assert year_prefixes(everything, "ano") == [f"ano {y}" for y in range(2016, 2026)]
    # RF-02: o --reconform tambem cria a collection_run, e ela termina ok
    reconform_runs = runs()[1:]
    assert len(reconform_runs) == 2
    assert {r.status for r in reconform_runs} == {CollectionRun.Status.OK}


def test_rf17_full_e_reconform_juntos_levantam_antes_de_tudo() -> None:
    empty = FakeCvm({}, {})
    with pytest.raises(ValueError):
        run_import_fundamentals(empty, full=True, reconform=[], now=clock(NOW_2025))
    assert empty.calls == []
    assert runs() == []


# RF-18


def test_rf18_reconform_duas_vezes_nao_cria_nem_atualiza() -> None:
    for code in NINE:
        add_stock(code)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, fixtures())
    run_import_fundamentals(fake, now=clock(NOW_2025))
    statements = dict(
        FinancialStatement.objects.values_list("pk", "updated_at").order_by("pk")
    )
    companies = dict(Company.objects.values_list("pk", "updated_at").order_by("pk"))
    assert len(statements) > 0 and len(companies) == len(NINE)

    empty = FakeCvm({}, {})
    run_import_fundamentals(empty, reconform=[], now=clock(LATER))
    second = run_import_fundamentals(empty, reconform=[], now=clock(LATEST))

    summaries = [t for t in lines(second) if re.match(r"ano \d{4}: \d+ companhias", t)]
    assert len(summaries) == 10
    assert all(", 0 criados, 0 atualizados, " in t for t in summaries)
    assert any(not re.match(r"ano \d{4}: 0 companhias", t) for t in summaries)
    assert (
        dict(FinancialStatement.objects.values_list("pk", "updated_at").order_by("pk"))
        == statements
    )
    assert dict(Company.objects.values_list("pk", "updated_at").order_by("pk")) == (
        companies
    )


# RF-19


def test_rf19_nome_e_o_do_documento_mais_recente() -> None:
    add_stock(PETROBRAS)
    # declarado: DENOM_CIA da Petrobras trocado no indice do ITR 2019 (o real e igual)
    itr_2019 = edit_member(
        fixture_zip("itr_2019"),
        "itr_cia_aberta_2019.csv",
        set_column("DENOM_CIA", "NOME ANTIGO DE TESTE", "009512"),
    )
    served = fixtures(("itr", 2024), ("dfp", 2024))
    served[("itr", 2019)] = itr_2019
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, served)
    run_import_fundamentals(fake, now=clock(NOW_2025))

    company = Company.objects.get(code_cvm=PETROBRAS)
    assert company.name == "PETROLEO BRASILEIRO S.A. PETROBRAS"
    assert company.source_reference_date == date(2024, 12, 31)

    # reconformar 2019 depois de 2024 nao sobrescreve o nome do mais recente
    report = run_import_fundamentals(
        FakeCvm({}, {}), reconform=[2019], now=clock(LATER)
    )

    assert any(t.startswith("ano 2019: 1 companhias, ") for t in lines(report))
    company.refresh_from_db()
    assert company.name == "PETROLEO BRASILEIRO S.A. PETROBRAS"
    assert company.source_reference_date == date(2024, 12, 31)
    assert company.updated_at == NOW_2025
    assert statement_years(PETROBRAS) == {2019, 2024}


# RF-27

FILE_LINE = re.compile(
    r"(itr|dfp) \d{4}: (baixado, \d+ bytes, (novo|inalterado)|nao modificado|ausente"
    r"|FALHOU \(\w+: .*\))"
)
YEAR_LINE = re.compile(
    r"(ano|novas) \d{4}: (\d+ companhias, \d+ criados, \d+ atualizados, \d+ ausentes, "
    r"\d+ plano desconhecido, \d+ falhos|FALHOU (\d+ )?\(\w+: .*\)"
    r"|\d+ registros mal formados descartados \(.+\)"
    r"|\d+ itr descartados por dfp na mesma data \(.+\))"
)
CATALOG_LINE = re.compile(
    r"catalogo: (\d+ companhias novas, \d+ sem documento na cvm|FALHOU .+)"
)
COLLECTION_LINE = re.compile(
    r"coleta: \d+ arquivos, \d+ novos, \d+ inalterados, \d+ nao modificados, "
    r"\d+ ausentes, \d+ falhos"
)


def test_rf27_relatorio_ancorado_nos_rotulos() -> None:
    for code in NINE:
        add_stock(code)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2026, fixtures())
    replace_last(fake, ("dfp", 2026), head=CvmHead(404, None))
    replace_last(fake, ("itr", 2017), head=CvmClientError("rede fora"))

    report = importing(fake, NOW_2026)

    text = lines(report)
    for line in text:
        assert any(
            p.fullmatch(line)
            for p in (FILE_LINE, YEAR_LINE, CATALOG_LINE, COLLECTION_LINE)
        ), line
    assert text[0] == f"itr 2016: baixado, {len(fixture_zip('itr_2016'))} bytes, novo"
    assert "itr 2017: FALHOU (CvmClientError: rede fora)" in text
    assert "dfp 2026: ausente" in text
    assert text[-2] == "catalogo: 0 companhias novas, 0 sem documento na cvm"
    assert text[-1] == (
        "coleta: 22 arquivos, 20 novos, 0 inalterados, 0 nao modificados, "
        "1 ausentes, 1 falhos"
    )
    # na ordem: arquivos, anos, catalogo, coleta
    kinds = [
        "file"
        if FILE_LINE.fullmatch(t)
        else "year"
        if YEAR_LINE.fullmatch(t)
        else "end"
        for t in text
    ]
    assert kinds == sorted(kinds, key=["file", "year", "end"].index)
    assert year_prefixes(report, "ano") == [f"ano {y}" for y in range(2016, 2027)]
    (line_2024,) = [t for t in text if t.startswith("ano 2024: ")]
    assert line_2024.startswith("ano 2024: 9 companhias, ")
    assert line_2024.endswith(", 0 falhos")


def test_rf27_registros_mal_formados_sao_relatados_e_nao_sao_falha() -> None:
    add_stock(PETROBRAS)
    # declarado: um registro de um campo so no fim da DRE consolidada do ITR 2024
    itr_2024 = edit_member(
        fixture_zip("itr_2024"),
        "itr_cia_aberta_DRE_con_2024.csv",
        lambda header, rows: [*rows, ["quebrado"]],
    )
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {("itr", 2024): itr_2024})

    report = run_import_fundamentals(fake, now=clock(NOW_2025))  # nao levanta

    text = lines(report)
    expected = (
        "{}: 1 registros mal formados descartados (itr_cia_aberta_DRE_con_2024.csv: 1)"
    )
    # logo depois da linha do ano — em 2024 e em 2025, que le o ITR 2024 como anterior
    for year in (2024, 2025):
        at = next(i for i, t in enumerate(text) if t.startswith(f"ano {year}: "))
        assert text[at + 1] == expected.format(f"ano {year}")
    assert not any("mal formados" in t for t in text if t.startswith("ano 2023"))
    (run,) = runs()
    assert run.status == CollectionRun.Status.OK


# RF-13b


def test_rf13b_itr_e_dfp_na_mesma_data_vale_o_dfp_e_nao_e_falha() -> None:
    add_stock(PETROBRAS)
    # declarado: o ITR 2024 com um documento da Petrobras em 2024-12-31, a data do DFP
    # 2024 (a construcao esta em `itr_2024_with_petrobras_at_dfp_date`)
    fake = FakeCvm({}, {})
    serve_range(
        fake,
        NOW_2025,
        {
            ("itr", 2024): itr_2024_with_petrobras_at_dfp_date(),
            ("dfp", 2024): fixture_zip("dfp_2024"),
        },
    )

    report = run_import_fundamentals(fake, now=clock(NOW_2025))  # nao levanta

    (run,) = runs()
    assert run.status == CollectionRun.Status.OK
    assert run.error == ""
    rows = FinancialStatement.objects.filter(
        company__code_cvm=PETROBRAS, reference_date__year=2024
    ).order_by("reference_date")
    assert [(r.reference_date, r.source) for r in rows] == [
        (date(2024, 3, 31), "itr"),
        (date(2024, 6, 30), "itr"),
        (date(2024, 9, 30), "itr"),
        (date(2024, 12, 31), "dfp"),
    ]
    text = lines(report)
    at = next(i for i, t in enumerate(text) if t.startswith("ano 2024: "))
    assert text[at] == (
        "ano 2024: 1 companhias, 4 criados, 0 atualizados, 0 ausentes, "
        "0 plano desconhecido, 0 falhos"
    )
    assert text[at + 1] == "ano 2024: 1 itr descartados por dfp na mesma data (9512)"
    assert YEAR_LINE.fullmatch(text[at + 1])
    # o ano 2025 le o ITR 2024 so como anterior: nao descarta nada
    assert not any("itr descartados" in t for t in text if not t.startswith("ano 2024"))
