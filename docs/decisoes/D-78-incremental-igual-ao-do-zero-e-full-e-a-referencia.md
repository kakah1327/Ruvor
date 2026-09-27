# D-78 — O critério é incremental igual ao do zero, e `--full` é a referência

**Status:** aceita · 2026-09-27

## Contexto

Reaproveitar o que já foi treinado é o que torna a rotina diária barata
([D-77](D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md)). O risco é o
reaproveitamento produzir, em silêncio, um número diferente do que um cálculo completo daria —
e ninguém ter como saber qual dos dois está no banco.

## Decisão

**Para a mesma série, semente e versão do motor, o cálculo a partir de retratos produz o mesmo
que o cálculo do zero:**

- no motor, a mesma `var_series` inteira, ponto a ponto, com **igualdade exata**, para cada
  (modelo caro, nível) — não só o que o `risk_result` guarda, que com dez casas não enxergaria
  uma diferença num ponto do meio;
- no banco, os dezoito `risk_result` iguais campo a campo, **exceto** `id`, `run`,
  `reused_snapshots` e `trained_snapshots`; na `risk_run`, exceto `id`, `calculated_at`,
  `finished_at` e `full_recompute`. **A lista é fechada.**

Diferença de ponto flutuante, se aparecer, é **escalação ao humano**, com o número e a causa —
não tolerância decidida por quem implementa.

**`compute_risk --full` é a referência e a saída de emergência**: não lê retrato nenhum, treina
tudo e grava o que treinar, sem duplicar o que já existia. Vale nos dois caminhos; no
assíncrono, viaja na `risk_run` (`full_recompute`), que a tarefa por (ativo, modelo) lê.

**O manifesto diz de onde veio o número**: cada `risk_result` dos modelos caros registra
`reused_snapshots` e `trained_snapshots` — `0` e todos no `--full`; nulos nos baratos, no par
de erro e nas execuções anteriores ao bloco.

## Consequências

- Não existe "modo rápido aproximado": ou o incremental é igual, ou é defeito.
- Provado com o motor real (V-02: série do zero, +1 pregão sem cruzar ponto, +1 cruzando) e em
  dado real no fecho do M1.5b: o incremental sobre a mesma série saiu igual ao `--full`
  campo a campo, nos quatro ativos.
- O `--full` é também a saída se um retrato defeituoso escapar: com a versão do motor na
  identidade, subir o `engine_version` é a outra.

Origem: [spec M1.5b — Treino separado da previsão](../specs/M1.5b-treino-separado-da-previsao.md)
(RF-06 a RF-09).
