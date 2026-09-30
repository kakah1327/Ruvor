# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6a ✅ → M1.6b ✅ → M1.6c ✅ → M2.1m. O M1.6b fechou o Marco 1: digita ITUB4, recebe o comportamento e o risco; o M1.6c completou a tela com as camadas 4 e 5.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99 (todas usadas; a D-99 é do M1.6c) e D-140 a D-159, reservadas pela spec do M1.6c — nenhuma usada.

---

## Agora

**Bloco:** M2.1m — A coluna do autor do pedido ([spec](../specs/M2.1m-requested-by.md),
[plano](../planos/M2.1m-requested-by.md)): `core.compute_request.requested_by`, para a T14 do M2.1a. Os blocos M1.5b a
M1.6c estão fechados e na `main` — o M1.6c pela PR #17, mesclada em 2026-09-29 pelo kakah1327, dono da `fundamentos`
(D-99)
**Etapa:** spec aprovada pelo dono em 2026-09-29; plano aprovado em 2026-09-29; implementação começa pela T1
**Ramo:** `marco1/M2.1m-requested-by`

## Próximo passo

1. **A migration de `core.compute_request.requested_by`**, que a `identidade` pediu à `marco1` no contrato do plano
   da fase 2 do M2.1a: sem ela, a T14 do M2.1a espera.
2. As **telas de acesso**, sobre o casco do M1.6b e as rotas de conta do M2.1a.
3. Olhar a zona de Basileia a 5% (ver *Aberto* no [ESTADO](../ESTADO.md#aberto-e-aguardando-decisão)).

## Depois

As telas de acesso usam o casco do M1.6b e as rotas de conta do M2.1a.

## O que esta frente deve a outras

| Para | O quê | Estado |
|---|---|---|
| `identidade` | convenções da API | ✅ [D-86](../decisoes/D-86-convencoes-da-api-http.md), aplicada pelo M1.6a |
| `identidade` | casco do frontend e kit | ✅ o kit (M1.6a) e o casco (M1.6b) |
| `identidade` | combinar quem preenche `risk_run.requested_by` | ⬜ na spec do M2.1 |

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84; a spec do M1.5b chega aprovada na revisão adversarial |
| 2026-09-26 | spec do M1.5b aprovada pelo dono da frente; plano escrito no ramo; D-85: o dono da frente mescla a própria PR |
| 2026-09-26 | plano do M1.5b aprovado; implementação começa pela T1 |
| 2026-09-27 | M1.5b fechado: T1 a T9, execução real, D-75 a D-81; a PR de implementação fica para o dono abrir |
| 2026-09-28 | M1.6a fechado: T1 a T14 e a T4b, a vitrine aprovada no portão, D-87 a D-93; a PR de implementação fica para o dono abrir |
| 2026-09-28 | M1.6a mesclado (PR #12). M1.6b aberto: telas com as camadas 1 a 3; as 4 e 5 vão para o M1.6c (D-95); 5.1 e 5.2 entram (D-96); frase fixa por número (D-97); 1 dia (D-98); três bibliotecas de gráfico comparadas com dado real, o uPlot escolhido (D-94) |
| 2026-09-29 | M1.6b fechado: T1 a T13, os três portões de mockup, D-94 a D-98; o AALR3 pedido pela tela e calculado em 100,8 s; a PR de implementação fica para o dono abrir |
| 2026-09-29 | M1.6b mesclado (PR #16). M1.6c fechado: T0 a T8, o mockup aprovado, D-99; as tabelas da `fundamentos` viraram contrato; a taxa do anônimo medida; a PR de implementação fica para o dono abrir |
| 2026-09-29 | M1.6c mesclado (PR #17) pelo dono da `fundamentos`, a frente que consome o contrato (D-99). M2.1m aberto: a coluna `core.compute_request.requested_by`; spec com duas rodadas de revisão, aprovada pelo dono; plano com uma |
