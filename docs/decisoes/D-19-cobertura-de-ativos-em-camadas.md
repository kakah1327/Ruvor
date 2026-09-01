# D-19 — Cobertura de ativos em camadas

**Status:** aceita · 2026-08-29

## Contexto

A B3 tem ~400 papeis, mas a maioria quase nao e negociada. Pre-calcular todos custaria caro sem retorno.

## Decisão

**Ativos liquidos ficam pre-calculados** (resposta imediata). **Cauda longa entra pelo modo A** na primeira consulta e passa a ser coberta dali em diante.

## Consequências

- O modo A vira excecao de primeira consulta, nao regra.
- Exige um catalogo de ativos da B3, mantido atualizado — empresa entra, sai e muda de codigo.
- A politica de cobertura (quais ativos, com que frequencia retreinar) e decisao de produto com efeito direto no custo de servidor.
