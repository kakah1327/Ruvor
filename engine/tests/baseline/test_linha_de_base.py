"""Compara o motor migrado contra a linha de base numerica congelada em `valores.json`.

O JSON foi capturado antes da migracao, contra o codigo do prototipo, e nao pode ser
regenerado: se a comparacao divergir, o defeito esta na migracao.

O caminho de execucao reproduz exatamente o da captura — chamada direta a `fit` sobre o
treino e `estimate_var` sobre o teste, com o mesmo alinhamento que
`engine/experiments/runner.py` faz antes dos backtests. `run_experiment` nao e usado
porque exige um provider de dados.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.backtesting import get_backtest, load_all_backtest_modules
from engine.models import get_model, load_all_model_modules

CAMINHO_JSON = Path(__file__).parent / "valores.json"
LINHA_DE_BASE = json.loads(CAMINHO_JSON.read_text(encoding="utf-8"))
PARAMETROS = LINHA_DE_BASE["parametros"]
ENTRADAS = LINHA_DE_BASE["entradas"]

TOLERANCIA_RELATIVA = 1e-6
PISO_ABSOLUTO = 1e-12


def _serie_completa() -> pd.Series:
    serie = PARAMETROS["serie"]
    rng = np.random.default_rng(serie["semente"])
    valores = rng.normal(serie["media"], serie["desvio"], serie["n_total"])
    indice = pd.bdate_range("2020-01-01", periods=serie["n_total"])
    return pd.Series(valores, index=indice)


@lru_cache(maxsize=None)
def _modelo_ajustado(nome: str):
    """Ajusta o modelo uma unica vez sobre o treino, como faz o runner."""
    load_all_model_modules()
    retornos = _serie_completa()
    treino = retornos.iloc[: PARAMETROS["divisao"]["treino"]]
    return get_model(nome)().fit(treino)


@lru_cache(maxsize=None)
def _resultado(nome: str, alpha: float) -> tuple[pd.Series, dict]:
    """Reproduz o par (serie de VaR, backtests) de uma combinacao."""
    load_all_backtest_modules()
    retornos = _serie_completa()
    teste = retornos.iloc[PARAMETROS["divisao"]["treino"] :]
    assert len(teste) == PARAMETROS["divisao"]["teste"]

    modelo = _modelo_ajustado(nome)
    estimativa = modelo.estimate_var(teste, alpha=alpha, horizon=PARAMETROS["horizon"])

    # mesmo alinhamento de engine/experiments/runner.py
    retornos_alinhados = teste.reindex(estimativa.var_series.index).dropna()
    var_series = estimativa.var_series.reindex(retornos_alinhados.index)

    backtests = {
        nome_bt: get_backtest(nome_bt)().run(retornos_alinhados, var_series, alpha)
        for nome_bt in PARAMETROS["backtests"]
    }
    return var_series, backtests


def _proximo(obtido: float, esperado: float) -> bool:
    return abs(obtido - esperado) <= max(
        TOLERANCIA_RELATIVA * abs(esperado), PISO_ABSOLUTO
    )


@pytest.mark.parametrize("chave", list(ENTRADAS))
def test_serie_de_var_reproduz_a_linha_de_base(chave: str) -> None:
    esperado = ENTRADAS[chave]
    var_series, _ = _resultado(esperado["modelo"], esperado["alpha"])

    assert len(var_series) == len(esperado["var"])
    divergencias = [
        f"indice {i}: esperado {e!r}, obtido {o!r}"
        for i, (e, o) in enumerate(zip(esperado["var"], var_series.tolist()))
        if not _proximo(o, e)
    ]
    assert not divergencias, f"{chave}: " + "; ".join(divergencias[:5])


@pytest.mark.parametrize("chave", list(ENTRADAS))
def test_backtests_reproduzem_a_linha_de_base(chave: str) -> None:
    esperado = ENTRADAS[chave]
    _, backtests = _resultado(esperado["modelo"], esperado["alpha"])

    assert sorted(backtests) == sorted(esperado["backtests"])
    for nome_bt, referencia in esperado["backtests"].items():
        obtido = backtests[nome_bt]
        assert _proximo(obtido.statistic, referencia["statistic"]), (
            f"{chave}/{nome_bt}.statistic: esperado {referencia['statistic']!r}, "
            f"obtido {obtido.statistic!r}"
        )
        assert (obtido.p_value is None) == (referencia["p_value"] is None), (
            f"{chave}/{nome_bt}.p_value: esperado {referencia['p_value']!r}, "
            f"obtido {obtido.p_value!r}"
        )
        if referencia["p_value"] is not None:
            assert _proximo(obtido.p_value, referencia["p_value"]), (
                f"{chave}/{nome_bt}.p_value: esperado {referencia['p_value']!r}, "
                f"obtido {obtido.p_value!r}"
            )
        assert obtido.passed == referencia["passed"], (
            f"{chave}/{nome_bt}.passed: esperado {referencia['passed']!r}, "
            f"obtido {obtido.passed!r}"
        )
