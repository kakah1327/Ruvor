# D-148 — O estresse é tabela filha da linha de métrica e sai pela rota `/metrics`

**Status:** aceita · 2026-09-29 · aplica a
[D-56](D-56-tabela-de-metricas-larga-e-serie-em-tabela-propria.md)

## Contexto

O estresse (D-146, D-147) são quatro grupos de medidas por ativo, um por episódio. Três desenhos eram possíveis:
colunas novas em `gold.behavior_metric` (quatro episódios × onze medidas, e uma migration a cada episódio novo);
calcular na leitura, sem gravar (a rota faria cálculo, e o número não teria linha que o datasse); ou uma tabela
filha. E a rota: ampliar `/metrics` ou criar uma nova.

## Decisão

1. **`gold.stress_episode`, filha de `gold.behavior_metric`**, uma linha por `(metric, episode)`, com `CASCADE` —
   o molde do histograma da D-56: a linha de estresse não tem vida própria.
2. **Gravada no mesmo cálculo e na mesma transação** que a linha de métrica e os baldes, pelo `calcular_metricas`
   de hoje — rotina diária e cálculo sob demanda. Nenhuma tarefa nova.
3. **Cada linha guarda a definição que usou** (início e fim do episódio) e a janela de pregões, para dizer de que
   recorte fala mesmo depois de a lista mudar.
4. **Sai pela rota `/metrics`**, num campo `stress` ao lado do `histogram`, e não por rota nova: é a mesma linha,
   do mesmo instante; uma rota à parte seria um pedido a mais por carga da tela contra a taxa do anônimo
   ([D-109](D-109-toda-rota-da-api-tem-taxa.md)), e a tela teria de casar duas respostas.

## Consequências

- Episódio novo não pede migration: é linha nova. Por isso o código do episódio é texto livre na tabela e no esquema
  OpenAPI; só o motivo de "sem dado" é lista fechada.
- A rota `/metrics` cresce por acréscimo; nenhum campo existente muda.
- A linha de métrica gravada antes do M3.3 não tem estresse, e a rota devolve `stress: []` até o próximo cálculo.

Origem: [spec M3.3 — Estresse histórico](../specs/M3.3-estresse-historico.md).
