import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_returns() -> pd.Series:
    """Retornos sinteticos (ruido gaussiano) — suficiente para testar a interface de
    qualquer modelo/backtest, sem depender de rede (yfinance) nos testes."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=500)
    return pd.Series(rng.normal(0, 0.01, size=len(dates)), index=dates)
