# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6a ✅ → M1.6b. É o fim do Marco 1: digita ITUB4, recebe o comportamento e o risco.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99 — usadas D-85 a D-93.

---

## Agora

**Bloco:** M1.6a — Fundação da aplicação, **fechado em 2026-09-28**; o próximo é o M1.6b
**Etapa:** implementação e FECHA feitos no ramo; a vitrine do kit aprovada no portão de mockup
(2026-09-28); **PR de implementação a abrir pelo dono da frente**
([D-85](../decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md))
**Ramo:** `marco1/M1.6-aplicacao-web`, com a spec
([`specs/M1.6a-fundacao-da-aplicacao.md`](../specs/M1.6a-fundacao-da-aplicacao.md)), o plano
([`planos/M1.6a-fundacao-da-aplicacao.md`](../planos/M1.6a-fundacao-da-aplicacao.md)) e as
decisões D-87 a D-93

## Próximo passo

1. Abrir a PR de implementação do M1.6a e mesclá-la com a CI verde
   ([D-85](../decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)). Ela toca arquivos comuns —
   `settings.py`, `urls.py`, `compose.yaml`, `test_esquemas.py` —, declarados na spec.
2. **M1.6b — As telas**: casco, busca e tela do ativo, sobre o kit e a API do M1.6a, **cada tela
   com mockup aprovado antes do código** ([PROCESSO §7](../PROCESSO.md#7-portão-de-mockup)). A
   spec começa pelo que o M1.6a deixou: o `/risk` com `latest`, `in_progress` e `request`, o
   cálculo de um ativo novo em ~100 s, e os ícones do conjunto fechado.
3. Conferir no log do `worker` o primeiro tique do Beat num dia útil (segunda a sexta, 19h30): é o
   dia comum com um pregão novo de verdade, que a execução real do M1.5b não teve — a coleta de
   domingo não trouxe pregão (ver o [ESTADO](../ESTADO.md)). O Beat ficou parado durante o M1.6a
   e voltou depois da execução real.
4. Olhar a zona de Basileia a 5%: na execução real do M1.6a, os 18 resultados do `BBDC4` saíram
   `verde`, inclusive o `historical` a 5% com 159 violações para 111,85 esperadas. Não
   investigado (ver *Aberto* no [ESTADO](../ESTADO.md#aberto-e-aguardando-decisão)).

## Depois

O M1.6b fecha o Marco 1. O que ele entrega é esperado pela `identidade`: o **casco do
frontend**, de que dependem as telas de login do M2.1 — o kit já está entregue
([contrato](../FRENTES.md#contratos-entre-frentes)).

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
