"""A costura entre `silver.price` e o motor: o unico arquivo que conhece os dois lados.

O motor pede um objeto com `fetch(ticker, start, end) -> DataFrame` indexado por data e
com a coluna `close` (`engine.data.providers.base.DataProvider`). Quem sabe que essa serie
mora em `silver.price`, sob um `Asset` de `ticker`, e este modulo — e so ele. O motor nao
aprende o que e `silver`, `Asset` ou `Price` (D-17, RF-04).

**A coluna `close` recebe o `adj_close`.** E a mesma base do `log_return` que o M1.2
gravou, e e o retorno que o investidor teve: quem calcula retorno sobre o `close` bruto ve
um tombo artificial em todo dividendo e em todo desdobramento (RF-05).

**Nao herda de `DataProvider`.** O contrato e satisfeito estruturalmente, por duck typing:
`run_experiment(config, provider)` nao anota o parametro, e herdar estreitaria o contrato
sem necessidade — obrigaria o backend a importar a classe base do motor para nada.

Duas escolhas de borda, que o contrato do motor nao fixa e ficam registradas aqui:

- **o intervalo e fechado dos dois lados** (`start <= date <= end`), ao contrario do
  `end` exclusivo do provedor do Yahoo: quem pede a janela ate o ultimo pregao espera o ultimo
  pregao;
- **serie vazia devolve `DataFrame` vazio**, com a coluna `close` e o indice de datas, nao
  excecao: ticker sem preco e um caso legitimo que quem chama decide como tratar, e o
  `clean_prices` do motor aceita o quadro vazio.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from apps.assets.models import Price


class SilverPriceProvider:
    """Le `silver.price` de um ativo, pelo ticker, e entrega o quadro que o motor consome."""

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Pregoes de `ticker` entre `start` e `end` (ISO `YYYY-MM-DD`), inclusive.

        O `adj_close` vira `float` na coluna `close`: o motor calcula com `numpy`, e uma
        coluna de `Decimal` chega la como `dtype=object` e quebra o `np.log`.
        """
        rows = (
            Price.objects.filter(
                asset__ticker=ticker,
                date__gte=date.fromisoformat(start),
                date__lte=date.fromisoformat(end),
            )
            .order_by("date")
            .values_list("date", "adj_close")
        )
        dates = [d for d, _ in rows]
        closes = [float(adj_close) for _, adj_close in rows]
        return pd.DataFrame(
            {"close": closes},
            index=pd.DatetimeIndex(pd.to_datetime(dates), name="date"),
        )
