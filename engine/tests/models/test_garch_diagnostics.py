"""Diagnosticos estatisticos dos modelos de volatilidade condicional (GARCH, EGARCH):
como nem todo ambiente de execucao tem R disponivel, a verificacao cruzada com o pacote
rugarch (ver tools/garch_rcheck/) e feita a parte, manualmente — estes testes cobrem os
mesmos criterios de "resultados esperados" da Etapa 2 que dao pra automatizar sem R:
parametros convergentes e residuos padronizados bem distribuidos.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.diagnostic import acorr_ljungbox

from engine.models.garch.egarch import EgarchVaR
from engine.models.garch.garch_1_1 import Garch11VaR


@pytest.fixture
def garch_returns() -> pd.Series:
    """Simula um processo GARCH(1,1) de verdade (volatility clustering genuino), para os
    diagnosticos terem algo real pra detectar — ao contrario do ruido branco puro de
    `synthetic_returns` (conftest.py)."""
    rng = np.random.default_rng(42)
    n = 1000
    omega, alpha, beta = 1e-6, 0.1, 0.85
    sigma2 = omega / (1 - alpha - beta)
    returns = np.empty(n)
    prev_return = 0.0
    for t in range(n):
        sigma2 = omega + alpha * prev_return**2 + beta * sigma2
        returns[t] = rng.normal(0, np.sqrt(sigma2))
        prev_return = returns[t]

    dates = pd.bdate_range("2015-01-01", periods=n)
    return pd.Series(returns, index=dates)


@pytest.mark.parametrize("model_cls", [Garch11VaR, EgarchVaR])
def test_converges_and_residuals_are_well_behaved(model_cls, garch_returns):
    model = model_cls().fit(garch_returns)

    assert model.result_.convergence_flag == 0

    std_resid = model.result_.std_resid.dropna()
    assert std_resid.std() == pytest.approx(1.0, abs=0.2)

    ljung_box = acorr_ljungbox(std_resid**2, lags=[10], return_df=True)
    assert ljung_box["lb_pvalue"].iloc[0] > 0.01
