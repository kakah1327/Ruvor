"""Diagnosticos especificos dos modelos de ML (Etapa 3), alem da interface generica ja
coberta por test_all_models.py (que ja garante var_series >= 0 e finito p/ todos, LSTM/GRU/
GARCHNet inclusive). O teste de monotonicidade usa o CAViaR (rapido, sem custo de rede
neural) como representante -- LSTM/GRU/GARCHNet compartilham a mesma base
(QuantileNeuralVaR) e ja sao exercitados pelo teste generico; repetir aqui multiplicaria o
tempo da suite sem ganho de sinal proporcional.
"""

from __future__ import annotations

import numpy as np

from engine.models.ml.caviar import CaviarVaR


def test_caviar_optimizer_converges_with_plausible_params(synthetic_returns):
    train, test = synthetic_returns.iloc[:250], synthetic_returns.iloc[250:]

    model = CaviarVaR().fit(train)
    beta, f0 = model._initial_beta(alpha=0.05)

    assert np.all(np.isfinite(beta))
    assert np.isfinite(f0) and f0 > 0


def test_caviar_var_increases_for_more_extreme_alpha(synthetic_returns):
    train, test = synthetic_returns.iloc[:250], synthetic_returns.iloc[250:]
    model = CaviarVaR().fit(train)

    var_5pct = model.estimate_var(test, alpha=0.05).var_series
    var_1pct = model.estimate_var(test, alpha=0.01).var_series

    assert var_1pct.mean() >= var_5pct.mean()
