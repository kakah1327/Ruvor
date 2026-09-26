# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b → M1.6. É o fim do Marco 1: digita ITUB4, recebe o comportamento e o risco.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (reservadas pelo M1.5b), depois D-85 a D-99.

---

## Agora

**Bloco:** M1.5b — Treino separado da previsão
**Etapa:** spec aprovada pelo dono da frente (2026-09-26), PR #1 a mesclar pelo dono ([D-85](../decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)); **plano escrito, em revisão**
**Ramo:** `marco1/M1.5b-treino-separado`, com a spec
([`specs/M1.5b-treino-separado-da-previsao.md`](../specs/M1.5b-treino-separado-da-previsao.md))
e a linha dela em `specs/README.md`

## Próximo passo

1. Mesclar a PR #1 (spec), com a CI verde — o dono da frente é o portão
   ([D-85](../decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)).
2. Fechar a revisão do plano, e abrir a PR dele no mesmo ramo.

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
| 2026-09-26 | spec do M1.5b aprovada pelo dono da frente; plano escrito no ramo; D-85: o dono da frente mescla a própria PR |
