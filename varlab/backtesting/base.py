"""Interface comum a todo teste de backtesting (Kupiec, Christoffersen, DQ, Basileia).

Um teste de backtesting so conhece `returns` (retornos realizados) e `var_series`
(estimativas de VaR de QUALQUER modelo) — nunca conhece GARCH, LSTM etc. Isso mantem
esta camada totalmente desacoplada de varlab.models: testar um modelo novo com Kupiec
nao exige nenhuma mudanca aqui.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class BacktestResult:
    test_name: str
    statistic: float
    p_value: float | None
    passed: bool
    details: dict


class BacktestTest(ABC):
    #: nome curto e unico usado no registry (ex: "kupiec")
    name: str

    @abstractmethod
    def run(self, returns: pd.Series, var_series: pd.Series, alpha: float) -> BacktestResult:
        """Compara violacoes (returns < -var_series) contra o esperado pelo teste."""
