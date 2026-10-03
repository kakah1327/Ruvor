"""Janela expansiva dos tradicionais (M1.4b, RF-05 a RF-08): o VaR do teste por trechos de
`REFIT_FREQUENCY_DAYS` pregoes.

O trecho `k` cobre as posicoes de teste `[k * R, min((k + 1) * R, n_test))` e usa todos os
retornos conhecidos ate o seu inicio -- os de treino mais os do teste antes de `k * R` --; o
VaR e constante dentro do trecho. O trecho 0 usa so o treino: e o numero de antes da
correcao.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

#: a cadencia de reestimacao, a mesma do GARCH e do `caviar`
REFIT_FREQUENCY_DAYS = 252


def chunk_bounds(n_test: int) -> list[tuple[int, int]]:
    """Os limites `(inicio, fim)` dos trechos, em posicoes do teste, em ordem."""
    return [
        (start, min(start + REFIT_FREQUENCY_DAYS, n_test))
        for start in range(0, n_test, REFIT_FREQUENCY_DAYS)
    ]


def expanding_var_series(
    train: pd.Series, test: pd.Series, var_of: Callable[[pd.Series], float]
) -> pd.Series:
    """A serie de VaR alinhada a `test.index`: `var_of` recebe, para cada trecho, em ordem,
    os retornos conhecidos ate o inicio dele, e devolve o VaR do trecho inteiro."""
    full = pd.concat([train, test])
    n_train = len(train)
    values = np.empty(len(test))
    for start, end in chunk_bounds(len(test)):
        values[start:end] = var_of(full.iloc[: n_train + start])
    return pd.Series(values, index=test.index)
