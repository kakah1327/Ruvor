"""O `SilverPriceProvider` contra o banco: V-07 e V-08.

O **V-07** e o criterio central: os retornos que o motor calcula a partir do provedor batem
com `silver.price.log_return` com diferenca absoluta menor que 1e-9. E o que prova que a
coluna `close` entregue ao motor e o `adj_close`, e nao o `close` bruto.

Os `log_return` da serie estao **escritos literalmente** abaixo, com a formula do M1.2 no
comentario: nenhum deles e produzido pelo codigo sob teste, que aprovaria qualquer coisa.
A serie embute um desdobramento e um dividendo: `close` e `adj_close` divergem nas cinco
primeiras linhas e nas duas ultimas, e coincidem no meio. Com o `close` bruto no lugar do
ajustado, os retornos das bordas nao fecham — e o
`test_v07_o_close_bruto_nao_passaria_no_criterio` mostra isso medindo.

O **V-08** e uma varredura sobre os arquivos de `apps/risk/`: a fixture `sem_rede` de
`tests/conftest.py` troca `urllib.request.urlopen`, e o `yfinance` usa `requests` — passaria
por ela sem ser barrado.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from engine.data.preprocessing import fetch_returns

import apps.risk.provider as provider_module
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk.provider import SilverPriceProvider

pytestmark = pytest.mark.django_db

AGORA = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)

# (data, close, adj_close, log_return). O `log_return` e `ln(adj_t / adj_{t-1})` a dez
# casas decimais -- a conta do M1.2, `(current / previous).ln().quantize(Q10)` --,
# calculada fora deste arquivo e copiada para ca.
SERIE: list[tuple[date, str, str, str | None]] = [
    (date(2026, 1, 5), "62.940000", "31.470000", None),
    (date(2026, 1, 6), "64.290000", "32.145000", "0.0212222065"),
    (date(2026, 1, 7), "61.996000", "30.998000", "-0.0363342313"),
    (date(2026, 1, 8), "62.004000", "31.002000", "0.0001290323"),
    (date(2026, 1, 9), "67.752000", "33.876000", "0.0886550805"),
    (date(2026, 1, 12), "33.100000", "33.100000", "-0.0231735167"),
    (date(2026, 1, 13), "34.550000", "34.550000", "0.0428742678"),
    (date(2026, 1, 14), "34.549000", "34.549000", "-0.0000289440"),
    (date(2026, 1, 15), "29.870000", "29.870000", "-0.1455239740"),
    (date(2026, 1, 16), "35.123000", "35.123000", "0.1620015543"),
    (date(2026, 1, 19), "36.900000", "35.900000", "0.0218811090"),
    (date(2026, 1, 20), "34.951000", "34.001000", "-0.0543473595"),
]

PRIMEIRA = SERIE[0][0]
ULTIMA = SERIE[-1][0]


def cria_ativo(ticker: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"EMPRESA {ticker}",
        trading_name=ticker[:4],
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


def cria_serie(
    asset: Asset, serie: list[tuple[date, str, str, str | None]] | None = None
) -> None:
    run = CollectionRun.objects.create(source="teste", started_at=AGORA)
    for dia, close, adj_close, log_return in serie if serie is not None else SERIE:
        Price.objects.create(
            asset=asset,
            date=dia,
            open=Decimal(close),
            high=Decimal(close),
            low=Decimal(close),
            close=Decimal(close),
            adj_close=Decimal(adj_close),
            volume=1000,
            log_return=None if log_return is None else Decimal(log_return),
            run=run,
            updated_at=AGORA,
        )


# --- V-07: o `adj_close` na coluna `close` ---------------------------------------------


def test_fetch_devolve_o_adj_close_na_coluna_close() -> None:
    asset = cria_ativo("PETR4")
    cria_serie(asset)

    df = SilverPriceProvider().fetch("PETR4", PRIMEIRA.isoformat(), ULTIMA.isoformat())

    assert list(df.columns) == ["close"]
    assert len(df) == len(SERIE)
    assert df["close"].tolist() == [float(adj) for _, _, adj, _ in SERIE]
    # E nao o `close` bruto, que diverge nas cinco primeiras linhas.
    assert df["close"].tolist() != [float(close) for _, close, _, _ in SERIE]


def test_fetch_indexa_por_data_em_ordem_crescente() -> None:
    asset = cria_ativo("PETR4")
    cria_serie(asset)

    df = SilverPriceProvider().fetch("PETR4", PRIMEIRA.isoformat(), ULTIMA.isoformat())

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.name == "date"
    assert [d.date() for d in df.index] == [dia for dia, _, _, _ in SERIE]


def test_v07_retornos_do_motor_batem_com_o_log_return_da_silver() -> None:
    """V-07: diferenca absoluta < 1e-9 contra `silver.price.log_return`."""
    asset = cria_ativo("PETR4")
    cria_serie(asset)

    retornos = fetch_returns(
        SilverPriceProvider(), "PETR4", PRIMEIRA.isoformat(), ULTIMA.isoformat()
    )

    gravados = [
        (dia, float(Decimal(log_return)))
        for dia, _, _, log_return in SERIE
        if log_return is not None
    ]
    assert len(retornos) == len(gravados) == len(SERIE) - 1

    for (dia, esperado), (indice, obtido) in zip(
        gravados, retornos.items(), strict=True
    ):
        assert indice.date() == dia
        assert abs(obtido - esperado) < 1e-9, f"{dia}: {obtido} vs {esperado}"


def test_v07_o_close_bruto_nao_passaria_no_criterio() -> None:
    """A prova de que o V-07 sabe reprovar: o mesmo criterio sobre o `close` cru falha."""
    asset = cria_ativo("PETR4")
    cria_serie(asset)

    brutos = pd.Series(
        [float(close) for _, close, _, _ in SERIE],
        index=pd.DatetimeIndex([dia for dia, _, _, _ in SERIE]),
    )
    retornos_brutos = np.log(brutos / brutos.shift(1)).dropna()
    gravados = [
        float(Decimal(log_return))
        for _, _, _, log_return in SERIE
        if log_return is not None
    ]

    assert any(
        abs(obtido - esperado) >= 1e-9
        for obtido, esperado in zip(retornos_brutos, gravados, strict=True)
    )


# --- o provedor filtra pelo intervalo ---------------------------------------------------


def test_fetch_filtra_pelo_intervalo_com_as_duas_bordas_inclusivas() -> None:
    asset = cria_ativo("PETR4")
    cria_serie(asset)

    df = SilverPriceProvider().fetch("PETR4", "2026-01-07", "2026-01-13")

    assert [d.date() for d in df.index] == [
        date(2026, 1, 7),
        date(2026, 1, 8),
        date(2026, 1, 9),
        date(2026, 1, 12),
        date(2026, 1, 13),
    ]


def test_fetch_nao_traz_preco_de_outro_ativo() -> None:
    petr = cria_ativo("PETR4")
    vale = cria_ativo("VALE3")
    cria_serie(petr)
    cria_serie(vale, SERIE[:3])

    df = SilverPriceProvider().fetch("VALE3", PRIMEIRA.isoformat(), ULTIMA.isoformat())

    assert len(df) == 3


def test_fetch_de_ticker_sem_preco_devolve_quadro_vazio_com_a_coluna() -> None:
    cria_ativo("XPTO3")

    df = SilverPriceProvider().fetch("XPTO3", PRIMEIRA.isoformat(), ULTIMA.isoformat())

    assert df.empty
    assert list(df.columns) == ["close"]
    assert isinstance(df.index, pd.DatetimeIndex)


def test_fetch_de_ticker_inexistente_devolve_quadro_vazio() -> None:
    df = SilverPriceProvider().fetch(
        "NAOEXISTE", PRIMEIRA.isoformat(), ULTIMA.isoformat()
    )

    assert df.empty


# --- o contrato satisfeito estruturalmente ----------------------------------------------


def test_satisfaz_o_contrato_sem_herdar_de_data_provider() -> None:
    from engine.data.providers.base import DataProvider

    assert not issubclass(SilverPriceProvider, DataProvider)
    assert callable(SilverPriceProvider().fetch)


# --- V-08: nenhum caminho de rede em `apps/risk/` ---------------------------------------


def test_v08_nenhum_arquivo_de_apps_risk_toca_o_yfinance_provider() -> None:
    raiz = Path(provider_module.__file__).parent
    arquivos = [
        caminho for caminho in raiz.rglob("*.py") if "__pycache__" not in caminho.parts
    ]
    assert arquivos, f"varredura nao encontrou arquivo nenhum em {raiz}"

    culpados = [
        str(caminho.relative_to(raiz))
        for caminho in arquivos
        if "YFinanceProvider" in caminho.read_text(encoding="utf-8")
        or "yfinance" in caminho.read_text(encoding="utf-8")
    ]
    assert culpados == [], f"apps/risk/ referencia o yfinance em: {culpados}"
