"""Os dois modelos de retorno do RF-04 (M5.1), em janela expansiva por trechos de 252.

Com `R = 252`, `full = concat(train, test)`, `n_train = len(train)`, `n = len(test)`: os
inicios de trecho sao `range(0, n + 1, R)`; o trecho que contem a posicao `p`
(`0 <= p <= n`) comeca em `(p // R) * R`, e os parametros do trecho que comeca em `s` sao
estimados com `full.iloc[: n_train + s]`. A posicao `n` -- o proximo pregao (RF-03a) -- nao
e caso especial: sai do mesmo laco; se `n % R == 0`, o trecho dela comeca nela e reestima
com tudo ate o `as_of_date`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from engine.returns.base import ReturnForecast, ReturnModel
from engine.returns.registry import register_return_model

#: a cadencia de reestimacao, a mesma dos modelos de VaR (D-158)
REFIT_FREQUENCY_DAYS = 252
R = REFIT_FREQUENCY_DAYS


def _chunk_starts(n: int) -> range:  # os inicios de trecho, inclusive o da posicao n
    return range(0, n + 1, R)  # n + 1: se n e multiplo de R, n abre um trecho


def _walk_forward(
    train: pd.Series,
    test: pd.Series,
    chunk_forecast: Callable[[pd.Series, np.ndarray], np.ndarray],
) -> ReturnForecast:
    """Monta as previsoes das posicoes `0..n` trecho a trecho.

    `chunk_forecast(known, previous)` recebe os retornos conhecidos no inicio do trecho
    (`full.iloc[: n_train + s]`) e, para cada posicao `p` do trecho, o retorno da vespera
    (`full.iloc[n_train + p - 1]`), e devolve a previsao de cada posicao.
    """
    full = pd.concat([train, test])
    values = full.to_numpy(dtype=float)
    n_train = len(train)
    n = len(test)
    out = np.empty(n + 1)
    for s in _chunk_starts(n):
        e = min(s + R, n + 1)
        known = full.iloc[: n_train + s]
        previous = values[n_train + s - 1 : n_train + e - 1]
        out[s:e] = chunk_forecast(known, previous)
    return ReturnForecast(
        series=pd.Series(out[:n], index=test.index),
        next_value=float(out[n]),
    )


def ar1_coefficients(known: pd.Series) -> tuple[float, float]:
    """`(c, phi)` por minimos quadrados ordinarios de `r(s)` sobre `1` e `r(s - 1)`, nos
    pares conhecidos."""
    r = known.to_numpy(dtype=float)
    y = r[1:]
    x = np.column_stack([np.ones(len(r) - 1), r[:-1]])
    (c, phi), *_ = np.linalg.lstsq(x, y, rcond=None)
    return float(c), float(phi)


@register_return_model("historical_mean")
class HistoricalMeanReturn(ReturnModel):
    """A previsao de cada dia e a media aritmetica dos retornos conhecidos no inicio do
    trecho."""

    @property
    def hyperparameters(self) -> dict[str, Any]:
        return {"refit_frequency_days": REFIT_FREQUENCY_DAYS, "window": "expanding"}

    def forecast(self, train: pd.Series, test: pd.Series) -> ReturnForecast:
        def chunk(known: pd.Series, previous: np.ndarray) -> np.ndarray:
            mu = float(known.mean())
            return np.full(len(previous), mu)

        return _walk_forward(train, test, chunk)


@register_return_model("ar_1")
class Ar1Return(ReturnModel):
    """A previsao do dia `t` e `c + phi * r(t - 1)`, com `(c, phi)` do inicio do trecho; o
    proximo pregao usa o retorno do `as_of_date`."""

    @property
    def hyperparameters(self) -> dict[str, Any]:
        return {
            "lags": 1,
            "intercept": True,
            "estimator": "ols",
            "refit_frequency_days": REFIT_FREQUENCY_DAYS,
            "window": "expanding",
        }

    def forecast(self, train: pd.Series, test: pd.Series) -> ReturnForecast:
        def chunk(known: pd.Series, previous: np.ndarray) -> np.ndarray:
            c, phi = ar1_coefficients(known)
            return c + phi * previous

        return _walk_forward(train, test, chunk)
