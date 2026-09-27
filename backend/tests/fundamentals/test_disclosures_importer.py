"""`run_import_disclosures` contra a `FakeCvm` servindo so `ipe`: coleta, anos a conformar,
versao corrente, transacao por (companhia, ano), reconformacao e o relatorio (M3.2, RF-02,
RF-04, RF-04a, RF-07, RF-07b, RF-08, RF-09).

Todo teste grava no banco de teste, dentro da transacao por teste do pytest-django — o
`atomic()` por companhia vira *savepoint*. O catalogo e montado no teste, por `add_stock`.
As substituicoes de um ano numa coleta sao feitas no **ultimo** item das filas da
`FakeCvm`, o que a `serve_range` acabou de acrescentar (ver `test_importer.py`). Toda
alteracao sobre uma fixture — link, versao, categoria ou `Codigo_CVM` trocados, linhas
tiradas, registro quebrado ou repetido — e declarada no teste que a faz.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from apps.assets.models import Asset, CollectionRun
from apps.fundamentals import disclosures_importer
from apps.fundamentals.cvm import IPE, CvmDownload, CvmHead, cvm_url
from apps.fundamentals.disclosures import ConformedDisclosure
from apps.fundamentals.disclosures_importer import (
    SOURCE,
    DisclosureCounts,
    DisclosuresImportFailed,
    DisclosuresReport,
    run_import_disclosures,
)
from apps.fundamentals.models import Company, CvmFile, Disclosure
from tests.fundamentals.conftest import (
    FakeCvm,
    Fields,
    edit_member,
    empty_ipe_zip,
    fixture_zip,
    ipe_rows,
    serve_range,
)
from tests.fundamentals.test_importer import (
    add_stock,
    clock,
    gets,
    redated,
    replace_last,
)

pytestmark = pytest.mark.django_db

SP = ZoneInfo("America/Sao_Paulo")
NOW_2025 = datetime(2025, 9, 30, 12, 0, tzinfo=SP)  # intervalo 2016..2025: 10 arquivos
NOW_2026 = datetime(2026, 9, 26, 12, 0, tzinfo=SP)  # intervalo 2016..2026: 11 arquivos
LATER = datetime(2026, 10, 3, 12, 0, tzinfo=SP)

PETROBRAS, VALE, ITAU = "9512", "4170", "19348"
NINE = ("9512", "4170", "19348", "906", "23159", "24805", "18627", "1228", "24228")
OUTSIDE_CODE = "26190"  # nas fixtures, fora do catalogo de todo teste

LINK = (
    "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext&descTipo=IPE"
    "&CodigoInstituicao=1&numProtocolo={}&numSequencia={}&numVersao={}"
)
# Os dois `(Protocolo_Entrega, Versao)` com dois links do `ipe_2025` (README das fixtures)
PETROBRAS_PAIR = (LINK.format(1337188, 861914, 1), LINK.format(1337189, 861915, 1))
ITAU_PAIR = (LINK.format(1330895, 855621, 1), LINK.format(1330899, 855625, 1))
# A reapresentacao da Petrobras em 2025, "Fato Relevante", versao 2
PETROBRAS_V2 = LINK.format(1328611, 853337, 2)
# Um "Fato Relevante" da Vale e um da Petrobras em 2025, versao 1
VALE_FACT = LINK.format(1334979, 859705, 1)
PETROBRAS_FACT = LINK.format(1328570, 853296, 1)

Edit = Callable[[Fields, list[Fields]], list[Fields]]


def ipe(year: int) -> bytes:
    return fixture_zip(f"ipe_{year}")


def both() -> dict[tuple[str, int], bytes]:
    return {(IPE, 2025): ipe(2025), (IPE, 2026): ipe(2026)}


def edited(year: int, edit: Edit) -> bytes:
    """Modificacao declarada: o `ipe_<year>.zip` com o membro reescrito por `edit`."""
    return edit_member(ipe(year), f"ipe_cia_aberta_{year}.csv", edit)


def set_on_link(link: str, **columns: str) -> Edit:
    """Troca as colunas dadas na linha de `link`; as outras linhas ficam intocadas."""

    def edit(header: Fields, rows: list[Fields]) -> list[Fields]:
        where = header.index("Link_Download")
        matches = [row for row in rows if row[where] == link]
        assert len(matches) == 1, link
        for column, value in columns.items():
            matches[0][header.index(column)] = value
        return rows

    return edit


def without_code(code: str) -> Edit:
    """Tira todas as linhas de `Codigo_CVM == code`."""

    def edit(header: Fields, rows: list[Fields]) -> list[Fields]:
        at = header.index("Codigo_CVM")
        kept = [row for row in rows if row[at] != code]
        assert len(kept) < len(rows), code
        return kept

    return edit


def row_of(year: int, link: str) -> dict[str, str]:
    header, rows = ipe_rows(ipe(year), year)
    where = header.index("Link_Download")
    (row,) = [row for row in rows if row[where] == link]
    return dict(zip(header, row, strict=True))


def importing(
    fake: FakeCvm,
    now: datetime,
    *,
    full: bool = False,
    reconform: list[int] | None = None,
) -> DisclosuresReport:
    """A execucao, devolvendo o relatorio tambem quando ela termina `failed`."""
    try:
        return run_import_disclosures(
            fake, full=full, reconform=reconform, now=clock(now)
        )
    except DisclosuresImportFailed as exc:
        return exc.report


def lines(report: DisclosuresReport) -> list[str]:
    return report.render().splitlines()


def runs() -> list[CollectionRun]:
    return list(CollectionRun.objects.filter(source=SOURCE).order_by("pk"))


def year_prefixes(report: DisclosuresReport, label: str) -> list[str]:
    """Os `"{label} {A}"` das linhas de resumo de ano, na ordem."""
    pattern = re.compile(rf"^({label} \d{{4}}): \d+ companhias, ")
    return [m.group(1) for line in lines(report) if (m := pattern.match(line))]


def links_of(code: str, year: int) -> set[str]:
    return set(
        Disclosure.objects.filter(code_cvm=code, year=year).values_list(
            "link", flat=True
        )
    )


def first_load(now: datetime, *codes: str) -> FakeCvm:
    """O catalogo com `codes` e a primeira coleta, com as duas fixtures (generation 1)."""
    for code in codes:
        add_stock(code)
    fake = FakeCvm({}, {})
    serve_range(fake, now, both(), kinds=(IPE,))
    run_import_disclosures(fake, now=clock(now))
    return fake


def serve_changed(fake: FakeCvm, now: datetime, changed: dict[int, bytes]) -> None:
    """A coleta seguinte: todo arquivo com o `Last-Modified` visto (`nao modificado`),
    menos os anos de `changed`, que ganham `Last-Modified` novo e o conteudo dado."""
    serve_range(fake, now, both(), kinds=(IPE,))
    for year, payload in changed.items():
        replace_last(
            fake,
            (IPE, year),
            head=CvmHead(200, f"gen-2-ipe-{year}"),
            get=CvmDownload(200, f"gen-2-ipe-{year}", cvm_url(IPE, year), payload),
        )


# RF-02


def test_rf02_coleta_cria_a_collection_run_cvm_ipe() -> None:
    add_stock(PETROBRAS)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2026, both(), kinds=(IPE,))

    run_import_disclosures(fake, now=clock(NOW_2026))

    (run,) = runs()
    assert run.source == "cvm-ipe"
    assert run.status == CollectionRun.Status.OK
    assert run.error == ""
    assert run.finished_at == NOW_2026
    assert Disclosure.objects.filter(code_cvm=PETROBRAS, run=run).exists()


def test_rf02_intervalo_de_2016_ao_ano_corrente_em_ordem() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {(IPE, 2025): ipe(2025)}, kinds=(IPE,))

    report = run_import_disclosures(fake, now=clock(NOW_2025))

    assert fake.calls == [
        (verb, IPE, year) for year in range(2016, 2026) for verb in ("head", "get")
    ]
    assert [line.split(":")[0] for line in lines(report)[:10]] == [
        f"ipe {year}" for year in range(2016, 2026)
    ]
    # primeira carga: todo ano e `novo`, e (b) nao conforma nada
    assert year_prefixes(report, "ano") == [f"ano {y}" for y in range(2016, 2026)]
    assert year_prefixes(report, "novas") == []


def test_rf02_last_modified_visto_e_nao_modificado_sem_get() -> None:
    fake = first_load(NOW_2025)
    serve_changed(fake, NOW_2025, {})
    fake.gets[(IPE, 2020)].pop()  # um GET de 2020 esgotaria a fila e reprovaria
    mark = len(fake.calls)

    report = run_import_disclosures(fake, now=clock(NOW_2025))

    assert gets(fake.calls[mark:]) == []
    assert "ipe 2020: nao modificado" in lines(report)
    assert CvmFile.objects.filter(kind=IPE, year=2020).count() == 1


def test_rf02_404_do_ano_corrente_e_ausente_e_a_coleta_ok() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2026, both(), kinds=(IPE,))
    replace_last(fake, (IPE, 2026), head=CvmHead(404, None))

    report = run_import_disclosures(fake, now=clock(NOW_2026))  # nao levanta

    assert "ipe 2026: ausente" in lines(report)
    (run,) = runs()
    assert run.status == CollectionRun.Status.OK
    assert not CvmFile.objects.filter(kind=IPE, year=2026).exists()


def test_rf02_zip_ruim_falha_e_a_coleta_sai_failed() -> None:
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {}, kinds=(IPE,))
    replace_last(
        fake,
        (IPE, 2019),
        get=CvmDownload(200, "gen-1-ipe-2019", cvm_url(IPE, 2019), b"nao e zip"),
    )

    with pytest.raises(DisclosuresImportFailed) as caught:
        run_import_disclosures(fake, now=clock(NOW_2025))

    assert "ipe 2019: FALHOU (BadZipFile: File is not a zip file)" in lines(
        caught.value.report
    )
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "ipe 2019"
    (bad,) = CvmFile.objects.filter(kind=IPE, year=2019)
    assert (bad.http_status, bad.content_sha256, bad.payload) == (200, None, None)


def test_rf02_mesmo_conteudo_com_outro_last_modified_e_inalterado() -> None:
    fake = first_load(NOW_2025, PETROBRAS)
    regenerated = redated(ipe(2025))
    serve_changed(fake, NOW_2025, {2025: regenerated})

    report = run_import_disclosures(fake, now=clock(NOW_2025))

    assert f"ipe 2025: baixado, {len(regenerated)} bytes, inalterado" in lines(report)
    assert year_prefixes(report, "ano") == []
    rows = list(CvmFile.objects.filter(kind=IPE, year=2025).order_by("pk"))
    assert len(rows) == 2
    assert rows[0].payload is not None
    assert rows[1].payload is None
    assert rows[0].content_sha256 == rows[1].content_sha256 is not None


# RF-04


def test_rf04_mesmo_protocolo_e_versao_com_dois_links_sao_duas_linhas() -> None:
    first_load(NOW_2025, PETROBRAS, ITAU)

    for pair in (PETROBRAS_PAIR, ITAU_PAIR):
        rows = list(Disclosure.objects.filter(link__in=pair))
        assert len(rows) == 2, pair
        assert rows[0].protocol == rows[1].protocol
        assert rows[0].version == rows[1].version


def test_rf04_reconformar_igual_nao_cria_nem_atualiza_nem_remove() -> None:
    first_load(NOW_2026, *NINE)
    (first,) = runs()
    before = {
        row.link: (row.run_id, row.updated_at) for row in Disclosure.objects.all()
    }
    assert len(before) > 0

    report = run_import_disclosures(FakeCvm({}, {}), reconform=[], now=clock(LATER))

    text = lines(report)
    assert (
        "ano 2025: 9 companhias, 0 criados, 0 atualizados, 0 removidos, 0 falhos"
        in text
    )
    assert (
        "ano 2026: 9 companhias, 0 criados, 0 atualizados, 0 removidos, 0 falhos"
        in text
    )
    after = {row.link: (row.run_id, row.updated_at) for row in Disclosure.objects.all()}
    assert after == before
    assert {run_id for run_id, _ in after.values()} == {first.pk}
    assert {updated_at for _, updated_at in after.values()} == {NOW_2026}


def test_rf04_nao_cria_silver_company_e_o_m31_segue_vendo_a_companhia_nova() -> None:
    before = Company.objects.count()

    first_load(NOW_2026, *NINE)

    assert Disclosure.objects.exists()
    assert Company.objects.count() == before


# RF-04a


def test_rf04a_versao_superada_por_reapresentacao_e_removida() -> None:
    v2 = row_of(2025, PETROBRAS_V2)
    v1 = PETROBRAS_V2.replace("numVersao=2", "numVersao=1")
    # declarado: a coleta 1 traz a mesma entrega na versao 1 (link e `Versao`)
    first = edited(2025, set_on_link(PETROBRAS_V2, Link_Download=v1, Versao="1"))
    add_stock(PETROBRAS)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {(IPE, 2025): first}, kinds=(IPE,))
    run_import_disclosures(fake, now=clock(NOW_2025))
    assert v1 in links_of(PETROBRAS, 2025)

    serve_changed(fake, NOW_2025, {2025: ipe(2025)})
    report = run_import_disclosures(fake, now=clock(NOW_2025))

    (row,) = Disclosure.objects.filter(protocol=v2["Protocolo_Entrega"])
    assert (row.link, row.version) == (PETROBRAS_V2, 2)
    assert (
        "ano 2025: 1 companhias, 1 criados, 0 atualizados, 1 removidos, 0 falhos"
        in lines(report)
    )


def test_rf04a_companhia_que_some_do_zip_perde_as_linhas_do_ano() -> None:
    fake = first_load(NOW_2026, PETROBRAS, VALE)
    vale_2025 = links_of(VALE, 2025)
    assert len(vale_2025) == 5
    petrobras_2025 = links_of(PETROBRAS, 2025)

    # declarado: o zip de 2025 sem nenhuma linha da Vale
    serve_changed(fake, NOW_2026, {2025: edited(2025, without_code(VALE))})
    report = run_import_disclosures(fake, now=clock(NOW_2026))

    assert links_of(VALE, 2025) == set()
    assert len(links_of(VALE, 2026)) == 5  # o outro ano nao e tocado
    assert links_of(PETROBRAS, 2025) == petrobras_2025
    assert (
        "ano 2025: 2 companhias, 0 criados, 0 atualizados, 5 removidos, 0 falhos"
        in lines(report)
    )


def test_rf04a_link_que_vai_para_categoria_de_fora_e_removido() -> None:
    fake = first_load(NOW_2025, PETROBRAS, VALE)
    assert VALE_FACT in links_of(VALE, 2025)

    # declarado: o fato relevante da Vale passa a "Assembleia", categoria de fora
    changed = edited(2025, set_on_link(VALE_FACT, Categoria="Assembleia"))
    serve_changed(fake, NOW_2025, {2025: changed})
    report = run_import_disclosures(fake, now=clock(NOW_2025))

    assert not Disclosure.objects.filter(link=VALE_FACT).exists()
    assert len(links_of(VALE, 2025)) == 4
    assert (
        "ano 2025: 2 companhias, 0 criados, 0 atualizados, 1 removidos, 0 falhos"
        in lines(report)
    )


def moved_link(link: str, source: str, target: str) -> None:
    """O link `link` passa de `source` para `target` no zip de 2025 (declarado: so o
    `Codigo_CVM` da linha muda) → uma linha, na nova, contada em `atualizados`."""
    assert source != target
    fake = first_load(NOW_2025, PETROBRAS, VALE)
    (before,) = Disclosure.objects.filter(link=link)
    assert before.code_cvm == source

    changed = edited(2025, set_on_link(link, Codigo_CVM=target))
    serve_changed(fake, NOW_2025, {2025: changed})
    report = run_import_disclosures(fake, now=clock(NOW_2025))  # nao levanta

    (row,) = Disclosure.objects.filter(link=link)
    assert row.code_cvm == target
    assert row.run_id == runs()[-1].pk
    assert (
        "ano 2025: 2 companhias, 0 criados, 1 atualizados, 0 removidos, 0 falhos"
        in lines(report)
    )


def test_rf04a_link_que_passa_da_que_ordena_primeiro_para_a_seguinte() -> None:
    # "4170" < "9512": a companhia de origem e conformada antes da de destino
    moved_link(VALE_FACT, VALE, PETROBRAS)


def test_rf04a_link_que_passa_da_que_ordena_depois_para_a_primeira() -> None:
    # a de destino, "4170", e conformada antes da de origem, "9512"
    moved_link(PETROBRAS_FACT, PETROBRAS, VALE)


def test_rf04a_companhia_que_saiu_do_catalogo_nao_e_tocada() -> None:
    fake = first_load(NOW_2025, PETROBRAS, VALE)
    vale_2025 = links_of(VALE, 2025)
    Asset.objects.filter(code_cvm=VALE).delete()

    # declarado: o zip de 2025 sem a Vale; ela ja nao esta no catalogo
    serve_changed(fake, NOW_2025, {2025: edited(2025, without_code(VALE))})
    report = run_import_disclosures(fake, now=clock(NOW_2025))

    assert links_of(VALE, 2025) == vale_2025
    assert (
        "ano 2025: 1 companhias, 0 criados, 0 atualizados, 0 removidos, 0 falhos"
        in lines(report)
    )


# RF-07


def test_rf07_escrita_falha_numa_companhia_reverte_so_ela(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for code in (PETROBRAS, VALE, ITAU):
        add_stock(code)
    real = disclosures_importer.write_disclosure_company_year
    attempts: list[tuple[str, int]] = []

    def vale_breaks(
        code_cvm: str,
        year: int,
        conformed: list[ConformedDisclosure],
        year_links: frozenset[str],
        run: CollectionRun,
        now: datetime,
    ) -> DisclosureCounts:
        attempts.append((code_cvm, year))
        counts = real(code_cvm, year, conformed, year_links, run, now)
        if code_cvm == VALE:  # pela companhia, nao pela ordem das chamadas
            assert Disclosure.objects.filter(code_cvm=VALE).exists()
            raise RuntimeError("falha depois de gravar")
        return counts

    monkeypatch.setattr(
        "apps.fundamentals.disclosures_importer.write_disclosure_company_year",
        vale_breaks,
    )
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {(IPE, 2025): ipe(2025)}, kinds=(IPE,))

    with pytest.raises(DisclosuresImportFailed) as caught:
        run_import_disclosures(fake, now=clock(NOW_2025))

    assert not Disclosure.objects.filter(code_cvm=VALE).exists()
    assert len(links_of(PETROBRAS, 2025)) == 7
    assert len(links_of(ITAU, 2025)) == 5
    text = lines(caught.value.report)
    assert "ano 2025: FALHOU 4170 (RuntimeError: falha depois de gravar)" in text
    assert (
        "ano 2025: 2 companhias, 12 criados, 0 atualizados, 0 removidos, 1 falhos"
        in text
    )
    assert attempts.count((VALE, 2025)) == 1
    (run,) = runs()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "ano 2025 4170"


def test_rf07_link_repetido_divergente_falha_so_a_companhia() -> None:
    """RF-04b pela escrita: o conflito e falha daquela (companhia, ano), com o link."""
    fake = first_load(NOW_2025, PETROBRAS, VALE)
    vale_2025 = links_of(VALE, 2025)

    def repeat_with_other_subject(header: Fields, rows: list[Fields]) -> list[Fields]:
        where = header.index("Link_Download")
        out: list[Fields] = []
        for row in rows:
            out.append(row)
            if row[where] == VALE_FACT:
                copy = list(row)
                copy[header.index("Assunto")] = "outro assunto"
                out.append(copy)
        return out

    # declarado: a linha do fato da Vale repetida logo abaixo dela, com outro `Assunto`
    serve_changed(fake, NOW_2025, {2025: edited(2025, repeat_with_other_subject)})
    report = importing(fake, NOW_2025)

    assert (
        f"ano 2025: FALHOU 4170 (ValueError: link repetido com campos diferentes: "
        f"{VALE_FACT})" in lines(report)
    )
    assert links_of(VALE, 2025) == vale_2025  # nada removido nem gravado
    assert runs()[-1].error == "ano 2025 4170"


# RF-07b


def test_rf07b_a_so_o_ano_alterado_e_conformado() -> None:
    fake = first_load(NOW_2026, PETROBRAS)

    # declarado: o zip de 2025 sem as linhas da Vale, fora do catalogo — conteudo novo
    serve_changed(fake, NOW_2026, {2025: edited(2025, without_code(VALE))})
    report = run_import_disclosures(fake, now=clock(NOW_2026))

    assert year_prefixes(report, "ano") == ["ano 2025"]
    assert year_prefixes(report, "novas") == []


def test_rf07b_b_companhia_nova_com_tudo_nao_modificado() -> None:
    fake = first_load(NOW_2026, PETROBRAS)
    (first,) = runs()
    add_stock(VALE, "VALE3")  # entra no catalogo depois da carga

    serve_changed(fake, NOW_2026, {})
    mark = len(fake.calls)
    report = run_import_disclosures(fake, now=clock(NOW_2026))

    assert gets(fake.calls[mark:]) == []
    assert year_prefixes(report, "ano") == []
    assert year_prefixes(report, "novas") == [f"novas {y}" for y in range(2016, 2027)]
    text = lines(report)
    for year in (2025, 2026):
        assert (
            f"novas {year}: 1 companhias, 5 criados, 0 atualizados, 0 removidos, "
            "0 falhos" in text
        )
    second = runs()[-1]
    assert set(
        Disclosure.objects.filter(run=second).values_list("code_cvm", flat=True)
    ) == {VALE}
    assert set(
        Disclosure.objects.filter(code_cvm=PETROBRAS).values_list("run_id", flat=True)
    ) == {first.pk}


def test_rf07b_a_e_b_na_mesma_coleta() -> None:
    fake = first_load(NOW_2026, PETROBRAS)
    add_stock(VALE, "VALE3")  # documentos no ano alterado (2026) e em outro (2025)

    # declarado: o zip de 2026 sem as linhas de 26190, fora do catalogo — conteudo novo
    serve_changed(fake, NOW_2026, {2026: edited(2026, without_code(OUTSIDE_CODE))})
    report = run_import_disclosures(fake, now=clock(NOW_2026))

    assert year_prefixes(report, "ano") == ["ano 2026"]
    assert year_prefixes(report, "novas") == [f"novas {y}" for y in range(2016, 2026)]
    text = lines(report)
    assert (
        "ano 2026: 2 companhias, 5 criados, 0 atualizados, 0 removidos, 0 falhos"
        in text
    )
    assert (
        "novas 2025: 1 companhias, 5 criados, 0 atualizados, 0 removidos, 0 falhos"
        in text
    )
    assert len(links_of(VALE, 2026)) == 5
    assert len(links_of(VALE, 2025)) == 5


# RF-08


def test_rf08_reconform_conforma_da_bronze_sem_chamar_a_cvm() -> None:
    first_load(NOW_2026, PETROBRAS)

    every = FakeCvm({}, {})
    report = run_import_disclosures(every, reconform=[], now=clock(LATER))
    assert every.calls == []
    assert year_prefixes(report, "ano") == [f"ano {y}" for y in range(2016, 2027)]
    assert not any(line.startswith(("ipe ", "coleta:")) for line in lines(report))

    one = FakeCvm({}, {})
    report = run_import_disclosures(one, reconform=[2025], now=clock(LATER))
    assert one.calls == []
    assert lines(report) == [
        "ano 2025: 1 companhias, 0 criados, 0 atualizados, 0 removidos, 0 falhos"
    ]


def test_rf08_full_baixa_todos() -> None:
    fake = first_load(NOW_2025)
    serve_changed(fake, NOW_2025, {})
    mark = len(fake.calls)

    report = run_import_disclosures(fake, full=True, now=clock(NOW_2025))

    assert len(gets(fake.calls[mark:])) == 10
    assert lines(report)[-1] == (
        "coleta: 10 arquivos, 0 novos, 10 inalterados, 0 nao modificados, "
        "0 ausentes, 0 falhos"
    )


def test_rf08_full_e_reconform_juntos_levantam_antes_de_tudo() -> None:
    fake = FakeCvm({}, {})

    with pytest.raises(ValueError, match="mutuamente exclusivos"):
        run_import_disclosures(fake, full=True, reconform=[], now=clock(NOW_2025))

    assert fake.calls == []
    assert runs() == []


# RF-09

FILE_LINE = re.compile(
    r"ipe \d{4}: (baixado, \d+ bytes, (novo|inalterado)|nao modificado|ausente"
    r"|FALHOU \(.+\))"
)
YEAR_LINE = re.compile(
    r"(ano|novas) \d{4}: (\d+ companhias, \d+ criados, \d+ atualizados, "
    r"\d+ removidos, \d+ falhos|\d+ registros mal formados descartados"
    r"|FALHOU \d+ \(.+\)|FALHOU \(.+\))"
)
COLLECTION_LINE = re.compile(
    r"coleta: \d+ arquivos, \d+ novos, \d+ inalterados, \d+ nao modificados, "
    r"\d+ ausentes, \d+ falhos"
)


def test_rf09_relatorio_ancorado_nos_rotulos(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = first_load(NOW_2026, PETROBRAS, VALE, ITAU)
    real = disclosures_importer.write_disclosure_company_year

    def vale_breaks(
        code_cvm: str,
        year: int,
        conformed: list[ConformedDisclosure],
        year_links: frozenset[str],
        run: CollectionRun,
        now: datetime,
    ) -> DisclosureCounts:
        if code_cvm == VALE:
            raise RuntimeError("quebrou")
        return real(code_cvm, year, conformed, year_links, run, now)

    monkeypatch.setattr(
        "apps.fundamentals.disclosures_importer.write_disclosure_company_year",
        vale_breaks,
    )

    def one_broken_record(header: Fields, rows: list[Fields]) -> list[Fields]:
        return [*rows, [*rows[0], "campo a mais"]]

    # declarado: 2016 com o mesmo conteudo e outras datas de membro (inalterado); 2025
    # com um registro de campo a mais no fim (novo); 2026 com 404 no HEAD (ausente)
    inalterado = redated(empty_ipe_zip(2016))
    novo = edited(2025, one_broken_record)
    serve_changed(fake, NOW_2026, {2016: inalterado, 2025: novo})
    replace_last(fake, (IPE, 2026), head=CvmHead(404, None))

    report = importing(fake, NOW_2026)

    text = lines(report)
    for line in text:
        assert any(
            p.fullmatch(line) for p in (FILE_LINE, YEAR_LINE, COLLECTION_LINE)
        ), line
    assert text == [
        f"ipe 2016: baixado, {len(inalterado)} bytes, inalterado",
        *(f"ipe {y}: nao modificado" for y in range(2017, 2025)),
        f"ipe 2025: baixado, {len(novo)} bytes, novo",
        "ipe 2026: ausente",
        "ano 2025: 2 companhias, 0 criados, 0 atualizados, 0 removidos, 1 falhos",
        "ano 2025: 1 registros mal formados descartados",
        "ano 2025: FALHOU 4170 (RuntimeError: quebrou)",
        "coleta: 11 arquivos, 1 novos, 1 inalterados, 8 nao modificados, "
        "1 ausentes, 0 falhos",
    ]
    assert runs()[-1].error == "ano 2025 4170"


def test_rf09_falha_do_ano_inteiro() -> None:
    add_stock(PETROBRAS)
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {}, kinds=(IPE,))
    # declarado: o zip de 2025 e um zip valido com o membro de 2024 — a leitura levanta
    replace_last(
        fake,
        (IPE, 2025),
        get=CvmDownload(200, "gen-1-ipe-2025", cvm_url(IPE, 2025), empty_ipe_zip(2024)),
    )

    report = importing(fake, NOW_2025)

    (line,) = [t for t in lines(report) if t.startswith("ano 2025: ")]
    assert line.startswith("ano 2025: FALHOU (KeyError: ")
    assert YEAR_LINE.fullmatch(line)
    assert report.failures() == ["ano 2025"]
    assert runs()[-1].status == CollectionRun.Status.FAILED
