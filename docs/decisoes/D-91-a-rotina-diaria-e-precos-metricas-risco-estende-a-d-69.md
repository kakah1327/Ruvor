# D-91 — A rotina diária é `preços → métricas → risco`; estende a D-69

**Status:** aceita · 2026-09-28 · estende a [D-69](D-69-o-agendamento-e-encadeado.md)

## Contexto

A [D-69](D-69-o-agendamento-e-encadeado.md) encadeou o recálculo do risco à coleta de preços: a
`rotina_diaria` enfileirava `importar_precos → recalcular_cobertos`. As métricas de
comportamento ficaram fora: `compute_metrics` só rodava à mão, e uma tela mostraria retornos e
volatilidade parados no dia em que alguém rodou o comando, ao lado de um risco de hoje.

## Decisão

**A `rotina_diaria` passa a enfileirar três elos**:
`chain(importar_precos.s(), calcular_metricas.si(), recalcular_cobertos.si())`, pelo mesmo
mecanismo da D-69 — a entrada `precos` do Beat não muda, e as métricas não ganham horário
próprio.

- **A tarefa nova é `apps.analytics.tasks.calcular_metricas`**, registrada como as outras
  (`app.task(name=...)(funcao)`), e o nome é contrato
  ([D-89](D-89-a-web-enfileira-pelo-nome-da-tarefa.md)).
- **Ela não rompe o elo por ativo falho**, como a coleta de preços já não rompe: cada ativo grava
  em transação própria, e a tarefa captura a falha agregada e devolve `"FALHOU: …"`. Outra
  exceção propaga — o cálculo não chegou a rodar, e o risco não deve seguir sobre isso.
- **O elo é imutável** (`.si()`), pela mesma razão que a D-69 dá para o recálculo.

## Consequências

- A mesma sequência é a da cadeia sob demanda por ticker
  ([D-90](D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md)): coleta, métricas,
  abertura do risco.
- A rotina ganha o tempo das métricas dos ativos cobertos — no pedido do `BBDC4` da execução real,
  métricas e abertura somaram 3,84 s.
- Mudar a ordem ou tirar um elo é mudar esta decisão; o teste da corrente confere os três nomes na
  ordem ([spec do M1.6a](../specs/M1.6a-fundacao-da-aplicacao.md#rf-21), V-20).
