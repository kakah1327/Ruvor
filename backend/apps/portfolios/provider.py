"""O provedor da carteira (M2.2a, RF-07): a serie pronta, no quadro que o motor consome.

**So no `worker`**: importa `pandas`. Recebe a `PortfolioSeries` que `series.build` montou -- o
indice da carteira, nao um preco -- e a entrega como a coluna `close`, o contrato do
`SilverPriceProvider` (`apps/risk/provider.py`): indice de datas de nome `date`, montado por
`pd.to_datetime`, e o intervalo fechado dos dois lados. O `ticker` e ignorado: a carteira tem uma
serie so. Nao herda de `DataProvider`, pela mesma razao do provedor do ativo.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from apps.portfolios.series import PortfolioSeries


class PortfolioSeriesProvider:
    """Entrega ao motor o indice da carteira como `close`."""

    def __init__(self, series: PortfolioSeries) -> None:
        self._series = series

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """As datas da serie entre `start` e `end` (ISO `YYYY-MM-DD`), inclusive."""
        first = date.fromisoformat(start)
        last = date.fromisoformat(end)
        pairs = [
            (d, v)
            for d, v in zip(self._series.dates, self._series.index, strict=True)
            if first <= d <= last
        ]
        return pd.DataFrame(
            {"close": [v for _, v in pairs]},
            index=pd.DatetimeIndex(pd.to_datetime([d for d, _ in pairs]), name="date"),
        )
