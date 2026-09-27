"""Base compartilhada por modelos de ML que preveem o quantil de VaR diretamente via
pinball loss (Etapa 3): LSTM, GRU e o componente neural do GARCHNet. Diferente do GARCH
(Etapa 2), a rede treinada para alpha=5% e DIFERENTE da treinada para alpha=1% -- por
isso o fit() e preguicoso por alpha: so guarda os dados; o treino de verdade (grid search
+ ajuste completo) acontece na primeira chamada de estimate_var() para cada alpha, com
cache pra nao retreinar a toa. A partir dai, o walk-forward so faz forward pass (barato) a
cada dia e, a cada REFIT_FREQUENCY_DAYS, continua o treino (warm start, poucas epocas) com
todo o dado ja observado ate ali -- mesmo espirito da janela expansiva do GARCH.

Contrato de `_features(returns)`: `returns` sempre comeca no INICIO do periodo de treino
(e' ou exatamente `train_returns_`, ou `train_returns_` concatenado com retornos de teste
ja observados) -- permite que subclasses como GARCHNet alinhem features que dependem de
estado acumulado (ex: volatilidade do GARCH) sem se preocupar com onde fica a fronteira
treino/teste.

O grid search cobre so `units` e `n_layers` (nao `learning_rate`/`batch_size`, fixos) --
decisao consciente de escopo computacional: o fit e' por alpha, e cada combinacao do grid
custa uma rodada de treino inteira.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, ClassVar

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

from engine import seeding
from engine.models.base import VaREstimate, VaRModel
from engine.snapshots import Snapshot, pack_network, unpack_network


def _pinball_loss(alpha: float):
    def loss(y_true, y_pred):
        error = tf.cast(y_true, tf.float32) - tf.cast(y_pred, tf.float32)
        return tf.reduce_mean(tf.maximum(alpha * error, (alpha - 1.0) * error))

    return loss


def _make_windows(features: np.ndarray, window: int) -> np.ndarray:
    n = len(features)
    return np.stack([features[i : i + window] for i in range(n - window)])


class QuantileNeuralVaR(VaRModel):
    WINDOW = 20
    REFIT_FREQUENCY_DAYS = 252
    GRID: ClassVar[dict[str, list[int]]] = {"units": [16, 32], "n_layers": [1, 2]}
    LEARNING_RATE = 0.001
    BATCH_SIZE = 32
    SEARCH_EPOCHS = 20
    REFIT_EPOCHS = 10
    PATIENCE = 5
    VAL_FRACTION = 0.15

    @property
    def hyperparameters(self) -> dict[str, Any]:
        return {
            "window": self.WINDOW,
            "refit_frequency_days": self.REFIT_FREQUENCY_DAYS,
            # copia que alcanca as LISTAS: devolver o proprio dict -- ou uma copia rasa,
            # que compartilha as listas -- deixaria um chamador alterar a grade de busca
            # de TODAS as instancias. Leitura pura nao pode entregar estado vivo.
            "grid": {chave: list(valores) for chave, valores in self.GRID.items()},
            "learning_rate": self.LEARNING_RATE,
            "batch_size": self.BATCH_SIZE,
            "search_epochs": self.SEARCH_EPOCHS,
            "refit_epochs": self.REFIT_EPOCHS,
            "patience": self.PATIENCE,
            "val_fraction": self.VAL_FRACTION,
        }

    @abstractmethod
    def _build_model(self, n_features: int, units: int, n_layers: int) -> keras.Model:
        """Modelo Keras NAO compilado: entrada (WINDOW, n_features), saida (1,)."""

    @abstractmethod
    def _features(self, returns: pd.Series) -> np.ndarray:
        """Matriz (n, n_features) alinhada a `returns` -- ver contrato no docstring do modulo."""

    def fit(self, returns: pd.Series) -> QuantileNeuralVaR:
        self.train_returns_ = returns
        self._fitted: dict[float, dict] = {}
        # retratos por alpha, por posicao (M1.5b): os recebidos por `restore` e os que o
        # ultimo `estimate_var` percorreu -- restaurados e treinados
        self._restored: dict[float, dict[int, Snapshot]] = {}
        self._taken: dict[float, dict[int, Snapshot]] = {}
        return self

    def restore(self, alpha: float, snapshots: list[Snapshot]) -> None:
        """Antes de estimate_var: os pontos cobertos nao sao treinados, sao carregados."""
        self._restored[alpha] = {s.position: s for s in snapshots}

    def snapshots(self, alpha: float) -> list[Snapshot]:
        """Depois de estimate_var -- ou depois de ela levantar: os pontos que existem ate ali,
        restaurados e treinados, em ordem de posicao."""
        taken = self._taken.get(alpha, {})
        return [taken[pos] for pos in sorted(taken)]

    @staticmethod
    def _take(model: keras.Model, config: tuple[int, int], position: int) -> Snapshot:
        units, n_layers = config
        return Snapshot(
            position=position,
            payload=pack_network(
                model.get_weights(),
                [v.numpy() for v in model.optimizer.variables],
                units,
                n_layers,
            ),
        )

    @staticmethod
    def _load(model: keras.Model, snapshot: Snapshot) -> None:
        """Pesos e otimizador no MESMO objeto de modelo, ja com o otimizador construido."""
        state = unpack_network(snapshot.payload)
        model.set_weights(state.weights)
        # POR POSICAO: os `path` levam o nome automatico do modelo, que muda entre processos
        for var, valor in zip(
            model.optimizer.variables, state.optimizer_variables, strict=True
        ):
            var.assign(valor)

    def _model_from_snapshot(
        self, snapshot: Snapshot, n_features: int, alpha: float
    ) -> tuple[keras.Model, tuple[int, int]]:
        state = unpack_network(snapshot.payload)
        config = (state.units, state.n_layers)
        model = self._compile(self._build_model(n_features, *config), alpha)
        model.optimizer.build(model.trainable_variables)  # as variaveis sao preguicosas
        self._load(model, snapshot)
        return model, config

    def _windows_and_targets(self, returns: pd.Series):
        features = self._features(returns)
        x = _make_windows(features, self.WINDOW)
        y = returns.to_numpy()[self.WINDOW :]
        return x, y

    def _compile(self, model: keras.Model, alpha: float) -> keras.Model:
        model.compile(
            optimizer=keras.optimizers.Adam(self.LEARNING_RATE),
            loss=_pinball_loss(alpha),
        )
        return model

    def _fit_for_alpha(self, alpha: float) -> dict:
        # o treino de verdade comeca aqui, e e o unico ponto do motor que consome
        # aleatoriedade sem semear: o fit() acima e preguicoso (ver RF-01 do M1.4)
        seeding.apply()

        x, y = self._windows_and_targets(self.train_returns_)
        n_val = max(1, int(len(x) * self.VAL_FRACTION))
        x_train, y_train = x[:-n_val], y[:-n_val]
        x_val, y_val = x[-n_val:], y[-n_val:]
        n_features = x.shape[-1]

        best_config, best_val_loss = None, np.inf
        for units in self.GRID["units"]:
            for n_layers in self.GRID["n_layers"]:
                candidate = self._compile(
                    self._build_model(n_features, units, n_layers), alpha
                )
                early_stop = keras.callbacks.EarlyStopping(
                    monitor="val_loss",
                    patience=self.PATIENCE,
                    restore_best_weights=True,
                )
                history = candidate.fit(
                    x_train,
                    y_train,
                    validation_data=(x_val, y_val),
                    epochs=self.SEARCH_EPOCHS,
                    batch_size=self.BATCH_SIZE,
                    callbacks=[early_stop],
                    verbose=0,
                )
                val_loss = min(history.history["val_loss"])
                if val_loss < best_val_loss:
                    best_val_loss, best_config = val_loss, (units, n_layers)

        units, n_layers = best_config
        model = self._compile(self._build_model(n_features, units, n_layers), alpha)
        early_stop = keras.callbacks.EarlyStopping(
            monitor="loss", patience=self.PATIENCE, restore_best_weights=True
        )
        model.fit(
            x,
            y,
            epochs=self.SEARCH_EPOCHS,
            batch_size=self.BATCH_SIZE,
            callbacks=[early_stop],
            verbose=0,
        )
        return {"model": model, "config": best_config}

    def estimate_var(
        self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1
    ) -> VaREstimate:
        restored = self._restored.get(alpha, {})
        # o dicionario e publicado ANTES do treino: se um retreino levantar, `snapshots()`
        # devolve os pontos ja percorridos (RF-02)
        taken: dict[int, Snapshot] = {}
        self._taken[alpha] = taken

        full_returns = pd.concat([self.train_returns_, returns])
        n_train = len(self.train_returns_)
        x_full, y_full = self._windows_and_targets(full_returns)
        test_start_window = (
            n_train - self.WINDOW
        )  # janela i preve o dia (WINDOW + i) da serie completa

        predicted = np.empty(len(returns))
        pos = 0
        while pos < len(returns):
            if pos == 0 and 0 in restored:
                # o objeto de modelo e montado UMA vez por (rede, alpha); os trechos
                # seguintes so trocam pesos e otimizador
                model, config = self._model_from_snapshot(
                    restored[0], x_full.shape[-1], alpha
                )
                taken[0] = restored[0]
            elif pos == 0:
                if alpha not in self._fitted:
                    fitted = self._fit_for_alpha(alpha)
                    # depois do ajuste final: pesos ja restaurados pelo EarlyStopping e o
                    # otimizador da ultima epoca -- o estado de onde o retreino parte
                    fitted["snapshot"] = self._take(
                        fitted["model"], fitted["config"], 0
                    )
                    self._fitted[alpha] = fitted
                model = self._fitted[alpha]["model"]
                config = self._fitted[alpha]["config"]
                taken[0] = self._fitted[alpha]["snapshot"]
            elif pos in restored:
                self._load(model, restored[pos])
                taken[pos] = restored[pos]
            else:
                # janela expansiva: continua o treino (warm start) com tudo ja observado
                known_windows = test_start_window + pos
                seeding.apply(position=pos)
                model.fit(
                    x_full[:known_windows],
                    y_full[:known_windows],
                    epochs=self.REFIT_EPOCHS,
                    batch_size=self.BATCH_SIZE,
                    verbose=0,
                )
                taken[pos] = self._take(model, config, pos)

            chunk_end = min(pos + self.REFIT_FREQUENCY_DAYS, len(returns))
            window_slice = slice(test_start_window + pos, test_start_window + chunk_end)
            predicted[pos:chunk_end] = model.predict(
                x_full[window_slice], verbose=0
            ).flatten()
            pos = chunk_end

        var_series = pd.Series(
            np.maximum(-predicted, 0) * (horizon**0.5), index=returns.index
        )
        return VaREstimate(
            var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name
        )
