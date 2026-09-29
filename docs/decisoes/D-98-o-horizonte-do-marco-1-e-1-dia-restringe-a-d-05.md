# D-98 — O horizonte do Marco 1 é 1 dia; restringe a D-05

**Status:** aceita · 2026-09-28 · restringe a [D-05](D-05-horizonte-semanas-primeiro.md)

## Contexto

A D-05 fixou o horizonte de **semanas** na primeira versão, porque quem pergunta "se eu aplicar"
pensa em semanas. O motor migrado no F2a calcula VaR de **1 dia**, os backtests do M1.4 validam 1
dia (~2.240 pregões de teste por ativo), e nenhuma spec — M1.4, M1.5, M1.6a — tratou a diferença.
A primeira tela, no M1.6b, precisava escolher o que mostrar.

A saída de mostrar semanas pela regra da raiz do tempo foi descartada: daria um número sem backtest
por trás, contra o diferencial do produto — a validação estatística do que se mostra.

## Decisão

**O Marco 1 mostra o VaR de 1 dia**, o único horizonte calculado e validado. O horizonte de semanas
fica para um bloco próprio, que precisa assumir o que a D-05 já avisava: janelas sobrepostas, com
correção estatística, porque ~120 períodos independentes em dez anos quase não detectam nada.

## Consequências

- A tela diz "em 1 dia" em toda perda que mostra.
- A PRODUTO §4 passa a dizer que o Marco 1 é de 1 dia.
- A D-05 continua valendo como direção; o que muda é a primeira versão.

Origem: [spec M1.6b — As telas](../specs/M1.6b-as-telas.md).
