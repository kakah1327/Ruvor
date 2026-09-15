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


# --- ajuste que nao converge: o SLSQP do arch devolve `code 4` a partir do ponto de
# partida padrao em Linux (medido em 2026-09-15 sobre a serie da linha de base) e o
# modelo tenta de novo a partir de `_fallback_starting_values`. Ver D-46.


class _FakeResult:
    def __init__(self, convergence_flag: int) -> None:
        self.convergence_flag = convergence_flag


class _FakeArchModel:
    """`fit` sem `starting_values` nao converge; com eles, converge — ou nunca."""

    def __init__(self, converges_on_retry: bool) -> None:
        self.converges_on_retry = converges_on_retry
        self.calls: list[object] = []

    def fit(self, disp="off", starting_values=None):
        self.calls.append(starting_values)
        if starting_values is None:
            return _FakeResult(4)
        return _FakeResult(0 if self.converges_on_retry else 9)


@pytest.mark.parametrize("model_cls", [Garch11VaR, EgarchVaR])
def test_fit_retries_from_fallback_when_default_does_not_converge(
    model_cls, garch_returns, monkeypatch
):
    fake = _FakeArchModel(converges_on_retry=True)
    monkeypatch.setattr(
        "engine.models.garch._conditional.arch_model", lambda *a, **k: fake
    )

    with pytest.warns(UserWarning, match="valores iniciais alternativos"):
        model = model_cls().fit(garch_returns)

    assert model.result_.convergence_flag == 0
    assert fake.calls[0] is None  # primeiro o ponto padrao do arch
    assert len(fake.calls) == 2  # depois o primeiro fallback, que bastou
    assert (
        list(fake.calls[1])
        == model._fallback_starting_values((garch_returns * 100).var())[0]
    )


@pytest.mark.parametrize("model_cls", [Garch11VaR, EgarchVaR])
def test_fit_raises_when_no_starting_point_converges(
    model_cls, garch_returns, monkeypatch
):
    fake = _FakeArchModel(converges_on_retry=False)
    monkeypatch.setattr(
        "engine.models.garch._conditional.arch_model", lambda *a, **k: fake
    )

    with pytest.raises(RuntimeError, match="nao convergiu"):
        model_cls().fit(garch_returns)

    fallbacks = model_cls()._fallback_starting_values(1.0)
    assert len(fake.calls) == 1 + len(fallbacks)  # tentou todos antes de desistir


@pytest.mark.parametrize("model_cls", [Garch11VaR, EgarchVaR])
def test_fallback_starting_values_are_valid_for_the_arch_model(
    model_cls, garch_returns
):
    """O arch rejeita `starting_values` de tamanho errado com ValueError; cada vetor de
    fallback precisa casar com a parametrizacao do modelo que o declara."""
    from arch import arch_model

    scaled = garch_returns * 100
    instance = model_cls()
    arch = arch_model(scaled, mean="Zero", dist="normal", **instance._arch_kwargs())
    for starting_values in instance._fallback_starting_values(scaled.var()):
        result = arch.fit(disp="off", starting_values=np.asarray(starting_values))
        assert result.convergence_flag == 0
