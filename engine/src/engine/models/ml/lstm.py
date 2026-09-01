"""LSTM (Hochreiter & Schmidhuber, 1997) para estimativa de VaR: preve o quantil alpha
diretamente via pinball loss (nao assume normalidade), a partir de uma janela deslizante
de retornos e retornos absolutos. Ver engine/models/ml/_quantile_nn.py para a logica
compartilhada (fit preguicoso por alpha, grid search, walk-forward com reajuste periodico).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from tensorflow import keras

from engine.models.base import ModelCategory
from engine.models.ml._quantile_nn import QuantileNeuralVaR
from engine.models.registry import register_model


@register_model("lstm")
class LstmVaR(QuantileNeuralVaR):
    category = ModelCategory.ML

    def _features(self, returns: pd.Series) -> np.ndarray:
        values = returns.to_numpy()
        return np.column_stack([values, np.abs(values)])

    def _build_model(self, n_features: int, units: int, n_layers: int) -> keras.Model:
        model = keras.Sequential()
        model.add(keras.layers.Input(shape=(self.WINDOW, n_features)))
        for i in range(n_layers):
            model.add(keras.layers.LSTM(units, return_sequences=(i < n_layers - 1)))
        model.add(keras.layers.Dense(1))
        return model
