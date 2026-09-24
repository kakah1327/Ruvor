# D-62 — A série que vai ao motor é o `adj_close`

**Status:** aceita · 2026-09-24

## Contexto

`silver.price` guarda `close` e `adj_close`. O contrato do motor pede uma coluna chamada
`close`, e o `run_experiment` calcula os retornos a partir dela. Qual das duas colunas
preenche esse `close` decide **de que série o VaR fala**.

O M1.2 já gravou `log_return` sobre os **ajustados** — proventos e desdobramentos
incorporados.

## Decisão

O `SilverPriceProvider` entrega o **`adj_close`** na coluna que o contrato chama de `close`.

É o retorno que o investidor teve, e é a mesma base do `log_return` do M1.2 — então a camada
3 e a camada 1 falam da mesma série, e a divergência entre elas deixa de ser possível por
construção.

## Consequências

- Verificável, e verificado: os retornos que o motor calcula a partir do provedor batem com
  `silver.price.log_return` com diferença absoluta **< 1e-9**. O piso da coluna
  `Decimal(18,10)` é 5e-11; o resto é ruído de ponto flutuante.
- O nome da coluna do `DataFrame` continua `close`, porque é o contrato do motor. A
  confusão possível — "o motor usa o preço de fechamento" — é de leitura, e existe este
  registro para desfazê-la.
- Um dia de desdobramento não vira retorno de −50%: é o defeito que a escolha do `close`
  cru produziria, e ele apareceria como violação de VaR, não como erro de dado.

Origem: [spec M1.4 — Motor de risco](../specs/M1.4-motor-de-risco.md) (RF-05).
