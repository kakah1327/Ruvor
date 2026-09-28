# D-107 — O M2.1a implementa em duas fases, com uma PR cada — restringe a D-82

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

A [D-82](D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md) diz três PRs por bloco: spec,
plano e implementação. O M2.1a depende da base da API do M1.6a (`apps/api`, `ApiError`, o tratador,
`REST_FRAMEWORK` e os tipos do DRF), que ainda não existia quando a spec foi aprovada.

## Decisão

**Duas fases, uma PR de implementação cada.** A fase 1 não importa `rest_framework` e não toca
arquivo de outra frente: sessão, cache, modelo, serviços, auditoria e comandos. A fase 2, com o
M1.6a na `main`, faz as rotas, a autenticação do DRF, o limite por IP, os códigos no tratador e o
`requested_by`. **A PR da fase 1 também atualiza o `ESTADO.md`** no que ela torna falso, como um
fecho parcial; a da fase 2 faz o FECHA do bloco.

## Consequências

- Quatro PRs no bloco: spec, plano, fase 1 e fase 2 (o plano da fase 2 entra no mesmo arquivo).
- Vale só para o M2.1a. Outro bloco que queira fases decide de novo.

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
