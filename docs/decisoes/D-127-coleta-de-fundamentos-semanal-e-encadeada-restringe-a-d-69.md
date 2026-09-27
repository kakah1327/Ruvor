# D-127 — A coleta de fundamentos é semanal e encadeia o cálculo; restringe a D-69

**Status:** aceita · 2026-09-27 · restringe a [D-69](D-69-o-agendamento-e-encadeado.md)

## Contexto

A [D-69](D-69-o-agendamento-e-encadeado.md) decidiu que o agendamento é encadeado e que "o Beat
declara duas entradas, não três": o recálculo do risco não tem horário próprio, e a mutação que
acrescenta uma terceira entrada reprova já na contagem das chaves do `CELERY_BEAT_SCHEDULE`.

O M3.1 precisa agendar a coleta da CVM e o cálculo dos indicadores, que é outra corrente: não
lê o risco e não é lido por ele. A CVM regera os zips recentes uma vez por semana; o balanço
muda por trimestre.

## Decisão

**O Beat ganha uma terceira entrada**, `fundamentos` →
`apps.fundamentals.tasks.rotina_fundamentos`, com `_cron("RUVOR_BEAT_FUNDAMENTALS_CRON",
"0 8 * * 1")` — segunda, 8h. A `rotina_fundamentos` enfileira
`chain(importar_fundamentos.s(), calcular_fundamentos.si())`: o cálculo **não tem horário
próprio**, é o segundo elo, imutável. A `importar_fundamentos` captura `CommandError` e devolve
`"FALHOU: ..."`, para o cálculo rodar sobre o que entrou — a regra da D-69.

**A D-69 passa a valer para a corrente de preço e risco**: ela continua com duas entradas, sem
entrada própria para o risco, e nenhuma entrada aponta para `apps.risk.tasks.*`. A guarda de
contagem em `tests/risk/test_beat.py` foi **atualizada, não removida**: o conjunto de chaves
esperado é `{"catalogo", "precos", "fundamentos"}`.

## Consequências

- As 8h dependem do catálogo das 7h por horário, não por ordem — o que a D-69 critica. É
  tolerável aqui porque não há número errado em jogo: a companhia que entrou no catálogo depois
  da coleta é pega na semana seguinte, com o histórico inteiro.
- O P/L fica até uma semana atrás do preço. Recalcular todo dia pediria encadear
  `compute_fundamentals` na `rotina_diaria`, que é arquivo da `marco1`.
- O horário é configuração; a variável chega ao serviço `beat` por uma linha no `environment`
  do `compose.yaml`, e a V-12 prova que ela chega (mutação 41: sem a linha, reprova).
- Uma quarta entrada, de qualquer frente, reprova na mesma guarda até que outra decisão a
  admita.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-28 a RF-31).
