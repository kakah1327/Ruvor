# D-50 — O preço vem do endpoint `chart` v8 do Yahoo, por HTTP direto

**Status:** aceita · 2026-09-21

## Contexto

O motor busca preço pelo `yfinance`, que entrega um `DataFrame` já ajustado. A `bronze` existe
para guardar o que o provedor devolveu ([D-13](D-13-camadas-bronze-prata-ouro.md)), e o cru
não passa pela biblioteca. As alternativas eram o `yfinance` no `worker` e a brapi.

## Decisão

`GET query2.finance.yahoo.com/v8/finance/chart/<símbolo>?period1&period2&interval=1d&events=div,splits`,
por `urllib`, sem dependência nova. A resposta inteira — OHLCV, ajustado, dividendos,
desdobramentos, metadados — vai crua para `bronze.yahoo_chart`. O `yfinance` fica no motor.

## Consequências

- `range=max` devolve mensal; só `period1`/`period2` explícitos devolvem diário.
- A data do pregão é o timestamp no fuso `meta.exchangeTimezoneName`, nunca UTC.
- Pregão com `close` nulo vem inteiro nulo e é descartado; os nulos se movem entre coletas.
- O ajustado é o do Yahoo, não recalculado — recalcular a partir dos eventos é outro bloco.
- Mesmo risco da [D-47](D-47-fonte-do-catalogo-e-o-site-da-b3.md): endpoint não prometido,
  contido pela `bronze`, pelo cliente isolado e pelas fixtures versionadas.

Origem: [spec M1.2 — Ingestão de preços](../specs/M1.2-ingestao-de-precos.md).
