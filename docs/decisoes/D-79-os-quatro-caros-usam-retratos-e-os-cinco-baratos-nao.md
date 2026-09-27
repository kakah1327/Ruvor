# D-79 — Os quatro modelos caros usam retratos; os cinco baratos, não

**Status:** aceita · 2026-09-27

## Contexto

Medido em 2026-09-25, no `worker`, sobre o ITUB4: `gru` 58,9 s, `lstm` 40,5 s, `garchnet`
37,6 s, `caviar` 11,9 s; `egarch` e `garch_1_1` 0,1 s cada; `historical`, `monte_carlo` e
`parametric` abaixo de 0,1 s. As três redes são 92% do tempo de um ativo; com o `caviar`,
~99,7%.

## Decisão

**`lstm`, `gru`, `garchnet` e `caviar` guardam e reaproveitam retratos.** Os cinco baratos
(`historical`, `parametric`, `monte_carlo`, `garch_1_1`, `egarch`) **continuam refazendo o
backtest inteiro todo dia**: guardar e validar estado custaria mais que o cálculo.

A lista é literal — `EXPENSIVE = ("caviar", "garchnet", "gru", "lstm")` em
`backend/apps/risk/compute.py` —, **não** derivada de `category == ML`, que por acaso coincide
hoje.

## Consequências

- Os cinco baratos gravam `reused_snapshots` e `trained_snapshots` nulos: "não se aplica", não
  zero.
- O `caviar` não muda de número: já semeava por retreino, e guardar e restaurar o `beta` não
  altera nada. Conferido em dado real no fecho do M1.5b: ele e os cinco baratos saíram iguais
  aos da última execução do `0.2.0` sobre a mesma série.
- Um modelo novo entra na lista só se custar o bastante para que o retrato se pague — e com os
  dois métodos (`restore`, `snapshots`) no motor, que exigem a lista fechada da
  [D-76](D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md) ou sucessora.

Origem: [spec M1.5b — Treino separado da previsão](../specs/M1.5b-treino-separado-da-previsao.md)
(Escopo, RF-10).
