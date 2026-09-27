# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6. É o fim do Marco 1: digita ITUB4, recebe o comportamento e o risco.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99.

---

## Agora

**Bloco:** M1.5b — Treino separado da previsão, **fechado em 2026-09-27**
**Etapa:** implementação concluída — T1 a T9, um commit por tarefa que produz (a T7 mediu as
mutações e não produz), com a execução real e o fecho na T9; **a PR de implementação ainda não
foi aberta**
**Ramo:** `marco1/M1.5b-treino-separado`, com a spec
([`specs/M1.5b-treino-separado-da-previsao.md`](../specs/M1.5b-treino-separado-da-previsao.md)),
o plano ([`planos/M1.5b-treino-separado-da-previsao.md`](../planos/M1.5b-treino-separado-da-previsao.md))
e as decisões D-75 a D-81

## Próximo passo

1. Abrir a PR de implementação do M1.5b e mesclá-la com a CI verde — o dono da frente é o portão
   ([D-85](../decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)).
2. Conferir no log do `worker` o primeiro tique do Beat num dia útil (segunda, 19h30): é o dia
   comum com um pregão novo de verdade, que a execução real do fecho não teve — a coleta de
   domingo não trouxe pregão (ver o [ESTADO](../ESTADO.md)).
3. **M1.6 — Aplicação web**: escrever a spec, num ramo novo `marco1/M1.6-…` a partir da `main`.

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
| 2026-09-26 | plano do M1.5b aprovado; implementação começa pela T1 |
| 2026-09-27 | M1.5b fechado: T1 a T9, execução real, D-75 a D-81; a PR de implementação fica para o dono abrir |
