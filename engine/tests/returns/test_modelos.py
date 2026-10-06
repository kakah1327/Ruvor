"""M5.1, T1: os dois modelos de retorno (RF-03, RF-03a, RF-04) e o registry proprio.

V-02 — sem olhar a frente, por perturbacao, no molde de `tests/test_sem_olhar_a_frente.py`:
trocar os retornos de teste de `t` em diante nao muda a previsao de nenhum dia ate `t`, e
muda alguma depois (a trava contra o teste inerte). E o proximo pregao: acrescentar um
retorno qualquer ao fim do teste e recalcular da, no novo ultimo dia, o `next_value` de
antes — com `n` fora e **sobre** um multiplo de 252.

V-03 — contra oraculo independente: a media de cada trecho pela soma exata (`math.fsum`), os
coeficientes do AR(1) pelo `statsmodels.OLS`; parametros constantes dentro do trecho e
diferentes entre trechos numa serie de dois regimes; duas instancias novas dao os mesmos
bytes.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from itertools import pairwise

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from engine.models import list_models, load_all_model_modules
from engine.returns import (
    get_return_model,
    list_return_models,
    load_all_return_model_modules,
)
from engine.returns.base import ReturnModel
from engine.returns.models import Ar1Return, HistoricalMeanReturn, ar1_coefficients

N_TRAIN = 252
N_TEST = 756  # tres trechos de 252: n e multiplo de 252
R = 252
T_PERTURBACAO = (0, 251, 252, 400)
N_PROXIMO = (700, 756)  # fora e sobre um multiplo de 252
TOL_PERTURBACAO = 1e-15
TOL_OLS = 1e-12

_FABRICAS: dict[str, Callable[[], ReturnModel]] = {
    "historical_mean": HistoricalMeanReturn,
    "ar_1": Ar1Return,
}

_VAR_NOVE = {
    "parametric",
    "historical",
    "monte_carlo",
    "garch_1_1",
    "egarch",
    "caviar",
    "garchnet",
    "lstm",
    "gru",
}


def _dois_regimes(semente: int, n: int) -> np.ndarray:
    """AR(1) em torno de uma media, com media e autocorrelacao que mudam no meio."""
    rng = np.random.default_rng(semente)
    troca = n // 2
    valores = np.empty(n)
    anterior = 0.0
    for i in range(n):
        media, phi = (0.002, 0.35) if i < troca else (-0.0015, -0.25)
        valores[i] = media + phi * (anterior - media) + rng.normal(0.0, 0.01)
        anterior = valores[i]
    return valores


def _treino_teste(n_test: int = N_TEST, extra: int = 0) -> tuple[pd.Series, pd.Series]:
    """A mesma serie de dois regimes (semente 7), cortada em treino e teste."""
    valores = _dois_regimes(7, N_TRAIN + N_TEST + 1)[: N_TRAIN + n_test + extra]
    full = pd.Series(valores, index=pd.bdate_range("2015-01-01", periods=len(valores)))
    return full.iloc[:N_TRAIN], full.iloc[N_TRAIN:]


def _todas(model: ReturnModel, train: pd.Series, test: pd.Series) -> np.ndarray:
    """As previsoes das posicoes 0..n: a serie e o proximo pregao."""
    f = model.forecast(train, test)
    assert f.series.index.equals(test.index)
    return np.append(f.series.to_numpy(dtype=float), f.next_value)


def _inicios(n: int) -> list[int]:
    return list(range(0, n + 1, R))


def _posicoes(s: int, n: int) -> list[int]:
    return list(range(s, min(s + R, n + 1)))


# --- V-02: a perturbacao --------------------------------------------------------------------


@pytest.mark.parametrize("t", T_PERTURBACAO)
@pytest.mark.parametrize("nome", sorted(_FABRICAS))
def test_v02_trocar_o_teste_de_t_em_diante_nao_muda_a_previsao_ate_t(
    nome: str, t: int
) -> None:
    train, test = _treino_teste()
    outra = test.copy()
    outra.iloc[t:] = np.random.default_rng(99).normal(0.004, 0.03, len(test) - t)

    antes = _FABRICAS[nome]().forecast(train, test).series.to_numpy(dtype=float)
    depois = _FABRICAS[nome]().forecast(train, outra).series.to_numpy(dtype=float)

    assert np.max(np.abs(antes[: t + 1] - depois[: t + 1])) <= TOL_PERTURBACAO
    # a trava contra o teste inerte: a troca tem de mover alguma previsao depois de t
    assert np.any(antes[t + 1 :] != depois[t + 1 :])


@pytest.mark.parametrize("extra", [0.0, 0.07, -0.05])
@pytest.mark.parametrize("n", N_PROXIMO)
@pytest.mark.parametrize("nome", sorted(_FABRICAS))
def test_v02_o_proximo_pregao_e_o_novo_ultimo_dia_com_um_retorno_a_mais(
    nome: str, n: int, extra: float
) -> None:
    train, test_longo = _treino_teste(n_test=n, extra=1)
    test = test_longo.iloc[:n]
    acrescido = test_longo.copy()
    acrescido.iloc[-1] = extra  # um retorno qualquer depois do ultimo

    proximo = _FABRICAS[nome]().forecast(train, test).next_value
    novo_ultimo = _FABRICAS[nome]().forecast(train, acrescido).series.iloc[-1]

    assert len(acrescido) == n + 1
    assert abs(float(novo_ultimo) - proximo) <= TOL_PERTURBACAO


# --- V-03: os modelos contra oraculo ---------------------------------------------------------


@pytest.mark.parametrize("n", N_PROXIMO)
def test_v03_a_media_de_cada_trecho_e_a_dos_retornos_conhecidos_no_inicio(
    n: int,
) -> None:
    train, test = _treino_teste(n_test=n)
    full = pd.concat([train, test])
    previsto = _todas(HistoricalMeanReturn(), train, test)

    medias = []
    for s in _inicios(n):
        conhecidos = full.iloc[: N_TRAIN + s]
        oraculo = math.fsum(conhecidos.to_numpy(dtype=float)) / len(conhecidos)
        trecho = previsto[_posicoes(s, n)]
        assert np.all(trecho == trecho[0]), f"a media muda dentro do trecho {s}"
        assert abs(trecho[0] - oraculo) <= TOL_PERTURBACAO
        assert abs(trecho[0] - conhecidos.mean()) <= TOL_PERTURBACAO
        medias.append(trecho[0])
    # dois regimes: a media muda de um trecho para o seguinte
    assert all(a != b for a, b in pairwise(medias))


@pytest.mark.parametrize("n", N_PROXIMO)
def test_v03_o_ar1_de_cada_trecho_e_o_ols_do_statsmodels(n: int) -> None:
    train, test = _treino_teste(n_test=n)
    valores = pd.concat([train, test]).to_numpy(dtype=float)
    previsto = _todas(Ar1Return(), train, test)

    coeficientes = []
    for s in _inicios(n):
        conhecidos = valores[: N_TRAIN + s]
        c, phi = sm.OLS(conhecidos[1:], sm.add_constant(conhecidos[:-1])).fit().params
        posicoes = _posicoes(s, n)
        vespera = valores[[N_TRAIN + p - 1 for p in posicoes]]
        # cada posicao do trecho: c + phi * r(vespera), com (c, phi) fixos no trecho -- os
        # do OLS sobre os retornos conhecidos no inicio dele
        assert np.max(np.abs(previsto[posicoes] - (c + phi * vespera))) <= TOL_OLS
        coeficientes.append((c, phi))
    # dois regimes: os coeficientes mudam de um trecho para o seguinte
    assert all(a != b for a, b in pairwise(coeficientes))


@pytest.mark.parametrize("n", N_PROXIMO)
def test_v03_os_coeficientes_de_cada_trecho_batem_com_o_statsmodels(n: int) -> None:
    train, test = _treino_teste(n_test=n)
    full = pd.concat([train, test])
    for s in _inicios(n):
        conhecidos = full.iloc[: N_TRAIN + s]
        x = conhecidos.to_numpy(dtype=float)
        esperado = sm.OLS(x[1:], sm.add_constant(x[:-1])).fit().params
        obtido = np.array(ar1_coefficients(conhecidos))
        assert np.max(np.abs(obtido - esperado)) <= TOL_OLS


@pytest.mark.parametrize("nome", sorted(_FABRICAS))
def test_v03_duas_instancias_novas_dao_os_mesmos_bytes(nome: str) -> None:
    train, test = _treino_teste()
    a = _FABRICAS[nome]().forecast(train, test)
    b = _FABRICAS[nome]().forecast(train, test)
    assert np.array_equal(a.series.to_numpy(), b.series.to_numpy())
    assert a.next_value == b.next_value


# --- os hiperparametros do RF-04 e o registry -----------------------------------------------


def test_os_hiperparametros_do_rf04() -> None:
    assert HistoricalMeanReturn().hyperparameters == {
        "refit_frequency_days": 252,
        "window": "expanding",
    }
    assert Ar1Return().hyperparameters == {
        "lags": 1,
        "intercept": True,
        "estimator": "ols",
        "refit_frequency_days": 252,
        "window": "expanding",
    }


def test_o_registry_de_retorno_e_separado_do_de_var() -> None:
    load_all_model_modules()
    load_all_return_model_modules()
    assert list_return_models() == ["ar_1", "historical_mean"]
    assert set(list_models()) == _VAR_NOVE
    assert len(list_models()) == 9
    assert get_return_model("ar_1") is Ar1Return
    assert get_return_model("historical_mean") is HistoricalMeanReturn
    with pytest.raises(KeyError):
        get_return_model("historical")
