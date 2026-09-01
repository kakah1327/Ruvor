"""GARCHNet (Buczynski & Chlebus, 2024): hibrido GARCH + LSTM -- usa a volatilidade
condicional do GARCH(1,1) ja implementado (Etapa 2, `engine.models.garch.garch_1_1`) como
feature de entrada extra pra uma LSTM que preve o quantil de VaR diretamente via pinball
loss, aprendendo uma correcao nao-linear sobre a estimativa GARCH.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from tensorflow import keras

from engine.models.base import ModelCategory
from engine.models.garch.garch_1_1 import Garch11VaR
from engine.models.ml._quantile_nn import QuantileNeuralVaR
from engine.models.registry import register_model


@register_model("garchnet")
class GarchNetVaR(QuantileNeuralVaR):
    category = ModelCategory.ML

    def fit(self, returns: pd.Series) -> "GarchNetVaR":
        super().fit(returns)
        self._garch = Garch11VaR().fit(returns)
        return self

    def _features(self, returns: pd.Series) -> np.ndarray:
        values = returns.to_numpy()
        sigma = self._garch.full_sigma_series(returns).to_numpy()
        return np.column_stack([values, np.abs(values), sigma])

    def _build_model(self, n_features: int, units: int, n_layers: int) -> keras.Model:
        model = keras.Sequential()
        model.add(keras.layers.Input(shape=(self.WINDOW, n_features)))
        for i in range(n_layers):
            model.add(keras.layers.LSTM(units, return_sequences=(i < n_layers - 1)))
        model.add(keras.layers.Dense(1))
        return model
