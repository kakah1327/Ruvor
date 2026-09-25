# D-69 — O agendamento é encadeado, não por horário paralelo

**Status:** aceita · 2026-09-25

## Contexto

A [D-14](D-14-celery-e-redis.md) registra o agendamento entre as razões de o Celery existir,
e até o M1.5 nada rodava sozinho. Três rotinas precisam de agenda: o catálogo, os preços e o
recálculo do risco. O recálculo lê `silver.price`; dispará-lo antes da ingestão produziria
manifesto apontando para dado velho — e o manifesto grava `price_run`, então o número ficaria
**auditavelmente** errado.

Dar ao recálculo um horário "com folga" depois do dos preços é coincidência, não ordem: basta
a coleta atrasar um dia.

## Decisão

**O Beat declara duas entradas, não três.**

| Entrada | Tarefa | Padrão |
|---|---|---|
| `catalogo` | `apps.assets.tasks.importar_ativos` | `0 7 * * 1` — segunda, 7h |
| `precos` | `apps.assets.tasks.rotina_diaria` | `30 19 * * 1-5` — segunda a sexta, 19h30 |

O recálculo **não tem horário próprio**: é o segundo elo de uma corrente que começa na
ingestão de preço. A `rotina_diaria` existe porque o `beat_schedule` aceita nome de tarefa,
não `chain`; ela enfileira `chain(importar_precos.s(), recalcular_cobertos.si())`. O segundo
elo é **imutável** — com `.s()`, o texto devolvido pela coleta chegaria como
`calculated_at_iso` do recálculo, e o `datetime.fromisoformat` estouraria.

**E o elo não se rompe por ativo falho.** O `import_prices` levanta `CommandError` quando um
ticker falha ([D-54](D-54-transacao-por-ativo-restringe-a-d-48.md)); a `importar_precos`
captura esse erro e devolve `"FALHOU: ..."`. A corrente segue para o risco com ou sem ativo
falho; só não segue se a ingestão não chegou a rodar — qualquer outra exceção propaga.

## Consequências

- Os dois horários são configuração (`RUVOR_BEAT_ASSETS_CRON`, `RUVOR_BEAT_PRICES_CRON`),
  **com padrão**, no fuso de São Paulo que o Celery herda do `TIME_ZONE`. Os padrões são
  chute declarado: hospedagem é pendência aberta, e o dado do Yahoo demora a estabilizar
  depois do fechamento da B3.
- O cron é lido por **argumentos nomeados**, nunca `crontab(*campos)`: a ordem posicional do
  `crontab` do Celery é `minute, hour, day_of_week, day_of_month, month_of_year`, e a leitura
  posicional de `"30 19 * * 1-5"` agendaria "todo dia, de janeiro a maio".
- Agendar o recálculo à parte custaria um manifesto apontando para dado velho sem erro
  nenhum. Por isso a mutação que acrescenta uma terceira entrada reprova já na contagem das
  chaves do `CELERY_BEAT_SCHEDULE`, e nenhuma entrada pode apontar para `apps.risk.tasks.*`.
- Um tique real, medido no fecho do M1.5: `rotina_diaria` → `import_prices` no Yahoo (0,8 s)
  → `recalcular_cobertos` → quatro execuções `ok`, 4 min 40 s depois do disparo.
- O `recalcular_cobertos` agenda **o que tem preço**, que é a
  [D-51](D-51-cobertura-e-o-que-tem-preco.md) valendo. A política de cobertura continua
  pendência de produto ([D-19](D-19-cobertura-de-ativos-em-camadas.md)).

Origem: [spec M1.5 — Execução assíncrona](../specs/M1.5-execucao-assincrona.md) (RF-09, RF-10,
RF-11).
