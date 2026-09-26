# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b → M1.6. É o fim do Marco 1: digita ITUB4, recebe o comportamento e o risco.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (reservadas pelo M1.5b), depois D-85 a D-99.

---

## Agora

**Bloco:** M1.5b — Treino separado da previsão
**Etapa:** spec aprovada na revisão adversarial, **aguardando o portão humano**
**Ramo:** `marco1/M1.5b-treino-separado`, ainda não criado

A spec ([`specs/M1.5b-treino-separado-da-previsao.md`](../specs/M1.5b-treino-separado-da-previsao.md))
foi escrita na `main` antes da [D-82](../decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md),
e está sem commit, junto com a linha dela em `specs/README.md`.

## Próximo passo

1. Criar o ramo `marco1/M1.5b-treino-separado` a partir da `main` e commitar nele a spec e a
   linha do índice.
2. Abrir a PR da spec. A aprovação, por um dev de outra frente, é o portão humano.
3. Escrever o plano no mesmo ramo, e seguir o [PROCESSO](../PROCESSO.md).

## Depois

**M1.6 — Aplicação web:** a API de leitura, o kit completo, os mockups e as primeiras telas
(casco, busca, tela do ativo), e o cálculo sob demanda para ativo não coberto. Duas coisas dele
são esperadas por outras frentes, e convém que saiam cedo:

- as **convenções da API HTTP**, que o M2.1 também usa ([contrato aberto](../FRENTES.md#contratos-entre-frentes));
- o **casco do frontend e o kit**, de que dependem as telas de login do M2.1.

## O que esta frente deve a outras

| Para | O quê | Estado |
|---|---|---|
| `identidade` | convenções da API | 🔴 aberto |
| `identidade` | casco do frontend e kit | ⬜ M1.6 |
| `identidade` | combinar quem preenche `risk_run.requested_by` | ⬜ na spec do M2.1 |

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84; a spec do M1.5b chega aprovada na revisão adversarial |
