"""V-03: `GET /api/v1/assets/{ticker}/disclosures` (M1.6c, RF-03).

Os comunicados vem pela ligacao por valor da D-126, `silver.disclosure.code_cvm =
silver.asset.code_cvm`, **sem passar por `silver.company`**: a acao com comunicados e sem linha
la os devolve, com o nome do comunicado mais recente de qualquer categoria. A ordem e
`-delivered_on`, com desempate por `link`; os parametros sao validados antes do ativo; o indice
e a acao sem `code_cvm` dao 200 com `company: null`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client

from apps.assets.models import Asset, CollectionRun
from apps.fundamentals.models import Company, Disclosure

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

pytestmark = pytest.mark.django_db

AGORA = datetime(2026, 9, 28, 13, 0, tzinfo=ZoneInfo("UTC"))

CHAVES = ["ticker", "company", "count", "limit", "offset", "results"]
CHAVES_ITEM = [
    "delivered_on",
    "reference_date",
    "category",
    "kind",
    "species",
    "title",
    "link",
]

FATO = "fato_relevante"
COMUNICADO = "comunicado"
AVISO = "aviso_acionistas"


def _ok(resposta: _MonkeyPatchedWSGIResponse) -> dict[str, Any]:
    assert resposta.status_code == 200, resposta.content
    assert resposta["Content-Type"] == "application/json"
    corpo: dict[str, Any] = resposta.json()
    return corpo


def _coleta() -> CollectionRun:
    return CollectionRun.objects.create(
        source="teste", started_at=AGORA, status=CollectionRun.Status.OK
    )


def _ativo(ticker: str, code_cvm: str | None) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        code_cvm=code_cvm,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


def _companhia(code_cvm: str, name: str) -> Company:
    return Company.objects.create(
        code_cvm=code_cvm,
        cnpj="60872504000123",
        name=name,
        account_plan="bank",
        source_reference_date=date(2026, 6, 30),
        run=_coleta(),
        updated_at=AGORA,
    )


def _comunicado(
    code_cvm: str,
    link: str,
    delivered_on: date,
    category: str = FATO,
    company_name: str = "ITAÚ UNIBANCO HOLDING S.A.",
    reference_date: date | None = None,
) -> Disclosure:
    return Disclosure.objects.create(
        code_cvm=code_cvm,
        cnpj="60872504000123",
        company_name=company_name,
        year=delivered_on.year,
        link=link,
        protocol=f"p-{link}",
        version=1,
        presentation="AP",
        category=category,
        kind="Fato Relevante" if category == FATO else "",
        species="",
        title=f"Titulo {link}",
        reference_date=reference_date,
        delivered_on=delivered_on,
        run=_coleta(),
        updated_at=AGORA,
    )


def _links(corpo: dict[str, Any]) -> list[str]:
    return [item["link"] for item in corpo["results"]]


def _confere_400(resposta: _MonkeyPatchedWSGIResponse, parametro: str) -> None:
    assert resposta.status_code == 400, resposta.content
    erro = resposta.json()["error"]
    assert erro["code"] == "invalid_parameter"
    assert erro["details"] == {"parameter": parametro}
    assert erro["message"]


# --- o corpo e a ordem ------------------------------------------------------------------


def test_v03_o_corpo_inteiro(client: Client) -> None:
    _ativo("ITUB4", "19348")
    _companhia("19348", "ITAU UNIBANCO HOLDING S.A.")
    _comunicado(
        "19348",
        "https://cvm/a",
        date(2026, 9, 25),
        reference_date=date(2026, 9, 24),
    )

    corpo = _ok(client.get("/api/v1/assets/itub4/disclosures"))

    assert list(corpo) == CHAVES
    assert corpo["ticker"] == "ITUB4"
    # o nome e o de `silver.company`, nao o do comunicado
    assert corpo["company"] == {
        "code_cvm": "19348",
        "name": "ITAU UNIBANCO HOLDING S.A.",
    }
    assert corpo["count"] == 1
    assert corpo["limit"] == 10
    assert corpo["offset"] == 0
    (item,) = corpo["results"]
    assert list(item) == CHAVES_ITEM
    assert item == {
        "delivered_on": "2026-09-25",
        "reference_date": "2026-09-24",
        "category": FATO,
        "kind": "Fato Relevante",
        "species": "",
        "title": "Titulo https://cvm/a",
        "link": "https://cvm/a",
    }


def test_v03_a_ordem_e_estavel_por_data_e_link(client: Client) -> None:
    _ativo("ITUB4", "19348")
    # criados fora de ordem; tres na mesma data, desempatados pelo `link`
    _comunicado("19348", "https://cvm/c", date(2026, 9, 20))
    _comunicado("19348", "https://cvm/b", date(2026, 9, 20), category=AVISO)
    _comunicado("19348", "https://cvm/z", date(2026, 9, 1))
    _comunicado("19348", "https://cvm/y", date(2026, 9, 25), category=COMUNICADO)
    _comunicado("19348", "https://cvm/a", date(2026, 9, 20))
    # de outra companhia: nao entra
    _comunicado("906", "https://cvm/outra", date(2026, 9, 26))

    corpo = _ok(client.get("/api/v1/assets/ITUB4/disclosures"))

    assert corpo["count"] == 5
    assert _links(corpo) == [
        "https://cvm/y",
        "https://cvm/a",
        "https://cvm/b",
        "https://cvm/c",
        "https://cvm/z",
    ]


def test_v03_a_paginacao_e_o_count(client: Client) -> None:
    _ativo("ITUB4", "19348")
    for dia in range(1, 13):  # doze: passa do limite padrao de dez
        _comunicado("19348", f"https://cvm/{dia:02d}", date(2026, 9, dia))

    padrao = _ok(client.get("/api/v1/assets/ITUB4/disclosures"))
    assert padrao["count"] == 12
    assert len(padrao["results"]) == 10
    assert _links(padrao)[0] == "https://cvm/12"

    pagina = _ok(client.get("/api/v1/assets/ITUB4/disclosures?limit=3&offset=4"))
    assert (pagina["count"], pagina["limit"], pagina["offset"]) == (12, 3, 4)
    assert _links(pagina) == ["https://cvm/08", "https://cvm/07", "https://cvm/06"]

    alem = _ok(client.get("/api/v1/assets/ITUB4/disclosures?offset=50"))
    assert alem["count"] == 12
    assert alem["results"] == []

    tudo = _ok(client.get("/api/v1/assets/ITUB4/disclosures?limit=100"))
    assert len(tudo["results"]) == 12


def test_v03_o_filtro_por_categoria(client: Client) -> None:
    _ativo("ITUB4", "19348")
    _comunicado("19348", "https://cvm/f1", date(2026, 9, 20), category=FATO)
    _comunicado("19348", "https://cvm/c1", date(2026, 9, 21), category=COMUNICADO)
    _comunicado("19348", "https://cvm/a1", date(2026, 9, 22), category=AVISO)
    _comunicado("19348", "https://cvm/f2", date(2026, 9, 23), category=FATO)

    fatos = _ok(client.get(f"/api/v1/assets/ITUB4/disclosures?category={FATO}"))
    assert fatos["count"] == 2
    assert _links(fatos) == ["https://cvm/f2", "https://cvm/f1"]

    avisos = _ok(client.get(f"/api/v1/assets/ITUB4/disclosures?category={AVISO}"))
    assert (avisos["count"], _links(avisos)) == (1, ["https://cvm/a1"])

    # a categoria vazia e "todas", como o `q` vazio da busca
    todas = _ok(client.get("/api/v1/assets/ITUB4/disclosures?category="))
    assert todas["count"] == 4


# --- a ligacao por valor (D-126) e o nome --------------------------------------------------


def test_v03_acao_sem_silver_company_devolve_os_comunicados(client: Client) -> None:
    _ativo("NOVA3", "99999")
    assert not Company.objects.filter(code_cvm="99999").exists()
    _comunicado(
        "99999",
        "https://cvm/velho",
        date(2026, 8, 1),
        category=FATO,
        company_name="NOVA ANTIGA S.A.",
    )
    # o mais recente e um aviso: o nome sai dele mesmo com o filtro de fato relevante
    _comunicado(
        "99999",
        "https://cvm/novo",
        date(2026, 9, 1),
        category=AVISO,
        company_name="NOVA COMPANHIA S.A.",
    )

    corpo = _ok(client.get(f"/api/v1/assets/NOVA3/disclosures?category={FATO}"))

    assert corpo["company"] == {"code_cvm": "99999", "name": "NOVA COMPANHIA S.A."}
    assert corpo["count"] == 1
    assert _links(corpo) == ["https://cvm/velho"]

    todas = _ok(client.get("/api/v1/assets/NOVA3/disclosures"))
    assert _links(todas) == ["https://cvm/novo", "https://cvm/velho"]


def test_v03_com_code_cvm_e_sem_nada_o_nome_e_nulo(client: Client) -> None:
    _ativo("VAZI3", "77777")
    corpo = _ok(client.get("/api/v1/assets/VAZI3/disclosures"))
    assert corpo["company"] == {"code_cvm": "77777", "name": None}
    assert (corpo["count"], corpo["results"]) == (0, [])


# --- company nulo: identidade, nao erro ------------------------------------------------------


def test_v03_o_indice_da_200_com_company_nulo(client: Client) -> None:
    # o IBOV vem da migration do catalogo, sem `code_cvm`
    corpo = _ok(client.get(f"/api/v1/assets/IBOV/disclosures?category={FATO}"))
    assert corpo == {
        "ticker": "IBOV",
        "company": None,
        "count": 0,
        "limit": 10,
        "offset": 0,
        "results": [],
    }


def test_v03_acao_sem_code_cvm_da_200_com_company_nulo(client: Client) -> None:
    _ativo("SEMC3", None)
    corpo = _ok(client.get("/api/v1/assets/SEMC3/disclosures?limit=5&offset=2"))
    assert corpo == {
        "ticker": "SEMC3",
        "company": None,
        "count": 0,
        "limit": 5,
        "offset": 2,
        "results": [],
    }


# --- os parametros, antes do ativo -----------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "parametro"),
    [
        ("?category=noticia", "category"),
        ("?category=FATO_RELEVANTE", "category"),
        ("?limit=0", "limit"),
        ("?limit=101", "limit"),
        ("?limit=abc", "limit"),
        ("?limit=1.5", "limit"),
        ("?offset=-1", "offset"),
        ("?offset=x", "offset"),
    ],
)
@pytest.mark.parametrize("ticker", ["ITUB4", "ZZZZ9"])
def test_v03_parametro_invalido_e_400_antes_do_404(
    client: Client, debug: bool, query: str, parametro: str, ticker: str
) -> None:
    _ativo("ITUB4", "19348")
    _confere_400(client.get(f"/api/v1/assets/{ticker}/disclosures{query}"), parametro)


def test_v03_a_categoria_e_conferida_antes_do_limit(client: Client) -> None:
    _confere_400(
        client.get("/api/v1/assets/ZZZZ9/disclosures?category=x&limit=0"), "category"
    )


def test_v03_ticker_ausente_e_404(client: Client, debug: bool) -> None:
    resposta = client.get("/api/v1/assets/zzzz9/disclosures")
    assert resposta.status_code == 404
    assert resposta.json() == {
        "error": {
            "code": "asset_not_found",
            "message": "Ativo ZZZZ9 não existe.",
            "details": {"ticker": "ZZZZ9"},
        }
    }
