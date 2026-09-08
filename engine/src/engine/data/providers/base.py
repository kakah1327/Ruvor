"""Interface comum a qualquer fonte de dados de precos (yfinance, CSV, outra API...)."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class DataProvider(ABC):
    @abstractmethod
    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Retorna DataFrame indexado por data com, no minimo, a coluna 'close'."""
