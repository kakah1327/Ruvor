"""Limpeza de precos e calculo de retornos — usado por todos os modelos, independente da fonte."""
from __future__ import annotations

import numpy as np
import pandas as pd


def clean_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Remove precos nulos/nao positivos (gaps) que quebrariam o log-retorno."""
    return df[df["close"] > 0].dropna(subset=["close"])


def log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1)).dropna()


def fetch_returns(provider, ticker: str, start: str, end: str) -> pd.Series:
    """Pipeline completo: busca precos no provider, limpa e converte para log-retornos."""
    df = clean_prices(provider.fetch(ticker, start, end))
    return log_returns(df["close"])
