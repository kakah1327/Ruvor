# D-67 — Uma tarefa por (ativo, modelo), e a transação acompanha; restringe o RF-12 do M1.4

**Status:** aceita · 2026-09-25

## Contexto

A [D-07](D-07-resposta-progressiva-modo-a.md) decidiu o modo A: os modelos rápidos respondem na
hora, os de ML preenchem conforme terminam. O [RF-12 do M1.4](../specs/M1.4-motor-de-risco.md#rf-12)
fixou **uma transação por ativo** — os dezoito resultados entram juntos ou não entram —, e com
ela o resultado de um ativo só fica visível quando as três redes terminam, ~2 min depois dos
seis determinísticos, que ficam prontos em segundos.

Havia três cortes possíveis para a fila: por ativo, por (ativo, modelo) e por (ativo, modelo,
nível). O primeiro não muda nada do que se vê. O terceiro parece o mais fino, e o custo dele
não é o que parece: o cache do `_quantile_nn` já é por nível — a rede treina duas vezes hoje,
dentro da mesma instância —, então dividir por nível não economiza nada nas redes; quem paga
são os **baratos**, porque o `runner` cria uma instância por modelo e a reusa nos dois níveis,
e dezoito tarefas duplicariam o `fit` ansioso dos tradicionais e dos GARCH.

## Decisão

**Uma tarefa Celery por (ativo, modelo)** — nove por ativo —, `apps.risk.tasks.compute_asset_model`.
Cada uma chama o `run_experiment` com **um** `model_names` e os dois níveis, reusando o runner
inteiro — isolamento de falha, semeadura, backtests — sem reimplementar nada.

E **a transação acompanha o corte**: cada tarefa grava os seus dois `risk_result` num
`transaction.atomic()` próprio. Isto **restringe o RF-12 do M1.4**, que exigia os dezoito
juntos: sem quebrar aquela transação não há modo A — resultado parcial que ninguém vê não é
resposta progressiva.

## Consequências

- O caminho síncrono **não muda**: `compute_risk` sem `--async` segue com uma transação por
  ativo. A restrição vale para o caminho assíncrono, e o RF-12 do M1.4 continua descrevendo o
  síncrono.
- Uma execução pode ser vista **pela metade** — seis de dezoito linhas com a `risk_run`
  `running` —, e é esse o estado que o M1.6 vai desenhar. Por isso a
  [D-68](D-68-o-estado-da-execucao-mora-no-banco.md) dá à `risk_run` um estado.
- Os dois níveis de um modelo são **tudo ou nada**: a escrita que grava a primeira linha e
  levanta deixa o par de erro do modelo, não uma linha boa mais uma de erro. Um teste prova
  isso, e a mutação que tira o `atomic()` da tarefa reprova nele.
- Separar os nove em nove chamadas de `run_experiment` **não muda número**, e isso foi
  medido: nos testes, com os nove modelos de verdade, síncrono e assíncrono deram as mesmas
  dezoito linhas; e na execução real do M1.5 os 72 resultados saíram iguais aos do M1.4,
  campo a campo.
- A tarefa é idempotente por `(run, model_name)`: se as linhas do modelo já existem, devolve
  sem gravar — repetição do Celery não duplica nem estoura a unicidade `(run, model_name,
  alpha)`.

Origem: [spec M1.5 — Execução assíncrona](../specs/M1.5-execucao-assincrona.md) (RF-01, RF-02).
