"""M2.2a, T2: o provedor da carteira (RF-07; V-04).

O quadro que `fetch` devolve e igual ao montado a mao com `pd.to_datetime`, o contrato do
`SilverPriceProvider`, e o motor calcula o mesmo VaR sobre o provedor e sobre um provedor de teste
que devolve o quadro montado a mao. So no `worker`: importa `pandas` e o motor.
"""

from __future__ import annotations

import math
from datetime import date

import pandas as pd
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, run_experiment
from engine.models import load_all_model_modules

from apps.portfolios.provider import PortfolioSeriesProvider
from apps.portfolios.series import PortfolioSeries
from apps.risk import config as risk_config
from tests.portfolios.dados import dias_uteis


def _serie(datas: list[date], indice: list[float]) -> PortfolioSeries:
    return PortfolioSeries(
        dates=tuple(datas),
        index=tuple(indice),
        sha256="0" * 64,
        price_run_id=1,
        coverage=(),
    )


def _quadro(datas: list[date], indice: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"close": indice},
        index=pd.DatetimeIndex(pd.to_datetime(datas), name="date"),
    )


def test_v04_fetch_devolve_o_quadro_com_as_bordas_inclusivas() -> None:
    datas = [date(2026, 3, d) for d in (2, 3, 5, 6, 9)]
    indice = [1.0, 1.01, 0.99, 1.02, 1.03]
    provedor = PortfolioSeriesProvider(_serie(datas, indice))

    quadro = provedor.fetch("ignorado", "2026-03-03", "2026-03-06")

    pd.testing.assert_frame_equal(quadro, _quadro(datas[1:4], indice[1:4]))
    assert quadro.index.name == "date"


def test_v04_fetch_ignora_o_ticker_e_devolve_tudo_na_janela_larga() -> None:
    datas = [date(2026, 3, d) for d in (2, 3, 5)]
    indice = [1.0, 1.01, 0.99]
    provedor = PortfolioSeriesProvider(_serie(datas, indice))

    pd.testing.assert_frame_equal(
        provedor.fetch("PETR4", "2000-01-01", "2100-01-01"), _quadro(datas, indice)
    )


def test_v04_fetch_fora_da_janela_devolve_quadro_vazio() -> None:
    provedor = PortfolioSeriesProvider(_serie([date(2026, 3, 2)], [1.0]))
    quadro = provedor.fetch("x", "2026-04-01", "2026-04-30")
    assert list(quadro.columns) == ["close"]
    assert quadro.empty


class _ProvedorAMao:
    def __init__(self, quadro: pd.DataFrame) -> None:
        self._quadro = quadro

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        return self._quadro


def test_v04_o_motor_da_o_mesmo_var_pelos_dois_provedores() -> None:
    load_all_model_modules()
    load_all_backtest_modules()
    datas = dias_uteis(date(2024, 1, 2), 520)
    # 520 pontos fabricados a mao: um indice com oscilacao e tendencia
    indice = [1.0]
    for k in range(1, 520):
        indice.append(indice[-1] * (1 + 0.012 * math.sin(k * 1.3) + 0.0004))
    configuracao = ExperimentConfig(
        ticker="x",
        start=datas[0].isoformat(),
        end=datas[-1].isoformat(),
        model_names=["historical"],
        backtest_names=list(risk_config.BACKTESTS),
        alphas=list(risk_config.ALPHAS),
        train_window_days=risk_config.TRAIN_WINDOW_DAYS,
        seed=risk_config.DEFAULT_SEED,
    )

    pela_carteira = run_experiment(
        configuracao, PortfolioSeriesProvider(_serie(datas, indice))
    )
    a_mao = run_experiment(configuracao, _ProvedorAMao(_quadro(datas, indice)))

    assert len(pela_carteira.runs) == len(a_mao.runs) == 2
    for nossa, deles in zip(pela_carteira.runs, a_mao.runs, strict=True):
        assert nossa.error is None
        assert nossa.alpha == deles.alpha
        assert nossa.estimate is not None
        assert deles.estimate is not None
        assert nossa.estimate.var_series.iloc[-1] == deles.estimate.var_series.iloc[-1]
