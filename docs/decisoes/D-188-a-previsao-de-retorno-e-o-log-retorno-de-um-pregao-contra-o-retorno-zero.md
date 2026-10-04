# D-188 — A previsão de retorno é o log-retorno de um pregão, pontual, medida fora da amostra contra o retorno zero; cada modelo grava também a previsão do próximo pregão

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do [M5.1](../specs/M5.1-retorno.md)
aprovada pelo dono (com a emenda do portão: a previsão do próximo pregão é gravada e mostrada)

## Contexto

A [D-06](D-06-perda-e-o-foco.md) deixou o retorno para o último módulo: o retorno de um dia é quase
imprevisível. O M5.1 o traz como pergunta honesta — os modelos simples erram menos que supor zero? —, na
série e no corte do risco ([D-61](D-61-backend-alimenta-o-motor-por-dataprovider.md),
[D-62](D-62-a-serie-que-vai-ao-motor-e-o-adj-close.md)) e sem olhar à frente
([D-158](D-158-o-var-do-dia-nao-usa-o-retorno-do-dia-e-os-tradicionais-reestimam-a-cada-252-pregoes-restringe-a-d-97.md)).

## Decisão

1. **O que se prevê**: o log-retorno de um pregão, pontual, do `adj_close`, na série e no corte do risco;
   a direção é o sinal da mesma previsão, não um modelo à parte.
2. **Sem olhar à frente**: a previsão do dia *t* usa só o treino e o teste antes de *t*; os parâmetros
   reestimam a cada 252 pregões, em janela que cresce.
3. **A referência é o retorno zero** — o passeio aleatório. A média histórica é modelo, não referência.
4. **Emenda do portão**: cada modelo grava também a previsão do próximo pregão — a posição *n* do mesmo
   walk-forward, sem caso especial —, com a data a que se refere: o primeiro dia de semana depois do
   `as_of_date`, sem o calendário de feriados.

## Consequências

- A previsão do próximo pregão é o mesmo cálculo do teste aplicado ao dia seguinte; acrescentar um retorno
  ao fim do teste e recalcular dá, no novo último dia, o número de antes (o V-02 do M5.1).
- Num feriado, a data da previsão cai num dia sem pregão; a spec registra o risco.
