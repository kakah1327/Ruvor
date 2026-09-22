# D-54 — Na ingestão de preços a transação é por ativo; restringe a D-48

**Status:** aceita · 2026-09-21

## Contexto

A [D-48](D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md) fixou "a `silver` só muda
depois de a coleta inteira chegar". No catálogo a coleta é uma resposta só, e tudo-ou-nada é a
unidade natural. Em preços cada ativo é uma resposta independente.

## Decisão

`silver.price` e `silver.corporate_event` mudam dentro de um `atomic()` **por ativo**, só depois
de a resposta daquele ativo ser válida. Um 404 num ticker não segura os outros. A
`collection_run` termina `failed` mesmo assim, com os tickers falhos em `error`, para a falha
não passar despercebida; o que entrou está inteiro, ativo a ativo.

## Consequências

- Quatro formas de falha com o mesmo destino no relatório: HTTP 4xx com JSON (vai para a
  `bronze`), 200 sem série (vai para a `bronze`), exceção do cliente (nada a gravar), exceção
  na gravação (a transação reverte, a `bronze` fica).
- O teste que distingue "com `atomic()`" de "sem" é o da quarta forma: uma gravação que escreve
  um pregão e levanta — sem transação, o pregão sobrevive. Foi provado por mutação.
- A D-48 continua valendo para o catálogo; a unidade de transação é decisão de cada ingestão.

Origem: [spec M1.2 — Ingestão de preços](../specs/M1.2-ingestao-de-precos.md).
