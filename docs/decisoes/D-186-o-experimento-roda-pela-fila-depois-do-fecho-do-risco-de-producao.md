# D-186 — O experimento roda pela fila depois do fecho do risco de produção, reaproveitando os retratos, numa tarefa por ativo, sem entrada no Beat; o operador tem `compute_lab`

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do
[M2.4](../specs/M2.4-regime-de-laboratorio.md) aprovada pelo dono

## Contexto

Medido na spec, o experimento custa ~4–5 s por ativo com os retratos da produção e ~173 s sem eles, com
pico de 1,35 GiB num processo. Rodar antes da produção treinaria o que a produção treina logo depois;
rodar no Beat diário recalcularia o que não muda.

## Decisão

1. **O fecho `ok` ou `partial` do risco registra um callback de `transaction.on_commit`** que consulta se
   o experimento é devido e o enfileira — a consulta e o enfileiramento juntos, depois do commit, fora da
   trava do ativo —, num `try` que nunca deixa o fecho falhar por ele. Não é registrado com `failed` nem
   quando o fecho não escreve.
2. **Uma tarefa por ativo**, `apps.risk.tasks.calcular_laboratorio`, que nunca levanta: sem estado
   `running` e sem trava no cálculo; a trava do ativo
   ([D-92](D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md)) só na escrita, que confere se já
   há `ok` da identidade antes de gravar; o índice único como guarda
   ([D-90](D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md), item 3).
3. **`manage.py compute_lab [TICKER ...]`**, síncrono, para o operador. **Nada no
   `CELERY_BEAT_SCHEDULE`**, e nem `--full` nem `--force`.

## Consequências

- Ativo novo, década completada, `partial` da véspera e motor novo disparam sozinhos. Com motor novo (o
  `0.5.0` do M5.1, por exemplo), a produção retreina as linhagens no recálculo da versão nova, e o
  experimento, enfileirado no fecho dele, reaproveita os retratos recém-treinados; **só treina do zero se
  `compute_lab` rodar antes desse recálculo**.
- A tela não tem estado "calculando"; uma corrida custa um cálculo a mais e grava um só `ok`.
- Na fase A da execução real (2026-10-04), o IBOV pelo fecho e quatro ativos pelo comando, ~4 s cada,
  nenhum retrato treinado.
