# D-82 — Ramo por bloco, e PR revisada por um dev de outra frente

**Status:** aceita · 2026-09-26 · substitui a [D-31](D-31-trabalho-direto-na-main.md)

## Contexto

A [D-31](D-31-trabalho-direto-na-main.md) pôs o trabalho direto na `main` "enquanto o time for
uma pessoa", e disse quando voltar atrás: *"mais de uma pessoa desenvolvendo ao mesmo tempo"*.

Aconteceu. A partir de 2026-09-26 são duas pessoas em duas frentes simultâneas, com uma
terceira definida
([D-84](D-84-frentes-com-cerca-de-pastas.md)). Na `main` compartilhada, um commit de uma
frente leva junto o trabalho em andamento de outra, e a `main` deixa de ser entregável.

## Decisão

**Todo bloco nasce num ramo próprio e entra na `main` por pull request, aprovada por um dev de
outra frente.** Ninguém commita direto na `main`.

- **Nome do ramo:** `<frente>/<bloco>-<assunto>` — `marco1/M1.5b-treino-separado`,
  `identidade/M2.1-identidade-e-acesso`. O prefixo é o nome da frente em
  [`FRENTES.md`](../FRENTES.md), e é por ele que o agente descobre onde está.
- **Três PRs por bloco, do mesmo ramo:** a da spec, a do plano e a da implementação. **A
  aprovação da PR é o portão humano** do [PROCESSO](../PROCESSO.md#3-o-ciclo): a spec só vale
  depois de entrar na `main`, e assim as outras frentes enxergam o contrato antes do código.
  Mockup segue a mesma regra, numa PR própria.
- **Quem aprova é de outra frente.** O dono da frente não aprova a própria PR.
- **Merge com commit de merge, nunca _squash_.** O commit por tarefa segue sendo a
  granularidade de revisão e de reversão; _squash_ o apagaria.
- Depois de cada merge, o ramo continua do ponto em que estava: `git merge origin/main` nele
  antes de seguir.

## Consequências

- Um commit por tarefa continua valendo, agora dentro do ramo.
- Reverter um bloco volta a ser descartar o ramo antes do merge, ou reverter o commit de merge
  depois.
- A CI passa a ter onde barrar — isso é a [D-83](D-83-a-ci-barra-na-pr.md).
- A proteção da `main` no GitHub (PR obrigatória, uma aprovação, CI verde) é configuração do
  repositório, feita à mão pelo dono dele; esta decisão não se aplica sozinha.
- O plano do F2a, executado com ramo próprio, volta a ser modelo também nisso.
