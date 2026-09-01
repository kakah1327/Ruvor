# D-15 — Todo resultado carrega um manifesto de execucao

**Status:** aceita · 2026-08-29

## Contexto

Um numero de risco isolado nao e interpretavel nem auditavel. E mudancas silenciosas de hiperparametro tornam o historico incomparavel sem ninguem perceber.

## Decisão

Todo resultado registra: **algoritmo e versao do codigo, hiperparametros, base de dados e data de coleta, semente aleatoria, quando rodou e a pedido de quem.**

## Consequências

- E parte do modelo de dominio, nao log paralelo.
- Se alguem mudar a janela da LSTM de 20 para 30 dias, o sistema sabe que os numeros anteriores sao de outro modelo.
- Fecha a pendencia de reprodutibilidade das redes neurais, que hoje nao fixam semente.
