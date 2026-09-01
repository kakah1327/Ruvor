# D-03 — Carteira e montada pelo usuario, nao importada

**Status:** aceita · 2026-08-29

## Contexto

A plataforma precisa analisar conjuntos de acoes, nao so acoes isoladas. Importar carteira pronta de corretora exigiria integracao com instituicoes financeiras, autenticacao de terceiros e tratamento de formatos proprietarios.

## Decisão

O usuario **compoe a carteira dentro da plataforma**, selecionando acoes e definindo pesos. Nao ha importacao de carteira externa.

## Consequências

- Elimina um subsistema inteiro de integracao no inicio.
- A combinacao de pesos e sempre nova, entao nao pode ser pre-calculada — e o que torna o modo A (D-07) necessario.
- Sugerir pesos atravessaria a fronteira regulatoria da CVM; a plataforma analisa o que o usuario escolheu.
