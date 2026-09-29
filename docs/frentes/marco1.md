# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6a ✅ → M1.6b → M1.6c. O M1.6b fecha o Marco 1: digita ITUB4, recebe o comportamento e o risco.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99 — usadas D-85 a D-98.

---

## Agora

**Bloco:** M1.6b — As telas, **fechado em 2026-09-29**; o próximo é o M1.6c
**Etapa:** implementação e FECHA feitos no ramo; **PR de implementação a abrir pelo dono da frente**
([D-85](../decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md))
**Ramo:** `marco1/M1.6b-as-telas`, com a spec, o plano, os três mockups aprovados e as decisões D-94 a
D-98

## Próximo passo

1. Abrir as PRs do M1.6b — spec, plano e implementação — e mesclá-las com a CI verde.
2. **M1.6c — Fundamentos e contexto na tela**: as camadas 4 e 5, com as rotas escritas pela `marco1` em
   `apps/api` e revisadas pela `fundamentos` ([D-95](../decisoes/D-95-o-m1-6-em-tres-blocos.md)). A faixa
   da `marco1` tem uma decisão livre (D-99); a spec reserva a próxima faixa.
3. As **telas de acesso**, depois da fase 2 do M2.1a, sobre o casco do M1.6b.
4. Olhar a zona de Basileia a 5% (ver *Aberto* no [ESTADO](../ESTADO.md#aberto-e-aguardando-decisão));
   a tela não a mostra até lá.

## Depois

O M1.6c completa a tela com as camadas 4 e 5; as telas de acesso usam o casco do M1.6b.

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
