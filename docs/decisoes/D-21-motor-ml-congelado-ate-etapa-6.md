# D-21 — Motor de ML nao e alterado antes da Etapa 6

**Status:** aceita · 2026-08-29

## Contexto

As Tabelas 1 e 2 do Capitulo 4 do TCC ja foram geradas com a configuracao atual. Trocar o backend do Keras mudaria a geracao de numeros aleatorios e a implementacao das operacoes internas.

## Decisão

**Nenhuma mudanca de backend ou biblioteca de ML antes da conclusao da Etapa 6.**

## Consequências

- Mover arquivos e seguro; trocar motor nao.
- Excecao necessaria: **fixar a semente**, que e pre-requisito da Etapa 6 e muda os numeros da Tabela 1 (gerada sem semente).
- Ordem correta: corrigir a semente -> refazer a Tabela 1 -> rodar a Etapa 6, tudo na mesma configuracao.
