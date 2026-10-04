# D-191 — O retorno mora na app `apps/returns`, em `gold.return_run` e `gold.return_result`, imutáveis, com manifesto; roda no quinto elo da `rotina_diaria` e na cadeia sob demanda; sai por `GET /api/v1/assets/{ticker}/returns`, sem pedido próprio — estende a D-91

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do [M5.1](../specs/M5.1-retorno.md)
aprovada pelo dono

## Contexto

A `rotina_diaria` encadeia presas → preços → métricas → risco
([D-91](D-91-a-rotina-diaria-e-precos-metricas-risco-estende-a-d-69.md)). A app do risco já tem a fila, as
execuções presas e os retratos; retorno não é risco.

## Decisão

1. **App nova, `apps/returns`**, que entra na cerca da `marco1`, com `gold.return_run` (o manifesto, sem
   semente) e `gold.return_result` (um por modelo), imutáveis ([D-16](D-16-resultado-e-imutavel.md)), o
   esquema no `db_table` ([D-38](D-38-public-guarda-o-encanamento.md)), uma transação por ativo.
2. **O quinto elo da `rotina_diaria`**, `calcular_retornos`, depois do leque do risco: roda junto do risco
   do mesmo tique, não depois dele, e **nunca propaga exceção** — é o único elo que pode faltar sem
   prejudicar o risco. Na cadeia sob demanda, depois das métricas e antes da abertura do risco; a falha
   dele não fecha o pedido.
3. **A rota** `GET /api/v1/assets/{ticker}/returns` ([D-86](D-86-convencoes-da-api-http.md)), lida também
   pela chave pessoal ([D-108](D-108-a-api-aceita-chave-pessoal-de-leitura.md)); `latest` é a execução de
   maior `calculated_at`. **Sem pedido próprio**: o retorno chega com o cálculo do risco.
4. A lista de modelos é a constante `RETURN_MODELS`, nunca o registry; registry incompleto é erro
   ([D-66](D-66-registry-incompleto-e-erro-restringe-o-silencio-do-motor.md)).

## Consequências

- A `rotina_diaria` passa a ter cinco elos, e o `CELERY_BEAT_SCHEDULE` continua com quatro entradas.
- A tabela cresce uma execução por ativo coberto por dia útil.
