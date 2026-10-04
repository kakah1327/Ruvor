"""Interface comum dos modelos de retorno (M5.1, RF-05): a previsao pontual do retorno
logaritmico de um pregao, sem olhar a frente (RF-03), mais a do proximo pregao (RF-03a).

O motor devolve numeros `float`: nao tem nivel de significancia, veredito nem data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ReturnForecast:
    """A previsao de um modelo sobre o teste, e a do pregao seguinte ao ultimo dia dele."""

    #: alinhada a test.index; o valor do dia t usa so train e test antes de t
    series: pd.Series
    #: a posicao n = len(test): o proximo pregao (RF-03a)
    next_value: float


class ReturnModel(ABC):
    """Contrato de um modelo de retorno do registry proprio de `engine.returns`."""

    #: nome curto e unico no registry de retorno (ex: "ar_1")
    name: str

    @property
    def hyperparameters(self) -> dict[str, Any]:
        """Os hiperparametros efetivos, para o manifesto (D-15). Leitura pura: nenhum
        caminho de calculo a chama."""
        return {}

    @abstractmethod
    def forecast(self, train: pd.Series, test: pd.Series) -> ReturnForecast:
        """A previsao de cada dia de `test`, com os parametros reestimados a cada 252
        pregoes numa janela que cresce, e a da posicao `len(test)` pela mesma regra."""
