"""`run_import` contra a `FakeSource`: coleta, transacao e *upsert* (RF-02 a RF-13, RF-16).

Todo teste grava no banco de teste (`@pytest.mark.django_db`), dentro da transacao por
teste do pytest-django — o `transaction.atomic()` do `importer` vira *savepoint*, e o
`failed` gravado "fora da transacao revertida" fica na transacao do teste, que e o que se
inspeciona. O teste do `UNIQUE` (RF-06) abre o proprio `atomic()` para que o
`IntegrityError` nao invalide a transacao do teste.

Os cenarios sao compostos de respostas reais (spec, "Fixtures"): os cinco itens de listagem
capturados com os seus detalhes, mais itens da pagina 1 — os `type != "1"` nao geram
chamada; um `type == "1"` da pagina 1 (`2WAV`, `codeCVM` 25224) recebe o `{}` real, que e o
que a B3 devolve para companhia que nao encontra. Toda alteracao sobre uma fixture e
declarada no teste que a faz.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from django.db import IntegrityError, transaction

from apps.assets.importer import CollectionFailed, ImportReport, run_import
from apps.assets.models import Asset, B3CompanyDetail, B3CompanyListing, CollectionRun
from tests.assets.conftest import FakeSource, fixture_json

pytestmark = pytest.mark.django_db

CODE_CVM = {
    "PETR": "9512",
    "BBAS": "1023",
    "CSNA": "4030",
    "INEL": "27251",
    "ZAMP": "24317",
}
EMPTY_DETAIL_CODE_CVM = "25224"  # 2WAV, type == "1" na pagina 1; recebe o `{}` real
TICKERS_DO_CENARIO = ["BBAS11", "BBAS3", "CSNA3", "PETR3", "PETR4"]


def listing_item(issuer: str) -> dict[str, Any]:
    return fixture_json(f"listing_item_{issuer}")


def detail(issuer: str) -> dict[str, Any]:
    return fixture_json(f"detail_{issuer}")


def page_1_item(code_cvm: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = [
        item
        for item in fixture_json("listing_page_1")["results"]
        if item["codeCVM"] == code_cvm
    ]
    assert len(items) == 1, f"cenario mal montado: {code_cvm} nao esta na pagina 1"
    return items[0]


# Itens da pagina 1 que nao sao companhia (`type != "1"`): nao geram chamada de detalhe.
NON_COMPANY_CODES = {"900049": "7", "50110": "4", "519715": "6"}


def non_company_items() -> list[dict[str, Any]]:
    items = [page_1_item(code) for code in NON_COMPANY_CODES]
    assert [item["type"] for item in items] == list(NON_COMPANY_CODES.values())
    return items


def full_page() -> list[dict[str, Any]]:
    """Uma pagina com as cinco companhias, o `2WAV` e os tres nao-companhia, intercalados."""
    non_company = non_company_items()
    return [
        listing_item("PETR"),
        non_company[0],
        listing_item("BBAS"),
        listing_item("INEL"),
        non_company[1],
        listing_item("CSNA"),
        page_1_item(EMPTY_DETAIL_CODE_CVM),
        listing_item("ZAMP"),
        non_company[2],
    ]


def full_details() -> dict[str, dict[str, Any]]:
    details = {CODE_CVM[issuer]: detail(issuer) for issuer in CODE_CVM}
    details[EMPTY_DETAIL_CODE_CVM] = fixture_json("detail_empty")
    return details


def full_source(**kwargs: Any) -> FakeSource:
    return FakeSource([full_page()], full_details(), **kwargs)


def stock_rows(exclude: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    """As linhas `kind=stock`, por ticker, como dicionarios — para comparar antes e depois."""
    rows: list[dict[str, Any]] = [
        dict(row)
        for row in Asset.objects.filter(kind=Asset.Kind.STOCK)
        .order_by("ticker")
        .values()
    ]
    for row in rows:
        for column in exclude:
            del row[column]
    return rows


def ibov_row() -> dict[str, Any]:
    return dict(Asset.objects.filter(ticker="IBOV").values().get())


def last_run() -> CollectionRun:
    return CollectionRun.objects.order_by("-pk").first() or pytest.fail(
        "nenhuma collection_run"
    )


# --- RF-02: collection_run sempre, `failed` inclusive ---------------------------------


def test_rf02_coleta_ok_registra_a_collection_run() -> None:
    run_import(full_source())
    run = last_run()
    assert run.source == "b3-listed-companies"
    assert run.status == CollectionRun.Status.OK
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.error == ""


def test_rf02_fonte_que_falha_na_listagem_deixa_a_run_failed() -> None:
    source = FakeSource(
        [[listing_item("PETR")], [listing_item("CSNA")]],
        full_details(),
        fail_listing=True,
    )
    with pytest.raises(CollectionFailed, match=r"^B3ClientError: fonte falsa"):
        run_import(source)
    run = last_run()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error.startswith("B3ClientError: fonte falsa")
    assert run.finished_at is not None
    # a bronze fica com o que foi coletado ate a falha
    assert list(run.listings.values_list("code_cvm", flat=True)) == [CODE_CVM["PETR"]]


def test_rf02_conformacao_que_levanta_deixa_a_run_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def quebra(*args: object, **kwargs: object) -> Any:
        raise RuntimeError("conformacao quebrou")

    monkeypatch.setattr("apps.assets.importer.conform_company", quebra)
    with pytest.raises(CollectionFailed, match=r"^RuntimeError: conformacao quebrou$"):
        run_import(full_source())
    run = last_run()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "RuntimeError: conformacao quebrou"
    assert run.finished_at is not None
    assert stock_rows() == []


# --- RF-03: payload sem transformacao ---------------------------------------------------


def test_rf03_listagem_e_detalhe_vao_para_a_bronze_como_vieram() -> None:
    run_import(full_source())
    run = last_run()

    listings = {row.code_cvm: row for row in run.listings.all()}
    assert len(listings) == len(full_page())
    assert listings[CODE_CVM["PETR"]].payload == listing_item("PETR")
    assert listings[CODE_CVM["PETR"]].page_number == 1
    assert listings["900049"].payload == page_1_item(
        "900049"
    )  # type == "7" tambem fica

    details = {row.code_cvm: row for row in run.details.all()}
    assert details[CODE_CVM["PETR"]].payload == detail("PETR")
    assert (
        details[CODE_CVM["PETR"]].payload["otherCodes"] == detail("PETR")["otherCodes"]
    )
    assert details[CODE_CVM["ZAMP"]].payload == detail("ZAMP")


def test_rf03_detalhe_vazio_tambem_e_gravado() -> None:
    run_import(full_source())
    row = B3CompanyDetail.objects.get(run=last_run(), code_cvm=EMPTY_DETAIL_CODE_CVM)
    assert row.payload == {}


# --- RF-04: so type == "1" e consultado ---------------------------------------------


def test_rf04_so_companhias_type_1_geram_chamada_de_detalhe() -> None:
    page = full_page()
    assert any(item["type"] == "7" for item in page)  # sem ele a mutacao 6 passa
    source = full_source()
    run_import(source)
    expected = [item["codeCVM"] for item in page if item["type"] == "1"]
    assert source.calls == expected
    assert set(NON_COMPANY_CODES).isdisjoint(source.calls)
    assert set(B3CompanyDetail.objects.values_list("code_cvm", flat=True)) == set(
        expected
    )


# --- RF-05 e RF-06: uma linha por ticker, com as colunas, e UNIQUE no banco ----------


def test_rf06_uma_linha_por_ticker_com_as_colunas_conformadas() -> None:
    run_import(full_source())
    run = last_run()
    assert [row["ticker"] for row in stock_rows()] == TICKERS_DO_CENARIO

    petr4 = Asset.objects.get(ticker="PETR4")
    assert petr4.kind == Asset.Kind.STOCK
    assert petr4.isin == "BRPETRACNPR6"
    assert petr4.name == "PETROLEO BRASILEIRO S.A. PETROBRAS"
    assert petr4.trading_name == "PETROBRAS"
    assert petr4.cnpj == "33000167000101"
    assert petr4.code_cvm == "9512"
    assert petr4.issuer_code == "PETR"
    assert petr4.sector == "Petróleo. Gás e Biocombustíveis"
    assert petr4.subsector == "Petróleo. Gás e Biocombustíveis"
    assert petr4.segment == "Exploração. Refino e Distribuição"
    assert petr4.listing_segment == "N2"
    assert petr4.status == Asset.Status.ACTIVE
    assert petr4.provider_symbol == "PETR4.SA"
    assert petr4.first_seen_run == run
    assert petr4.last_seen_run == run
    assert petr4.created_at == petr4.updated_at

    csna3 = Asset.objects.get(ticker="CSNA3")
    assert csna3.listing_segment is None  # `market` vazio na listagem vira nulo


def test_rf06_ticker_e_unico_no_banco() -> None:
    run_import(full_source())
    petr4 = Asset.objects.get(ticker="PETR4")
    with pytest.raises(IntegrityError), transaction.atomic():
        Asset.objects.create(
            ticker="PETR4",
            kind=Asset.Kind.STOCK,
            name=petr4.name,
            trading_name=petr4.trading_name,
            provider_symbol=petr4.provider_symbol,
            created_at=petr4.created_at,
            updated_at=petr4.updated_at,
        )


# --- RF-07: segunda coleta igual so avanca last_seen_run --------------------------------


def test_rf07_segunda_coleta_igual_so_avanca_last_seen_run() -> None:
    run_import(full_source())
    first = last_run()
    before = stock_rows(exclude=("last_seen_run_id",))

    report = run_import(full_source())
    second = last_run()
    assert second.pk != first.pk

    assert stock_rows(exclude=("last_seen_run_id",)) == before
    active = Asset.objects.filter(kind=Asset.Kind.STOCK, status=Asset.Status.ACTIVE)
    assert active.count() == len(TICKERS_DO_CENARIO)
    assert all(asset.last_seen_run_id == second.pk for asset in active)
    assert all(asset.first_seen_run_id == first.pk for asset in active)
    assert ibov_row()["last_seen_run_id"] is None

    assert (report.created, report.updated, report.inactivated, report.reactivated) == (
        0,
        0,
        0,
        0,
    )


def test_rf07_coluna_conformada_que_muda_escreve_updated_at_e_conta_em_alteradas() -> (
    None
):
    run_import(full_source())
    before = {row["ticker"]: row for row in stock_rows()}

    # Alteracao declarada: o `tradingName` da Petrobras muda no detalhe.
    details = full_details()
    details[CODE_CVM["PETR"]] = {**detail("PETR"), "tradingName": "PETROBRAS NOVA"}
    report = run_import(FakeSource([full_page()], details))
    second = last_run()

    after = {row["ticker"]: row for row in stock_rows()}
    for ticker in ("PETR3", "PETR4"):
        assert after[ticker]["trading_name"] == "PETROBRAS NOVA"
        assert after[ticker]["updated_at"] > before[ticker]["updated_at"]
        assert after[ticker]["created_at"] == before[ticker]["created_at"]
        assert after[ticker]["last_seen_run_id"] == second.pk
    for ticker in ("BBAS3", "BBAS11", "CSNA3"):
        assert after[ticker]["updated_at"] == before[ticker]["updated_at"]
        assert after[ticker]["last_seen_run_id"] == second.pk
    assert (report.created, report.updated, report.inactivated, report.reactivated) == (
        0,
        2,
        0,
        0,
    )


# --- RF-08 e RF-09: ausente vira inactive, reaparece volta a active -------------------


def test_rf08_rf09_petr3_some_e_volta() -> None:
    run_import(full_source())
    first = last_run()
    petr3_before = Asset.objects.filter(ticker="PETR3").values().get()

    # Alteracao declarada: o detalhe de PETR sem o PETR3 em `otherCodes`.
    sem_petr3 = copy.deepcopy(detail("PETR"))
    sem_petr3["otherCodes"] = [
        code for code in sem_petr3["otherCodes"] if code["code"] != "PETR3"
    ]
    assert [code["code"] for code in sem_petr3["otherCodes"]] == ["PETR4", "PETR-DEB62"]
    details = full_details()
    details[CODE_CVM["PETR"]] = sem_petr3
    report2 = run_import(FakeSource([full_page()], details))
    second = last_run()

    petr3 = Asset.objects.get(ticker="PETR3")  # nunca e apagado
    assert petr3.status == Asset.Status.INACTIVE
    assert petr3.last_seen_run_id == first.pk  # a ultima coleta em que apareceu
    assert petr3.updated_at > petr3_before["updated_at"]
    assert Asset.objects.get(ticker="PETR4").last_seen_run_id == second.pk
    assert [row["ticker"] for row in stock_rows()] == TICKERS_DO_CENARIO
    assert (report2.conformed, report2.inactivated, report2.reactivated) == (4, 1, 0)

    report3 = run_import(full_source())
    third = last_run()
    petr3.refresh_from_db()
    assert petr3.status == Asset.Status.ACTIVE
    assert petr3.last_seen_run_id == third.pk
    assert petr3.first_seen_run_id == first.pk
    assert (
        report3.conformed,
        report3.updated,
        report3.inactivated,
        report3.reactivated,
    ) == (
        5,
        0,
        0,
        1,
    )


# --- RF-10: falha no detalhe nao toca na silver ----------------------------------------


def test_rf10_falha_no_detalhe_deixa_a_silver_como_estava() -> None:
    page = full_page()
    assert (
        page[0]["issuingCompany"] == "PETR"
    )  # uma companhia que produz acoes vem antes
    source = FakeSource([page], full_details(), fail_on=CODE_CVM["BBAS"])
    before = list(Asset.objects.order_by("ticker").values())
    assert [row["ticker"] for row in before] == ["IBOV"]

    with pytest.raises(
        CollectionFailed, match=r"^B3ClientError: fonte falsa: falha em 1023$"
    ):
        run_import(source)

    assert list(Asset.objects.order_by("ticker").values()) == before
    run = last_run()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error == "B3ClientError: fonte falsa: falha em 1023"
    assert source.calls == [CODE_CVM["PETR"], CODE_CVM["BBAS"]]
    # a bronze fica com o que foi coletado ate a falha: a listagem e o detalhe de PETR
    assert run.listings.count() == len(page)
    assert list(run.details.values_list("code_cvm", flat=True)) == [CODE_CVM["PETR"]]
    assert B3CompanyDetail.objects.get(
        run=run, code_cvm=CODE_CVM["PETR"]
    ).payload == detail("PETR")


# --- RF-12: o Ibovespa nao e lido nem escrito ------------------------------------------


def test_rf12_ibovespa_existe_e_a_coleta_o_preserva() -> None:
    before = ibov_row()
    assert before["kind"] == Asset.Kind.INDEX
    assert before["provider_symbol"] == "^BVSP"
    assert before["status"] == Asset.Status.ACTIVE

    run_import(full_source())
    assert ibov_row() == before  # inclusive updated_at e last_seen_run

    # tambem quando a coleta nao traz nada: `IBOV` nao esta no conformado e nao e inativado
    run_import(FakeSource([non_company_items()], {}))
    assert ibov_row() == before
    assert Asset.objects.filter(kind=Asset.Kind.INDEX).count() == 1


# --- RF-13: o relatorio --------------------------------------------------------------


def test_rf13_relatorio_com_os_rotulos_e_os_numeros_do_cenario() -> None:
    page = full_page()
    report = run_import(full_source())
    assert isinstance(report, ImportReport)
    assert report.render() == "\n".join(
        [
            f"listagem: {len(page)} companhias em 1 paginas",
            "consultadas (type=1): 6",
            "acoes conformadas: 5 (criadas 5, alteradas 0, inativadas 0, reativadas 0)",
            "casos de borda: detalhe vazio 1, hasQuotation=S sem codigo de acao 1, "
            "classificacao fora de tres partes 0",
        ]
    )
    assert len(page) == 9


def test_rf13_contagens_sao_disjuntas_entre_alteradas_inativadas_e_reativadas() -> None:
    run_import(full_source())

    # Coleta 2, alteracoes declaradas: PETR sem PETR3 e com `tradingName` novo — PETR4 muda
    # de coluna (alterada), PETR3 some (inativada); CSNA com classificacao de duas partes.
    petr = copy.deepcopy(detail("PETR"))
    petr["otherCodes"] = [c for c in petr["otherCodes"] if c["code"] != "PETR3"]
    petr["tradingName"] = "PETROBRAS NOVA"
    csna = {
        **detail("CSNA"),
        "industryClassification": "Materiais Básicos / Siderurgia",
    }
    details = {**full_details(), CODE_CVM["PETR"]: petr, CODE_CVM["CSNA"]: csna}
    report2 = run_import(FakeSource([full_page()], details))
    assert report2.render().splitlines()[2:] == [
        "acoes conformadas: 4 (criadas 0, alteradas 2, inativadas 1, reativadas 0)",
        "casos de borda: detalhe vazio 1, hasQuotation=S sem codigo de acao 1, "
        "classificacao fora de tres partes 1",
    ]

    # Coleta 3, de volta ao cenario completo: PETR3 reaparece com o `tradingName` original;
    # reativada conta so na sua, nao em alteradas. PETR4 e CSNA3 voltam: alteradas.
    report3 = run_import(full_source())
    assert report3.render().splitlines()[2] == (
        "acoes conformadas: 5 (criadas 0, alteradas 2, inativadas 0, reativadas 1)"
    )


# --- RF-16: um codigo em duas companhias e falha, antes de escrever --------------------


def test_rf16_codigo_repetido_entre_companhias_falha_sem_tocar_na_silver() -> None:
    # Alteracao declarada: o detalhe de CSNA recebe tambem o PETR4 em `otherCodes`.
    csna = copy.deepcopy(detail("CSNA"))
    csna["otherCodes"].append({"code": "PETR4", "isin": "BRPETRACNPR6"})
    details = {**full_details(), CODE_CVM["CSNA"]: csna}
    source = FakeSource([full_page()], details)

    with pytest.raises(CollectionFailed) as excinfo:
        run_import(source)
    assert "9512" in str(excinfo.value)
    assert "4030" in str(excinfo.value)

    run = last_run()
    assert run.status == CollectionRun.Status.FAILED
    assert run.error.startswith("CollectionFailed: ")
    assert "9512" in run.error
    assert "4030" in run.error
    assert stock_rows() == []
    assert Asset.objects.filter(
        ticker="IBOV"
    ).exists()  # a 0002 correu no banco de teste
    # a bronze ficou com a coleta inteira: a inconsistencia e da fonte, e fica registrada
    assert run.listings.count() == len(full_page())
    assert run.details.count() == 6
    assert B3CompanyListing.objects.filter(run=run).count() == run.listings.count()
