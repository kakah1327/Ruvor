# D-83 — A CI barra na PR

**Status:** aceita · 2026-09-26 · substitui a [D-42](D-42-ci-avisa-e-nao-bloqueia.md)

## Contexto

A [D-42](D-42-ci-avisa-e-nao-bloqueia.md) restringiu a promessa da
[ARQUITETURA](../ARQUITETURA.md#ambientes) — *"não passou, não entra"* — porque, com trabalho
direto na `main`, não havia ponto de integração onde barrar. E disse: *"isto se inverte quando
a D-31 se inverter"*.

A [D-82](D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md) inverteu a D-31.

## Decisão

**A CI roda em toda pull request, e PR com CI vermelha não entra na `main`.** A promessa
original da ARQUITETURA volta a valer inteira.

O gatilho `pull_request` entra no `ci.yml` ao lado do `push` na `main`, que continua: ele prova
que o resultado do merge também passa.

## Consequências

- **A `main` vermelha deixa de ser aceita.** Se ficar — merge de duas PRs verdes que juntas
  reprovam —, conserta quem fez o último merge, antes de qualquer outro.
- O barramento de fato depende da proteção de ramo no GitHub (verificações obrigatórias); até
  ela ser ligada, a CI da PR avisa e o revisor não aprova PR vermelha.
- Os mesmos quatro trabalhos, com os mesmos tetos de tempo. A cota mensal pesa mais: agora
  roda por PR e por merge.
