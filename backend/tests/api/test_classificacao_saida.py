"""V-07 e a parte do V-05 do M1.7: a classificacao da B3 corrigida na saida da API (RF-06, RF-08).

A API troca o texto da B3 pelo da tabela da D-144 em todo campo de classificacao que publica
-- `sector` no item da busca; `sector`, `subsector` e `segment` na identidade; os `group_*`
dos pares no `/fundamentals` -- e so na saida: `silver.asset` e `gold.peer_comparison`
continuam com o texto da B3 depois da leitura.

As fixtures tem texto com ponto **em cada campo**, e um texto diferente em cada um, para que
o campo esquecido (ou trocado por outro) apareca. O `QQMQ3` carrega o "Maq. e Equip.", que
fica como veio, e um `name` igual a um texto da tabela: o nome nao passa pela funcao.

Os tickers sao inventados e comecam por `QQ`, para nao casar com o IBOV da migration de
dados.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client
from rest_framework.test import APIClient

from apps.api.serializers import CLASSIFICATION_DESCRIPTION
from apps.assets.models import Asset
from apps.fundamentals.models import PeerComparison
from tests.api.test_fundamentos import _balanco, _comparacao, _indicador

pytestmark = pytest.mark.django_db

AGORA = datetime(2026, 9, 25, 13, 0, tzinfo=ZoneInfo("UTC"))

# o que o RF-06 manda a descricao dizer
REGRA = "corrigido pela tabela"

# os textos da B3, um diferente em cada campo, e o que a API devolve
SETOR_B3 = "Petróleo. Gás e Biocombustíveis"
SETOR = "Petróleo, Gás e Biocombustíveis"
SUBSETOR_B3 = "Serv.Méd.Hospit..Análises e Diagnósticos"
SUBSETOR = "Serv.Méd.Hospit., Análises e Diagnósticos"
SEGMENTO_B3 = "Exploração. Refino e Distribuição"
SEGMENTO = "Exploração, Refino e Distribuição"

GRUPO_SETOR_B3 = "Tecidos. Vestuário e Calçados"
GRUPO_SETOR = "Tecidos, Vestuário e Calçados"
GRUPO_SUBSETOR_B3 = "Motores . Compressores e Outros"
GRUPO_SUBSETOR = "Motores, Compressores e Outros"
GRUPO_SEGMENTO_B3 = "Exploração. Refino e Distribuição"
GRUPO_SEGMENTO = "Exploração, Refino e Distribuição"

FICA = "Máq. e Equip. Industriais"


def _ativo(ticker: str, **extra: Any) -> Asset:
    valores: dict[str, Any] = {
        "name": f"Companhia {ticker}",
        "trading_name": ticker,
        "sector": SETOR_B3,
        "subsector": SUBSETOR_B3,
        "segment": SEGMENTO_B3,
        "listing_segment": "NM",
    }
    valores.update(extra)
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        code_cvm="9512",
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
        **valores,
    )


def _silver(ticker: str) -> dict[str, Any]:
    return dict(
        Asset.objects.filter(ticker=ticker)
        .values("name", "sector", "subsector", "segment", "listing_segment")
        .get()
    )


def _pares_gravados(ticker: str) -> dict[str, Any]:
    return dict(
        PeerComparison.objects.filter(asset__ticker=ticker)
        .values("group_sector", "group_subsector", "group_segment")
        .get()
    )


def _json(client: Client, url: str, **params: Any) -> dict[str, Any]:
    resposta = client.get(url, params)
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    return corpo


# --- V-07: a busca --------------------------------------------------------------------


def test_v07_a_busca_devolve_o_setor_corrigido(client: Client) -> None:
    _ativo("QQCL3")
    antes = _silver("QQCL3")

    corpo = _json(client, "/api/v1/assets", q="QQCL3")

    assert [item["ticker"] for item in corpo["results"]] == ["QQCL3"]
    assert corpo["results"][0]["sector"] == SETOR
    assert _silver("QQCL3") == antes
    assert antes["sector"] == SETOR_B3


def test_v07_a_busca_deixa_o_ponto_de_abreviacao_e_o_nome(client: Client) -> None:
    _ativo("QQMQ3", sector=FICA, name=SETOR_B3)

    item = _json(client, "/api/v1/assets", q="QQMQ3")["results"][0]

    assert item["sector"] == FICA
    assert item["name"] == SETOR_B3  # o nome nao passa pela funcao


def test_v07_a_busca_com_setor_nulo(client: Client) -> None:
    _ativo("QQNU3", sector=None)

    item = _json(client, "/api/v1/assets", q="QQNU3")["results"][0]

    assert item["sector"] is None


# --- V-07: a identidade ---------------------------------------------------------------


def test_v07_a_identidade_devolve_os_tres_campos_corrigidos(client: Client) -> None:
    _ativo("QQCL3")
    antes = _silver("QQCL3")

    corpo = _json(client, "/api/v1/assets/qqcl3")

    assert corpo["sector"] == SETOR
    assert corpo["subsector"] == SUBSETOR
    assert corpo["segment"] == SEGMENTO
    assert corpo["listing_segment"] == "NM"
    assert _silver("QQCL3") == antes
    assert (antes["sector"], antes["subsector"], antes["segment"]) == (
        SETOR_B3,
        SUBSETOR_B3,
        SEGMENTO_B3,
    )


def test_v07_a_identidade_deixa_o_ponto_de_abreviacao_o_nulo_e_o_nome(
    client: Client,
) -> None:
    _ativo("QQMQ3", name=SETOR_B3, subsector=None, segment=FICA)

    corpo = _json(client, "/api/v1/assets/qqmq3")

    assert corpo["name"] == SETOR_B3
    assert corpo["sector"] == SETOR
    assert corpo["subsector"] is None
    assert corpo["segment"] == FICA


# --- V-07: os pares do /fundamentals ----------------------------------------------------


def test_v07_os_pares_devolvem_os_tres_grupos_corrigidos(client: Client) -> None:
    ativo = _ativo("QQCL3")
    indicador = _indicador(ativo, AGORA, _balanco(date(2026, 6, 30)))
    _comparacao(
        indicador,
        group_sector=GRUPO_SETOR_B3,
        group_subsector=GRUPO_SUBSETOR_B3,
        group_segment=GRUPO_SEGMENTO_B3,
    )
    antes = _pares_gravados("QQCL3")

    pares = _json(client, "/api/v1/assets/qqcl3/fundamentals")["peers"]

    assert pares["group_sector"] == GRUPO_SETOR
    assert pares["group_subsector"] == GRUPO_SUBSETOR
    assert pares["group_segment"] == GRUPO_SEGMENTO
    assert _pares_gravados("QQCL3") == antes
    assert antes == {
        "group_sector": GRUPO_SETOR_B3,
        "group_subsector": GRUPO_SUBSETOR_B3,
        "group_segment": GRUPO_SEGMENTO_B3,
    }


def test_v07_os_pares_deixam_o_ponto_de_abreviacao_e_o_nulo(client: Client) -> None:
    ativo = _ativo("QQMQ3")
    indicador = _indicador(ativo, AGORA, _balanco(date(2026, 6, 30)))
    _comparacao(
        indicador,
        peer_level="subsector",
        group_sector=GRUPO_SETOR_B3,
        group_subsector=FICA,
        group_segment=None,
    )

    pares = _json(client, "/api/v1/assets/qqmq3/fundamentals")["peers"]

    assert pares["group_sector"] == GRUPO_SETOR
    assert pares["group_subsector"] == FICA
    assert pares["group_segment"] is None


# --- V-05: o esquema ------------------------------------------------------------------


@pytest.fixture
def esquema() -> dict[str, Any]:
    resposta = APIClient().get("/api/v1/schema")
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    return corpo


CAMPOS_NO_ESQUEMA = [
    ("AssetItem", "sector"),
    ("AssetDetail", "sector"),
    ("AssetDetail", "subsector"),
    ("AssetDetail", "segment"),
    ("PeersOut", "group_sector"),
    ("PeersOut", "group_subsector"),
    ("PeersOut", "group_segment"),
]


@pytest.mark.parametrize(("componente", "campo"), CAMPOS_NO_ESQUEMA)
def test_v05_o_campo_de_classificacao_tem_a_descricao_e_o_tipo(
    esquema: dict[str, Any], componente: str, campo: str
) -> None:
    propriedade = esquema["components"]["schemas"][componente]["properties"][campo]

    # o tipo de antes do M1.7 -- `string`, anulavel, ate 120 --, agora com a descricao
    assert propriedade == {
        "type": "string",
        "nullable": True,
        "maxLength": 120,
        "description": CLASSIFICATION_DESCRIPTION,
    }
    assert REGRA in propriedade["description"]
    assert "D-144" in propriedade["description"]


def test_v05_listing_segment_nao_e_classificacao(esquema: dict[str, Any]) -> None:
    propriedade = esquema["components"]["schemas"]["AssetDetail"]["properties"][
        "listing_segment"
    ]

    assert "description" not in propriedade
