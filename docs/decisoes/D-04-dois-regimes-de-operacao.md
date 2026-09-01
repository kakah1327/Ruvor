# D-04 — Dois regimes: laboratorio e producao

**Status:** aceita · 2026-08-29

## Contexto

O periodo 2015-2024 serve para provar cientificamente que os modelos funcionam. Mas o usuario quer saber o risco de hoje, nao o de 2017.

## Decisão

O sistema opera em **dois regimes distintos**: laboratorio (2015-2024, validacao do metodo) e producao (dados atuais, atualizados em escala diaria — nada tick a tick).

## Consequências

- Sao dois caminhos de codigo diferentes sobre o mesmo motor.
- O regime de laboratorio justifica confiar no numero; o de producao entrega o numero.
- Granularidade diaria mantem o volume de dados pequeno (ver D-13).
