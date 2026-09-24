# D-57 — A janela estatística do Marco 1 é 60 meses

**Status:** aceita · 2026-09-24

## Contexto

Volatilidade longa, beta, correlação, assimetria, curtose e histograma precisam, cada um, de
uma janela. Escolher uma por métrica é defensável estatisticamente e indefensável na tela: o
usuário lê os números lado a lado, na mesma linha, e supõe que falam do mesmo período.

## Decisão

Uma constante, `STATISTICAL_WINDOW = 60` (meses), serve a `volatility_60m`, `beta_60m`,
`correlation_60m`, `skewness`, `excess_kurtosis`, `statistical_observations` e aos 42 baldes
do histograma. A volatilidade de 12 meses continua existindo como coluna própria, para leitura
de curto prazo; ela é a exceção declarada, não uma segunda janela estatística.

Sessenta meses é a convenção mais próxima do mercado para beta e cabe nos dez anos que os
quatro ativos coletados têm.

## Consequências

- Os números da mesma linha são comparáveis entre si, e `statistical_observations` diz, numa
  coluna só, sobre quantos retornos todos eles foram calculados. Na execução real de
  2026-09-24 foram 1.248 retornos para PETR4, VALE3 e ITUB4, e 1.247 para o IBOV.
- **É escolha, não lei.** Quando a cobertura passar dos quatro ativos, ação recém-listada terá
  beta nulo por anos. A saída — beta de 12 meses como segunda coluna — é barata, e o gatilho é
  a cobertura crescer, não uma revisão de método.
- Menos de 30 pares no emparelhamento com o índice gravam beta e correlação nulos, com
  `benchmark_observations` preenchido: o mínimo diz que o número não merece confiança, não que
  seja desconhecido.

Origem: [spec M1.3 — Camadas 1 e 2](../specs/M1.3-camadas-1-e-2.md).
