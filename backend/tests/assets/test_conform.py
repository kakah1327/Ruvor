"""A conformacao, provada sobre as fixtures reais da B3 (RF-05, RF-11 e casos de borda).

Nenhum teste aqui toca banco, cliente ou rede: `conform_company` recebe o item da
listagem e o detalhe como dicionarios, lidos de `tests/fixtures/b3/`.
"""

from __future__ import annotations

import pytest

from apps.assets.conform import (
    EQUITY_CODE,
    ConformedCompany,
    conform_company,
    is_company,
    provider_symbol,
    split_classification,
)
from tests.assets.conftest import fixture_json


def conform(issuer: str) -> ConformedCompany:
    return conform_company(
        fixture_json(f"listing_item_{issuer}"), fixture_json(f"detail_{issuer}")
    )


def tickers(company: ConformedCompany) -> list[str]:
    return [asset.ticker for asset in company.assets]


# --- RF-05: quais codigos viram acao -------------------------------------------------


def test_rf05_regex_e_o_contrato_literal() -> None:
    assert EQUITY_CODE.pattern == r"^[A-Z0-9]{4}(3|4|5|6|7|8|11)$"


@pytest.mark.parametrize(
    "code",
    ["PETR3", "PETR4", "BBAS11", "CSNA3", "B3SA3", "ABCD5", "ABCD6", "ABCD7", "ABCD8"],
)
def test_rf05_regex_aceita_acao_e_unit(code: str) -> None:
    assert EQUITY_CODE.match(code)


@pytest.mark.parametrize(
    "code",
    ["PETR-DEB62", "BBAS12", "PETR", "PETR1", "PETR2", "PETR9", "petr4", "ABCDE3"],
)
def test_rf05_regex_recusa_o_que_nao_e_acao(code: str) -> None:
    assert not EQUITY_CODE.match(code)


def test_rf05_petrobras_gera_petr3_e_petr4_sem_debenture() -> None:
    company = conform("PETR")
    assert tickers(company) == ["PETR3", "PETR4"]
    assert not company.empty_detail
    assert not company.quoted_without_code
    assert not company.odd_classification


def test_rf05_bbas_gera_bbas3_e_bbas11_sem_recibo_bbas12() -> None:
    company = conform("BBAS")
    assert sorted(tickers(company)) == ["BBAS11", "BBAS3"]
    assert "BBAS12" not in tickers(company)
    assert not company.quoted_without_code


def test_rf05_csna_gera_um_so_codigo() -> None:
    company = conform("CSNA")
    assert tickers(company) == ["CSNA3"]


def test_rf05_inel_sem_cotacao_nao_gera_acao_nem_flag() -> None:
    company = conform("INEL")
    assert company.assets == []
    assert not company.empty_detail
    assert not company.quoted_without_code
    assert not company.odd_classification


def test_rf05_zamp_com_cotacao_e_sem_codigo_conta_como_caso_de_borda() -> None:
    company = conform("ZAMP")
    assert company.assets == []
    assert company.quoted_without_code
    assert not company.empty_detail


def test_rf05_detalhe_vazio_conta_como_empty_detail() -> None:
    company = conform_company(
        fixture_json("listing_item_PETR"), fixture_json("detail_empty")
    )
    assert company.assets == []
    assert company.empty_detail
    assert not company.quoted_without_code
    assert not company.odd_classification


# --- As colunas conformadas ----------------------------------------------------------


def test_rf05_colunas_da_petr4_vem_do_detalhe_e_o_listing_segment_da_listagem() -> None:
    company = conform("PETR")
    petr4 = next(asset for asset in company.assets if asset.ticker == "PETR4")
    assert petr4.isin == "BRPETRACNPR6"
    assert petr4.name == "PETROLEO BRASILEIRO S.A. PETROBRAS"
    assert petr4.trading_name == "PETROBRAS"
    assert petr4.cnpj == "33000167000101"
    assert petr4.code_cvm == "9512"
    assert petr4.issuer_code == "PETR"
    assert petr4.listing_segment == "N2"
    assert petr4.provider_symbol == "PETR4.SA"


def test_rf05_classificacao_da_petrobras_dividida_em_tres_com_os_pontos_preservados() -> (
    None
):
    company = conform("PETR")
    petr3 = company.assets[0]
    assert petr3.sector == "Petróleo. Gás e Biocombustíveis"
    assert petr3.subsector == "Petróleo. Gás e Biocombustíveis"
    assert petr3.segment == "Exploração. Refino e Distribuição"
    assert not company.odd_classification


def test_rf05_market_vazio_na_listagem_vira_listing_segment_none() -> None:
    company = conform("CSNA")
    assert fixture_json("listing_item_CSNA")["market"] == ""
    assert company.assets[0].listing_segment is None


def test_rf05_cnpj_vem_do_detalhe_com_os_zeros_a_esquerda() -> None:
    # A listagem traz "191"; o detalhe, "00000000000191". A spec le o cnpj do detalhe.
    company = conform("BBAS")
    assert {asset.cnpj for asset in company.assets} == {"00000000000191"}


# --- is_company ----------------------------------------------------------------------


def test_rf04_is_company_so_aceita_type_1() -> None:
    assert is_company(fixture_json("listing_item_PETR"))
    page = fixture_json("listing_page_1")["results"]
    outros = [item for item in page if item["type"] != "1"]
    assert outros, "a pagina 1 deveria ter itens type != 1 para servir de reservatorio"
    assert not any(is_company(item) for item in outros)
    assert not is_company({})


# --- split_classification ------------------------------------------------------------


def test_split_classification_com_tres_partes() -> None:
    assert split_classification("Financeiro / Intermediários Financeiros / Bancos") == (
        "Financeiro",
        "Intermediários Financeiros",
        "Bancos",
        False,
    )


def test_split_classification_com_duas_partes_deixa_a_terceira_nula_e_marca() -> None:
    assert split_classification("Financeiro / Bancos") == (
        "Financeiro",
        "Bancos",
        None,
        True,
    )


def test_split_classification_com_uma_parte() -> None:
    assert split_classification("Financeiro") == ("Financeiro", None, None, True)


def test_split_classification_com_quatro_partes_reune_as_excedentes_na_terceira() -> (
    None
):
    assert split_classification("A / B / C / D") == ("A", "B", "C / D", True)


def test_split_classification_ausente() -> None:
    assert split_classification(None) == (None, None, None, True)
    assert split_classification("") == (None, None, None, True)


def test_split_classification_marca_odd_no_conform_company() -> None:
    detail = dict(fixture_json("detail_CSNA"))
    detail["industryClassification"] = "Materiais Básicos / Siderurgia"
    company = conform_company(fixture_json("listing_item_CSNA"), detail)
    assert company.odd_classification
    assert company.assets[0].segment is None


# --- RF-11: provider_symbol ----------------------------------------------------------


def test_rf11_provider_symbol_de_acao_e_ticker_ponto_sa() -> None:
    assert provider_symbol("PETR4", "stock") == "PETR4.SA"
    assert provider_symbol("BBAS11", "stock") == "BBAS11.SA"


def test_rf11_provider_symbol_do_ibovespa_e_bvsp() -> None:
    assert provider_symbol("IBOV", "index") == "^BVSP"


def test_rf11_provider_symbol_recusa_combinacao_desconhecida() -> None:
    with pytest.raises(ValueError):
        provider_symbol("XPTO", "index")
    with pytest.raises(ValueError):
        provider_symbol("PETR4", "bond")
