# D-158 — Nos nove modelos, o VaR do dia *t* não usa o retorno de *t* nem posteriores, e o número mostrado tem a data do último pregão; os tradicionais reestimam a cada 252 pregões em janela expansiva; restringe a D-97

**Status:** aceita · 2026-10-02 · com a aprovação da [spec do M1.4b](../specs/M1.4b-correcao-do-motor.md)

## Contexto

Até o motor `0.3.0`, o GARCH e o EGARCH comparavam o retorno do dia `pos` com a σ do dia `pos + 1`, já calculada com
o retorno de `pos` — o backtest deles era otimista, e o último ponto da série era a previsão para o pregão seguinte,
rotulada com a data do último. A [D-64](D-64-veredito-de-adequacao-e-kupiec-e-christoffersen.md) afirma que "o número
que o usuário vê é o do último pregão", e para o GARCH isso não valia. E o `run_experiment` ajusta cada modelo uma vez,
nos 252 primeiros retornos: os três tradicionais devolviam um VaR constante, um quantil de dez anos atrás.

As frases avançadas `risco.perda95` e `risco.perda99`, que o M2.3 aprovou no portão de mockup, dizem como o número é
estimado e precisam acompanhar.

## Decisão

1. **Nenhum dos nove modelos usa, para o VaR do dia *t*, o retorno do dia *t* ou posterior**, e o último ponto da
   série de cada um tem a data do último pregão. Nos seis que se atualizam a cada pregão, ele é o VaR do último pregão
   previsto com os dados até a véspera; nos três tradicionais, o valor do último trecho, estimado sobre os retornos
   conhecidos no início dele. Confirma a frase da D-64 para os nove.
2. **Os tradicionais reestimam a cada 252 pregões, numa janela que cresce desde o primeiro retorno** — a mesma
   cadência do GARCH, das redes e do CAViaR. Restringe o "ajuste uma vez" do `run_experiment` para eles.
3. **Restringe o item 2 da [D-97](D-97-no-marco-1-cada-numero-tem-uma-frase-fixa.md):** as frases do RF-14 da spec são
   aprovadas no portão da spec, sem mockup, porque só o texto muda, num lugar cujo desenho o portão do M2.3 já
   aprovou.

## Consequências

- Os vereditos do GARCH e do EGARCH mudam: com a correção eles têm mais violações — o resultado certo, não regressão.
  A execução real do M1.4b registra a mudança por modelo no [ESTADO](../ESTADO.md#m14b--correção-do-motor).
- O número de hoje dos tradicionais usa os dados até o início do último trecho, de 0 a 251 pregões de defasagem; a
  janela móvel diária foi considerada e preterida pelo dono, pela coerência com a cadência dos outros seis.
- Mostrar o VaR de amanhã seria número novo, com tela e frase próprias — outro bloco.
- O mockup aprovado do M2.3 (`docs/mockups/M2.3/risco.html`) fica como registro do portão, com a frase velha; o índice
  dos mockups marca que ele não reflete o M1.4b.

Origem: [spec M1.4b — Correção do motor](../specs/M1.4b-correcao-do-motor.md) (RF-01 a RF-09, RF-14).
