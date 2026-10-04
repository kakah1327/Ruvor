"""A validacao de um modelo de retorno contra a referencia zero (M5.1, RF-07 e RF-08).

Funcoes puras sobre o retorno realizado `r` e a previsao `y`: as metricas, o acerto de
direcao com a parcela de alta, e tres testes unilaterais -- Diebold-Mariano (perda
quadratica), Clark-West e Pesaran-Timmermann. O motor devolve estatistica e *p* em `float`
e nao decide nada: o nivel de significancia e o veredito moram no backend.

`V` e a variancia de longo prazo de Newey-West, nucleo de Bartlett, com defasagem
`L = floor(4 * (n / 100) ** (2 / 9))`, sobre a serie **centrada na propria media** e com
**divisor n** em toda autocovariancia.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm


@dataclass(frozen=True)
class ReturnEvaluation:
    mse: float
    mse_reference: float
    r2_os: float
    direction_days: int
    hit_rate: float | None
    up_share: float | None
    forecast_up_share: float | None
    dm_statistic: float | None
    dm_p_value: float | None
    cw_statistic: float | None
    cw_p_value: float | None
    pt_statistic: float | None
    pt_p_value: float | None


def newey_west_lag(n: int) -> int:
    return math.floor(4 * (n / 100) ** (2 / 9))  # 7 com n = 2240; 4 com n = 250


def long_run_variance(x: np.ndarray) -> float:
    n = len(x)
    c = x - x.mean()
    L = newey_west_lag(n)
    v = float(c @ c) / n  # gamma_0, divisor n
    for k in range(1, L + 1):
        v += 2 * (1 - k / (L + 1)) * float(c[k:] @ c[:-k]) / n  # divisor n, nao n - k
    return v


def _one_sided(x: np.ndarray) -> tuple[float | None, float | None]:
    """`mean(x) / sqrt(V / n)` e `1 - Phi` dela; os dois nulos com `V <= 0`."""
    n = len(x)
    v = long_run_variance(x)
    if v <= 0:
        return None, None
    statistic = float(x.mean()) / math.sqrt(v / n)
    return statistic, float(norm.sf(statistic))


def evaluate(realized: pd.Series, forecast: pd.Series) -> ReturnEvaluation:
    """As metricas e os testes do RF-07 e do RF-08 sobre os dias de `realized`.

    `forecast` tem de estar alinhada a `realized` (o mesmo indice).
    """
    if not realized.index.equals(forecast.index):
        raise ValueError("a previsao nao esta alinhada ao retorno realizado")
    r = realized.to_numpy(dtype=float)
    y = forecast.to_numpy(dtype=float)

    e = r - y
    mse = float(np.mean(e**2))
    mse_reference = float(np.mean(r**2))
    r2_os = 1 - mse / mse_reference

    # DM: d = r^2 - e^2; CW: f = r^2 - (e^2 - y^2)
    dm_statistic, dm_p_value = _one_sided(r**2 - e**2)
    cw_statistic, cw_p_value = _one_sided(r**2 - (e**2 - y**2))

    m = (r != 0) & (y != 0)
    direction_days = int(m.sum())
    hit_rate: float | None = None
    up_share: float | None = None
    forecast_up_share: float | None = None
    pt_statistic: float | None = None
    pt_p_value: float | None = None
    if direction_days > 0:
        up = r[m] > 0
        forecast_up = y[m] > 0
        p_y = float(np.mean(up))
        p_x = float(np.mean(forecast_up))
        P = float(np.mean(up == forecast_up))
        hit_rate, up_share, forecast_up_share = P, p_y, p_x

        N = direction_days
        p_star = p_y * p_x + (1 - p_y) * (1 - p_x)
        var_p = p_star * (1 - p_star) / N
        var_p_star = (
            (2 * p_y - 1) ** 2 * p_x * (1 - p_x) / N
            + (2 * p_x - 1) ** 2 * p_y * (1 - p_y) / N
            + 4 * p_y * p_x * (1 - p_y) * (1 - p_x) / N**2
        )
        if p_x not in (0.0, 1.0) and p_y not in (0.0, 1.0) and var_p - var_p_star > 0:
            pt_statistic = (P - p_star) / math.sqrt(var_p - var_p_star)
            pt_p_value = float(norm.sf(pt_statistic))

    return ReturnEvaluation(
        mse=mse,
        mse_reference=mse_reference,
        r2_os=r2_os,
        direction_days=direction_days,
        hit_rate=hit_rate,
        up_share=up_share,
        forecast_up_share=forecast_up_share,
        dm_statistic=dm_statistic,
        dm_p_value=dm_p_value,
        cw_statistic=cw_statistic,
        cw_p_value=cw_p_value,
        pt_statistic=pt_statistic,
        pt_p_value=pt_p_value,
    )
