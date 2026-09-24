# D-55 — Métrica de comportamento é imutável, uma linha por (ativo, data de cálculo)

**Status:** aceita · 2026-09-24

## Contexto

A [D-16](D-16-resultado-e-imutavel.md) fixou que resultado nunca se atualiza, e falava de
resultado de risco. O M1.3 é o primeiro bloco a escrever em `gold`, e a pergunta estava
aberta no ESTADO desde o fim do M1.2: uma linha por ativo recalculada, ou uma linha por
(ativo, data de cálculo)?

Métrica de comportamento não é imune ao problema que a D-16 existe para resolver. O provedor
reescreve o histórico a cada evento corporativo ([D-13](D-13-camadas-bronze-prata-ouro.md)),
então o mesmo ativo calculado em duas datas pode discordar sobre o mesmo passado.

## Decisão

`gold.behavior_metric` tem uma linha por `(asset, calculated_at)`, garantida pela restrição
`behavior_metric_asset_calculated_at`. Recalcular **cria** linha; nunca altera a anterior.
Quem lê pega a mais recente, e o índice `behavior_metric_asset_recent`, em
`(asset, -calculated_at)`, é para isso.

`calculated_at` não tem `auto_now_add`: quem grava escreve o `now()`, chamado **uma vez por
execução**, e é isso que torna "uma execução" identificável por consulta.

## Consequências

- A tabela cresce por execução: 4 ativos × 43 linhas (1 métrica + 42 baldes) por rodada. Com
  473 ações e execução diária, ~20 mil linhas por dia. A **política de retenção é pergunta
  real e é do M1.5**, o bloco que agenda a execução; o M1.3 não apaga nada.
- Duas linhas do mesmo ativo podem discordar sobre o passado, e isso é o mecanismo
  funcionando, não defeito. Dizer isso na tela é assunto do M1.6.
- Provado em dado real: duas execuções de `compute_metrics` em 2026-09-24 deixaram oito
  linhas e 336 baldes, com a primeira linha de cada ativo intacta campo a campo.

Origem: [spec M1.3 — Camadas 1 e 2](../specs/M1.3-camadas-1-e-2.md).
