# D-159 — A linha de base numérica passa a ser a do motor `0.4.0`; restringe a D-44

**Status:** aceita · 2026-10-02 · com a aprovação da [spec do M1.4b](../specs/M1.4b-correcao-do-motor.md)

## Contexto

A linha de base numérica (`engine/tests/baseline/valores.json`) provava, desde o F2a, que o motor reproduz o protótipo
VaR Lab, e a [D-44](D-44-o-motor-entra-no-estilo.md) a usa como reforço de que a formatação do motor não mudou
comportamento numérico. O script da captura original nunca foi versionado: o arquivo "não podia ser regenerado". O
M1.4b corrige cinco famílias — `parametric`, `historical`, `monte_carlo`, `garch_1_1` e `egarch` — que o protótipo
calculava com os mesmos defeitos.

## Decisão

**A linha de base deixa de ser a paridade com o protótipo VaR Lab nas cinco famílias corrigidas** — de propósito,
porque o protótipo tinha os mesmos defeitos —, passa a ser a do motor `0.4.0`, é **recapturada por script versionado**
(`engine/tests/baseline/capturar.py`) e continua valendo **só no hospedeiro Windows**. As duas entradas do `caviar`
ficam como estavam.

## Consequências

- O que se perde: a prova de que o motor reproduz o VaR Lab nas cinco famílias. O que se ganha: a prova de que o motor
  corrigido não muda sem querer, e um arquivo que se regenera.
- A captura do M1.4b mudou as dez entradas das cinco famílias e deixou as duas do `caviar` iguais (V-05); a linha de
  base no hospedeiro, 25 verdes.
- A CI continua rodando o motor sem ela, e a não portabilidade entre plataformas segue aceita (ESTADO, *Dívida
  registrada*).

Origem: [spec M1.4b — Correção do motor](../specs/M1.4b-correcao-do-motor.md) (RF-11).
