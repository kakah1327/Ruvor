"""A identidade, a impressao digital e a gravacao dos retratos (M1.5b, T5).

Cobre V-07 (as duas metades, **por contagem**), V-08 (os seis componentes), V-09 (as duas
metades) e a borda `position == test_count`. A segunda metade do V-17 mora em
`tests/test_versoes_travadas.py`, que guarda a imagem.

Nada aqui roda o motor: os retratos sao fabricados com `pack_beta` sobre um `beta`
distinto por posicao, e comparados pelo que foi desempacotado -- os **bytes** do npz nao
sao deterministicos (o zip grava a hora). O modelo e o `caviar`, um dos quatro caros; os
hiperparametros saem do registry, que e carregado antes de cada teste.

As series sao sinteticas, diarias, com o `adj_close` em seis casas, como em
`test_compute.py`. Nenhum numero esperado vem do codigo sob teste: as posicoes esperadas
sao escritas a mao, e os indices alterados sao `252 + 252` e `252 + 253`, contados aqui.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from importlib.metadata import version
from typing import Any

import numpy as np
import pytest
from engine.models import load_all_model_modules
from engine.snapshots import Snapshot, pack_beta, unpack_beta

from apps.assets.models import Asset, CollectionRun, Price
from apps.risk.models import ModelSnapshot
from apps.risk.snapshots import (
    SnapshotKey,
    library_versions,
    load_valid,
    save,
)

pytestmark = pytest.mark.django_db

Q6 = Decimal("0.000001")
AGORA = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
ULTIMO_PREGAO = date(2026, 9, 18)

MODELO = "caviar"
ALPHA = 0.05
JANELA = 252

# 1 + 252 + 600: o periodo de teste tem 600 retornos, e cabem as posicoes 0, 252 e 504
PREGOES_TRES_PONTOS = 1 + JANELA + 600
# 1 + 252 + 504: o periodo de teste tem exatamente 504 retornos -- a borda
PREGOES_NA_BORDA = 1 + JANELA + 504


@pytest.fixture(autouse=True)
def registry() -> Iterator[None]:
    # `load_valid` e `save` leem os hiperparametros de `get_model(nome)()`
    load_all_model_modules()
    yield


def dias_uteis(quantidade: int, fim: date = ULTIMO_PREGAO) -> list[date]:
    datas: list[date] = []
    dia = fim
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    return sorted(datas)


def cria_ativo(ticker: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


def cria_serie(asset: Asset, quantidade: int, *, semente: int = 7) -> None:
    """`quantidade` pregoes, com log-retornos normais de desvio 1% a partir de 100."""
    rng = np.random.default_rng(semente)
    coleta = CollectionRun.objects.create(source="teste", started_at=AGORA)
    nivel = 100.0
    valores = [Decimal("100.000000")]
    for retorno in rng.normal(0, 0.01, quantidade - 1):
        nivel *= math.exp(float(retorno))
        valores.append(Decimal(str(nivel)).quantize(Q6))
    Price.objects.bulk_create(
        Price(
            asset=asset,
            date=dia,
            open=adj,
            high=adj,
            low=adj,
            close=adj,
            adj_close=adj,
            volume=1000,
            log_return=None,
            run=coleta,
            updated_at=AGORA,
        )
        for dia, adj in zip(dias_uteis(quantidade), valores, strict=True)
    )


def barras(asset: Asset) -> list[Price]:
    return list(Price.objects.filter(asset=asset).order_by("date"))


def com_serie(ticker: str, quantidade: int) -> tuple[Asset, list[Price]]:
    asset = cria_ativo(ticker)
    cria_serie(asset, quantidade)
    return asset, barras(asset)


def chave(asset: Asset, bars: list[Price], **troca: Any) -> SnapshotKey:
    campos: dict[str, Any] = {
        "asset": asset,
        "seed": 42,
        "engine_version": version("ruvor-engine"),
        "train_window_days": JANELA,
        "first_price_date": bars[0].date,
        "library_versions": library_versions(),
    }
    campos.update(troca)
    return SnapshotKey(**campos)


def beta_de(position: int, variante: float = 0.0) -> np.ndarray:
    return np.array([0.01, 0.9, 0.2], dtype=np.float64) + position + variante


def retrato(position: int, variante: float = 0.0) -> Snapshot:
    return Snapshot(position=position, payload=pack_beta(beta_de(position, variante)))


def posicoes(snaps: list[Snapshot]) -> list[int]:
    return [s.position for s in snaps]


def altera_sexta_casa(bars: list[Price], indice: int) -> None:
    """Soma um na sexta casa do `adj_close` do pregao `indice`, no banco."""
    preco = bars[indice]
    Price.objects.filter(pk=preco.pk).update(adj_close=preco.adj_close + Q6)


# --- V-07: a impressao digital estrita, por contagem ------------------------------------


def _tres_pontos(ticker: str) -> tuple[Asset, list[Price], SnapshotKey]:
    asset, bars = com_serie(ticker, PREGOES_TRES_PONTOS)
    key = chave(asset, bars)
    save(key, MODELO, ALPHA, bars, [retrato(0), retrato(252), retrato(504)])
    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0, 252, 504]
    return asset, bars, key


def test_v07_os_tres_pontos_voltam_com_o_payload_e_o_trained_through() -> None:
    asset, bars, key = _tres_pontos("AAA3")

    validos = load_valid(key, MODELO, ALPHA, bars)

    for snap in validos:
        np.testing.assert_array_equal(unpack_beta(snap.payload), beta_de(snap.position))
    gravados = dict(
        ModelSnapshot.objects.filter(asset=asset).values_list(
            "position", "trained_through"
        )
    )
    # o ultimo preco visto pelo ponto p e o de indice 252 + p
    assert gravados == {
        0: bars[252].date,
        252: bars[504].date,
        504: bars[756].date,
    }


def test_v07a_o_trained_through_de_252_alterado_invalida_252_e_os_seguintes() -> None:
    asset, bars, key = _tres_pontos("AAA3")

    altera_sexta_casa(bars, JANELA + 252)
    bars = barras(asset)

    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0]


def test_v07b_o_pregao_seguinte_ao_trained_through_de_252_preserva_252() -> None:
    asset, bars, key = _tres_pontos("AAA3")

    altera_sexta_casa(bars, JANELA + 253)
    bars = barras(asset)

    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0, 252]


# --- a borda: position == test_count -------------------------------------------------


def test_retrato_na_posicao_igual_a_test_count_nao_e_devolvido() -> None:
    """Com 504 retornos de teste, o retrato da posicao 504 -- gravado por uma rodada mais
    longa -- tem `trained_through` no ultimo pregao e impressao digital que bate, mas nao
    tem trecho nenhum para prever."""
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)
    save(key, MODELO, ALPHA, bars, [retrato(0), retrato(252), retrato(504)])
    assert ModelSnapshot.objects.filter(asset=asset).count() == 3

    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0, 252]


# --- V-08: cada componente da identidade -------------------------------------------------


def _fabricacoes(bars: list[Price]) -> dict[str, dict[str, Any]]:
    versoes = {**library_versions(), "numpy": "0.0.0"}
    return {
        "semente": {"seed": 43},
        "versao do motor": {"engine_version": "0.0.0"},
        "versoes de biblioteca": {
            "library_versions": versoes,
            "library_versions_hash": "f" * 64,
        },
        "hiperparametros": {
            "hyperparameters": {"refit_frequency_days": 252, "n_restarts": 11},
            "hyperparameters_hash": "e" * 64,
        },
        "janela": {"train_window_days": JANELA - 1},
        "primeiro pregao": {"first_price_date": bars[0].date - timedelta(days=1)},
    }


@pytest.mark.parametrize(
    "componente",
    [
        "semente",
        "versao do motor",
        "versoes de biblioteca",
        "hiperparametros",
        "janela",
        "primeiro pregao",
    ],
)
def test_v08_retrato_diferente_so_num_componente_nao_e_reaproveitado_e_o_novo_e_gravado(
    componente: str,
) -> None:
    """O fabricado nasce de uma gravacao com a identidade de agora e tem **um** campo
    trocado depois: e identico em tudo -- inclusive na impressao digital -- menos nele."""
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)
    save(key, MODELO, ALPHA, bars, [retrato(0, variante=0.5)])
    ModelSnapshot.objects.filter(asset=asset).update(**_fabricacoes(bars)[componente])

    assert load_valid(key, MODELO, ALPHA, bars) == []

    save(key, MODELO, ALPHA, bars, [retrato(0)])

    assert ModelSnapshot.objects.filter(asset=asset).count() == 2
    validos = load_valid(key, MODELO, ALPHA, bars)
    assert posicoes(validos) == [0]
    np.testing.assert_array_equal(unpack_beta(validos[0].payload), beta_de(0))


# --- V-09: imutavel e idempotente --------------------------------------------------------


def test_v09_gravar_o_mesmo_retrato_duas_vezes_da_uma_linha_sem_excecao() -> None:
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)
    snap = retrato(0)

    save(key, MODELO, ALPHA, bars, [snap])
    save(key, MODELO, ALPHA, bars, [snap])

    assert ModelSnapshot.objects.filter(asset=asset).count() == 1


def test_v09_mesma_identidade_com_outro_payload_fica_o_primeiro() -> None:
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)

    save(key, MODELO, ALPHA, bars, [retrato(0)])
    save(key, MODELO, ALPHA, bars, [retrato(0, variante=0.5)])

    linha = ModelSnapshot.objects.get(asset=asset)
    np.testing.assert_array_equal(unpack_beta(bytes(linha.payload)), beta_de(0))
