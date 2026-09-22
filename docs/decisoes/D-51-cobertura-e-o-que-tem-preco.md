# D-51 — Cobertura é "o que tem preço"; não há coluna de cobertura no catálogo

**Status:** aceita · 2026-09-21

## Contexto

A [D-19](D-19-cobertura-de-ativos-em-camadas.md) separa ativos cobertos de cauda longa, e a
política de quem entra é pendência de produto. O M1.2 precisava coletar preço de quatro ativos
(os do TCC) sem decidir a política.

## Decisão

`import_prices <tickers>` faz a primeira carga dos tickers dados; `import_prices` sem argumentos
atualiza os ativos **ativos** que já têm linha em `silver.price`. Coberto é o que tem dado. Não
existe coluna `covered` em `silver.asset`.

## Consequências

- O mecanismo já aceita qualquer ticker do catálogo; quando a D-19 for decidida, ela escolhe
  quem roda o comando — não muda esquema.
- Ativo inativado pelo `import_assets` deixa de ser atualizado e é reportado como pulado.
- A primeira carga foi PETR4, VALE3, ITUB4 e IBOV, em 2026-09-22.

Origem: [spec M1.2 — Ingestão de preços](../specs/M1.2-ingestao-de-precos.md).
