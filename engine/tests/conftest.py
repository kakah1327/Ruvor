import numpy as np
import pandas as pd
import pytest


def serie_da_linha_de_base() -> pd.Series:
    """A serie de 552 pontos sobre a qual a linha de base numerica foi capturada —
    252 de treino e 300 de teste, os parametros de `baseline/valores.json`.

    E funcao importavel, e nao fixture, porque `baseline/test_linha_de_base.py` a consome
    de dentro de funcoes com `@cache`, de onde nao se chama fixture. O teste de determinismo
    da semente (V-03) usa a mesma serie.

    Nao confundir com a fixture `synthetic_returns`, que tem 500 pontos e outro proposito.
    """
    rng = np.random.default_rng(42)
    valores = rng.normal(0.0, 0.01, 552)
    return pd.Series(valores, index=pd.bdate_range("2020-01-01", periods=552))


@pytest.fixture
def synthetic_returns() -> pd.Series:
    """Retornos sinteticos (ruido gaussiano) — suficiente para testar a interface de
    qualquer modelo/backtest, sem depender de rede (yfinance) nos testes."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=500)
    return pd.Series(rng.normal(0, 0.01, size=len(dates)), index=dates)
