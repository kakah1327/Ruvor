# D-89 — A `web` enfileira pelo nome da tarefa, e os nomes são contrato interno

**Status:** aceita · 2026-09-28

## Contexto

A imagem da `web` não tem o motor — só a do `worker` o instala
([D-81](D-81-imagem-do-worker-travada-pelo-lock-e-versoes-na-identidade.md)). Toda tarefa de
risco o importa no topo (`apps/risk/tasks.py`, `compute.py`, `snapshots.py`), e
`apps/assets/tasks.py` o arrasta, porque importa `recalcular_cobertos` de `apps.risk.tasks`. O
M1.6a publica a primeira rota que enfileira trabalho — o `POST /api/v1/assets/{ticker}/risk` —, e
ela roda na `web`.

## Decisão

1. **A `web` enfileira por `send_task("<nome registrado>", …)`**, nunca importando um `tasks.py`
   que importe o motor. A chamada vai no `transaction.on_commit` do pedido, para que o `worker`
   nunca receba um pedido que outra conexão ainda não vê.
2. **Os nomes de registro das tarefas passam a ser contrato interno** — hoje, o que a API usa é
   `apps.assets.tasks.calcular_sob_demanda`. Renomear uma tarefa é mudar contrato.
3. **A app da API não importa o motor, nem direta nem indiretamente**: nenhum módulo de
   `apps/api/`, nem `config.urls` com ela incluída, importa `engine`, `tensorflow`, `pandas`,
   `apps.risk.tasks`, `apps.risk.compute`, `apps.risk.snapshots` ou `apps.assets.tasks`.
4. **Broker recusando não é 500**: o pedido passa a `failed` com o erro, e a resposta continua
   202 com o pedido — o estado diz o que houve.

## Consequências

- Um teste lê do código de `apps/api/`, por `ast`, cada nome passado a `send_task` e confere, em
  subprocesso, que ele está no registro do `worker`; outro importa todos os submódulos de
  `apps.api` com um bloqueador em `sys.meta_path` para os módulos proibidos
  ([spec do M1.6a](../specs/M1.6a-fundacao-da-aplicacao.md#rf-19), V-10 e V-18).
- O domínio do pedido mora em `apps/api/ondemand.py`, que só importa modelos, `django.db`, as configurações e a aplicação Celery (`config.celery.app`, para o `send_task`) — o único caminho indireto que o RF-10 vigia, e o V-10 prova que ele não arrasta o motor — é
  o que a `web` e o `worker` compartilham.
- Tarefa nova que a `web` precise enfileirar segue a mesma forma, e o nome entra no teste pelo
  próprio código.
