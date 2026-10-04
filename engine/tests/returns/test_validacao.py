"""M5.1, T2 — V-04: as metricas e os testes da validacao (RF-07, RF-08).

Os casos pequenos sao escritos a mao; o DM, o CW, o PT e a variancia de Newey-West sao
conferidos contra uma implementacao **em laco puro** deste arquivo — listas do Python,
`math`, nenhum `numpy` vetorizado e nenhum `scipy` (`1 - Phi(x)` por `math.erfc`).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from engine.returns.evaluation import (
    ReturnEvaluation,
    evaluate,
    long_run_variance,
    newey_west_lag,
)

TOL = 1e-12

# --- a implementacao de referencia, em laco puro ---------------------------------------------


def _lag(n: int) -> int:
    return math.floor(4 * (n / 100) ** (2 / 9))


def _lrv(xs: list[float]) -> float:
    """Newey-West, Bartlett, serie centrada, divisor n em toda autocovariancia."""
    n = len(xs)
    media = 0.0
    for x in xs:
        media += x
    media /= n
    c = [x - media for x in xs]
    lag = _lag(n)
    v = 0.0
    for t in range(n):
        v += c[t] * c[t]
    v /= n
    for k in range(1, lag + 1):
        gk = 0.0
        for t in range(k, n):
            gk += c[t] * c[t - k]
        v += 2 * (1 - k / (lag + 1)) * gk / n
    return v


def _sf(x: float) -> float:
    return 0.5 * math.erfc(x / math.sqrt(2))


def _unilateral(xs: list[float]) -> tuple[float | None, float | None]:
    n = len(xs)
    v = _lrv(xs)
    if v <= 0:
        return None, None
    media = 0.0
    for x in xs:
        media += x
    media /= n
    estatistica = media / math.sqrt(v / n)
    return estatistica, _sf(estatistica)


def _referencia(r: list[float], y: list[float]) -> dict[str, float | int | None]:
    n = len(r)
    mse = 0.0
    mse_ref = 0.0
    d: list[float] = []
    f: list[float] = []
    for rt, yt in zip(r, y, strict=True):
        e = rt - yt
        mse += e * e
        mse_ref += rt * rt
        d.append(rt * rt - e * e)
        f.append(rt * rt - (e * e - yt * yt))
    mse /= n
    mse_ref /= n
    dm, dm_p = _unilateral(d)
    cw, cw_p = _unilateral(f)

    dias = 0
    altas = 0
    previstas = 0
    acertos = 0
    for rt, yt in zip(r, y, strict=True):
        if rt != 0 and yt != 0:
            dias += 1
            altas += rt > 0
            previstas += yt > 0
            acertos += (rt > 0) == (yt > 0)
    hit = up = fup = pt = pt_p = None
    if dias:
        hit, up, fup = acertos / dias, altas / dias, previstas / dias
        p_star = up * fup + (1 - up) * (1 - fup)
        var_p = p_star * (1 - p_star) / dias
        var_ps = (
            (2 * up - 1) ** 2 * fup * (1 - fup) / dias
            + (2 * fup - 1) ** 2 * up * (1 - up) / dias
            + 4 * up * fup * (1 - up) * (1 - fup) / dias**2
        )
        if fup not in (0.0, 1.0) and up not in (0.0, 1.0) and var_p - var_ps > 0:
            pt = (hit - p_star) / math.sqrt(var_p - var_ps)
            pt_p = _sf(pt)
    return {
        "mse": mse,
        "mse_reference": mse_ref,
        "r2_os": 1 - mse / mse_ref,
        "direction_days": dias,
        "hit_rate": hit,
        "up_share": up,
        "forecast_up_share": fup,
        "dm_statistic": dm,
        "dm_p_value": dm_p,
        "cw_statistic": cw,
        "cw_p_value": cw_p,
        "pt_statistic": pt,
        "pt_p_value": pt_p,
    }


def _serie(valores: list[float]) -> pd.Series:
    return pd.Series(valores, index=pd.bdate_range("2024-01-01", periods=len(valores)))


def _avaliar(r: list[float], y: list[float]) -> ReturnEvaluation:
    return evaluate(_serie(r), _serie(y))


def _confere_com_a_referencia(
    ev: ReturnEvaluation, r: list[float], y: list[float]
) -> None:
    ref = _referencia(r, y)
    for campo, esperado in ref.items():
        obtido = getattr(ev, campo)
        if esperado is None:
            assert obtido is None, campo
        else:
            assert obtido is not None, campo
            assert abs(obtido - esperado) <= TOL, (campo, obtido, esperado)


# o caso pequeno: seis dias, um de retorno zero (2) e um de previsao zero (1)
R6 = [0.01, -0.02, 0.0, 0.015, -0.005, 0.02]
Y6 = [0.005, 0.0, 0.01, -0.01, -0.002, 0.004]


# --- a defasagem e a variancia de longo prazo -------------------------------------------------


def test_a_defasagem_de_newey_west() -> None:
    assert newey_west_lag(2240) == 7
    assert newey_west_lag(250) == 4
    assert newey_west_lag(100) == 4
    assert newey_west_lag(6) == 2


def test_long_run_variance_centra_na_propria_media() -> None:
    x = np.random.default_rng(3).normal(0.0, 1.0, 40)
    assert abs(x.mean()) > 0.01  # a serie tem media nao nula
    deslocada = x + 5.0
    assert long_run_variance(deslocada) == pytest.approx(
        long_run_variance(x - x.mean()), rel=TOL, abs=0
    )
    assert long_run_variance(x) == pytest.approx(_lrv(list(x)), rel=TOL, abs=0)


def test_long_run_variance_contra_o_laco_com_divisor_n() -> None:
    # serie curta: o divisor n contra n - k muda o numero por k/n
    x = [0.3, -0.1, 0.4, 0.2, -0.5, 0.1, 0.25, -0.05]
    assert long_run_variance(np.array(x)) == pytest.approx(_lrv(x), rel=TOL, abs=0)


# --- o caso pequeno escrito a mao -------------------------------------------------------------


def test_as_metricas_do_caso_pequeno_a_mao() -> None:
    ev = _avaliar(R6, Y6)
    e = [0.005, -0.02, -0.01, 0.025, -0.003, 0.016]
    mse = (0.005**2 + 0.02**2 + 0.01**2 + 0.025**2 + 0.003**2 + 0.016**2) / 6
    mse_ref = (0.01**2 + 0.02**2 + 0.0 + 0.015**2 + 0.005**2 + 0.02**2) / 6
    assert [round(a - b, 15) for a, b in zip(R6, Y6, strict=True)] == e
    assert ev.mse == pytest.approx(mse, abs=TOL)
    assert ev.mse_reference == pytest.approx(mse_ref, abs=TOL)
    assert ev.r2_os == pytest.approx(1 - mse / mse_ref, abs=TOL)
    # sem o dia 1 (previsao zero) e sem o dia 2 (retorno zero): os dias 0, 3, 4 e 5
    assert ev.direction_days == 4
    assert ev.up_share == 3 / 4  # dias 0, 3 e 5 subiram
    assert ev.forecast_up_share == 2 / 4  # previu alta nos dias 0 e 5
    assert ev.hit_rate == 3 / 4  # acertou 0, 4 e 5; errou 3


def test_o_caso_pequeno_contra_o_laco() -> None:
    ev = _avaliar(R6, Y6)
    assert ev.dm_statistic is not None and ev.pt_statistic is not None
    _confere_com_a_referencia(ev, R6, Y6)


def test_o_p_e_unilateral() -> None:
    ev = _avaliar(R6, Y6)
    assert ev.dm_statistic is not None and ev.dm_p_value is not None
    assert ev.dm_p_value == pytest.approx(_sf(ev.dm_statistic), abs=TOL)
    assert ev.cw_p_value == pytest.approx(_sf(ev.cw_statistic), abs=TOL)
    assert ev.pt_p_value == pytest.approx(_sf(ev.pt_statistic), abs=TOL)


def _autocorrelacionado() -> tuple[list[float], list[float]]:
    """250 dias com volatilidade em grupos: `d(t)` carrega `r(t)^2`, autocorrelacionado."""
    rng = np.random.default_rng(11)
    r: list[float] = []
    sigma2 = 1e-4
    anterior = 0.0
    for _ in range(250):
        sigma2 = 2e-6 + 0.25 * anterior**2 + 0.73 * sigma2
        anterior = float(rng.normal(0.0, math.sqrt(sigma2)))
        r.append(anterior)
    y = [0.0005] + [0.3 * r[t - 1] for t in range(1, 250)]
    return r, y


def test_o_caso_autocorrelacionado_contra_o_laco() -> None:
    r, y = _autocorrelacionado()
    d = [rt * rt - (rt - yt) ** 2 for rt, yt in zip(r, y, strict=True)]
    # a trava: a correcao de Newey-West move V neste caso (L = 4), senao o teste nao mede
    so_gamma0 = sum((x - sum(d) / len(d)) ** 2 for x in d) / len(d)
    assert abs(_lrv(d) / so_gamma0 - 1) > 0.05
    _confere_com_a_referencia(_avaliar(r, y), r, y)


def test_o_cw_tem_o_termo_da_previsao_ao_quadrado() -> None:
    ev = _avaliar(R6, Y6)
    f = [rt * rt - ((rt - yt) ** 2 - yt * yt) for rt, yt in zip(R6, Y6, strict=True)]
    d = [rt * rt - (rt - yt) ** 2 for rt, yt in zip(R6, Y6, strict=True)]
    assert ev.cw_statistic == pytest.approx(_unilateral(f)[0], abs=TOL)
    assert ev.cw_statistic != pytest.approx(_unilateral(d)[0], abs=1e-6)


# --- os nulos do RF-08 ------------------------------------------------------------------------


def test_previsao_zero_todo_dia_anula_dm_cw_e_direcao() -> None:
    r = [0.01, -0.02, 0.003, 0.015, -0.005]
    ev = _avaliar(r, [0.0] * 5)
    # d identicamente zero: V = 0
    assert (ev.dm_statistic, ev.dm_p_value) == (None, None)
    assert (ev.cw_statistic, ev.cw_p_value) == (None, None)
    assert ev.direction_days == 0
    assert (ev.hit_rate, ev.up_share, ev.forecast_up_share) == (None, None, None)
    assert (ev.pt_statistic, ev.pt_p_value) == (None, None)
    assert ev.r2_os == 0.0


# sete dias, tres de um lado: o caso em que Var(P) - Var(P*) sai positivo por arredondamento
# (6,9e-18) com uma das parcelas em 0 -- sem a regra dos extremos, o PT viraria um numero
TRES_DE_SETE = [1, -1, 1, -1, -1, 1, -1]


@pytest.mark.parametrize(
    ("r", "y", "campo", "valor"),
    [
        # forecast_up_share 0 e 1
        ([0.01 * s for s in TRES_DE_SETE], [-0.002] * 7, "forecast_up_share", 0.0),
        ([0.01 * s for s in TRES_DE_SETE], [0.002] * 7, "forecast_up_share", 1.0),
        # up_share 0 e 1
        ([-0.01] * 7, [0.002 * s for s in TRES_DE_SETE], "up_share", 0.0),
        ([0.01] * 7, [0.002 * s for s in TRES_DE_SETE], "up_share", 1.0),
    ],
)
def test_direcao_constante_anula_o_pt(
    r: list[float], y: list[float], campo: str, valor: float
) -> None:
    ev = _avaliar(r, y)
    assert getattr(ev, campo) == valor
    assert ev.direction_days == 7
    assert (ev.pt_statistic, ev.pt_p_value) == (None, None)
    assert ev.hit_rate is not None


def test_previsao_desalinhada_levanta() -> None:
    with pytest.raises(ValueError):
        evaluate(_serie(R6), pd.Series(Y6))
