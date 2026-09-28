# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6a ✅ → M1.6b → M1.6c. O M1.6b fecha o Marco 1: digita ITUB4, recebe o comportamento e o risco.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99 — usadas D-85 a D-98.

---

## Agora

**Bloco:** M1.6b — As telas
**Etapa:** spec aprovada pelo dono (2026-09-28), depois de duas rodadas de revisão adversarial; plano a escrever ([`specs/M1.6b-as-telas.md`](../specs/M1.6b-as-telas.md)), com as
decisões D-94 a D-98; comparativo de gráficos em
[`mockups/M1.6b/graficos-comparativo.html`](../mockups/M1.6b/graficos-comparativo.html)
**Ramo:** `marco1/M1.6b-as-telas`, criado em 2026-09-28 a partir da `main` com o M1.6a (PR #12) e a
fase 1 do M2.1a (PR #11) mesclados

## Próximo passo

1. A PR da spec do M1.6b, mesclada pelo dono com a CI verde.
2. O plano, e os três mockups do portão (busca, ativo, estados), nos dois temas.
3. Conferir no log do `worker` o primeiro tique do Beat num dia útil (segunda a sexta, 19h30) — o
   dia comum com pregão novo, que a execução real do M1.5b não teve.
4. Olhar a zona de Basileia a 5%: no `BBDC4`, 159 violações para 111,85 esperadas deram `verde`.
   Não investigado; a tela do M1.6b não mostra a zona até lá (ver *Aberto* no
   [ESTADO](../ESTADO.md#aberto-e-aguardando-decisão)).

## Depois

O M1.6b fecha o Marco 1 e entrega o **casco do frontend**, de que dependem as telas de acesso (bloco
da `marco1`, depois da fase 2 do M2.1a) e o M1.6c — as camadas 4 e 5 na tela, com rotas revisadas
pela `fundamentos` ([D-95](../decisoes/D-95-o-m1-6-em-tres-blocos.md)).

## O que esta frente deve a outras

| Para | O quê | Estado |
|---|---|---|
| `identidade` | convenções da API | ✅ [D-86](../decisoes/D-86-convencoes-da-api-http.md), aplicada pelo M1.6a |
| `identidade` | casco do frontend e kit | 🟡 o kit ✅ (M1.6a); o casco ⬜ (M1.6b) |
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
