"""Provider de dados via yfinance — ativos da B3 (ex: PETR4.SA, VALE3.SA, ITUB4.SA, ^BVSP)."""
from __future__ import annotations

import pandas as pd

from varlab.data.providers.base import DataProvider


class YFinanceProvider(DataProvider):
    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        import yfinance as yf

        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError(f"Nenhum dado retornado para '{ticker}' entre {start} e {end}")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.rename(columns=str.lower)
        df.index.name = "date"
        return df[["close"]]
