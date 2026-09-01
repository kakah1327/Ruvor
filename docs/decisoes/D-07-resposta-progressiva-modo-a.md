# D-07 — Resposta progressiva: rapidos na hora, ML depois

**Status:** aceita · 2026-08-29

## Contexto

Os algoritmos tem custos assimetricos: os estatisticos resolvem em segundos, as redes neurais precisam ser treinadas e levam minutos — em qualquer implementacao. E a carteira do usuario e sempre uma combinacao nova, que nao pode ter sido pre-calculada.

## Decisão

Quando o usuario dispara uma analise, os **modelos rapidos respondem imediatamente** e os de Machine Learning **preenchem a tela conforme terminam**.

## Consequências

- Preserva o diferencial (todos os algoritmos, de verdade) sem deixar a tela vazia.
- Exige fila e execucao assincrona (D-14).
- Para ativos individuais isso vira excecao de primeira consulta, nao regra — ver D-18 e D-19.
