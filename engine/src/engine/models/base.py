"""Interface comum que todo modelo de VaR (tradicional, GARCH ou ML) deve implementar."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class ModelCategory(str, Enum):
    TRADITIONAL = "traditional"
    GARCH = "garch"
    ML = "ml"


@dataclass
class VaREstimate:
    """Serie de estimativas de VaR alinhada aos retornos de teste, mais metadados do fit."""

    var_series: pd.Series
    alpha: float
    horizon: int
    model_name: str


class VaRModel(ABC):
    """Contrato que qualquer modelo precisa cumprir para entrar no registry.

    Um modelo novo (ex: um EGARCH diferente, ou um algoritmo de ML novo) so precisa
    implementar esta interface e se registrar via `@register_model` — nenhum outro
    modulo do sistema (web, cli, backtesting, experiments) precisa ser alterado.
    """

    #: nome curto e unico usado no registry e na UI (ex: "garch_1_1")
    name: str
    category: ModelCategory

    @abstractmethod
    def fit(self, returns: pd.Series) -> "VaRModel":
        """Ajusta o modelo a uma serie de retornos historicos (janela de treino)."""

    @abstractmethod
    def estimate_var(
        self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1
    ) -> VaREstimate:
        """Retorna as estimativas de VaR alinhadas ao indice de `returns` (periodo de teste).

        `returns` aqui serve para o modelo saber PARA QUAIS DATAS gerar a serie de VaR —
        modelos estaticos (Etapa 1) ignoram os valores e so usam `returns.index`; modelos
        condicionais/rolling (GARCH, ML) podem usar os valores para atualizar o estado a
        cada passo (walk-forward).
        """
