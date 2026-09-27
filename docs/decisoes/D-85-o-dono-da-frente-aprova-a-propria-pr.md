# D-85 — O dono da frente aprova e faz o merge da própria PR; restringe a D-82

**Status:** aceita · 2026-09-26 · restringe a [D-82](D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md)

## Contexto

A [D-82](D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md) pôs cada bloco num ramo próprio,
com três PRs — spec, plano e implementação —, e fez da aprovação **por um dev de outra frente**
o portão humano.

No primeiro dia, a regra mostrou o custo: com duas frentes ativas, cada PR de uma frente espera o
único dono da outra, e cada bloco tem três delas. A spec do M1.5b chegou aprovada pelo dono da
frente e ficou parada na PR, esperando uma pessoa que trabalha em outra coisa. O dono da frente
`marco1` decidiu não depender disso.

## Decisão

**O portão humano de spec, plano, mockup e implementação é o dono da frente**, que aprova e faz o
merge da própria PR. Revisão de outra frente deixa de ser obrigatória.

O resto da D-82 continua valendo: ramo por bloco, `<frente>/<bloco>-<assunto>`, as três PRs,
merge com commit de merge e nunca _squash_, e `git merge origin/main` no ramo depois de cada
merge. A CI também continua barrando: **PR vermelha não entra**
([D-83](D-83-a-ci-barra-na-pr.md)).

**A exceção que fica:** PR que **muda um contrato entre frentes** — a tabela de contratos de
[`FRENTES.md`](../FRENTES.md#contratos-entre-frentes) — passa pela frente que o consome, como
aquela seção já dizia. É o único caso em que uma frente pode quebrar o trabalho da outra sem
perceber.

## Consequências

- As PRs deixam de esperar outra pessoa. A PR continua existindo: é ela que roda a CI, que
  registra o portão e que mostra às outras frentes o que entrou.
- Revisão entre frentes vira voluntária, fora dos contratos. Quem quiser olhar a PR de outra
  frente olha; ninguém espera por isso.
- O GitHub não deixa o autor aprovar a própria PR. O registro do portão é o **merge feito pelo
  dono da frente**, com a CI verde; se a proteção da `main` for configurada, ela exige CI verde,
  não aprovação.
- A decisão vale para todas as frentes e foi escrita na faixa da `marco1`, como
  [`FRENTES.md`](../FRENTES.md#numeração-de-decisão) manda. A frente `fundamentos` fica sabendo
  pela PR que a traz.
