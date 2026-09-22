# D-53 — Dividendo ou desdobramento novo rebusca a série inteira

**Status:** aceita · 2026-09-21

## Contexto

A cada evento corporativo o Yahoo recalcula o `adjclose` de toda a série anterior — é a
reescrita retroativa que motiva a `bronze` ([D-13](D-13-camadas-bronze-prata-ouro.md)). Uma
coleta incremental só traz a cauda; o ajustado histórico ficaria velho sem ninguém notar.

## Decisão

Na coleta incremental, se a resposta traz um evento `(ativo, data, tipo)` que ainda não existe
em `silver.corporate_event`, o comando pede de novo a série inteira desde a primeira data
conhecida, e é essa resposta que conforma. `--full` faz o mesmo à força.

## Consequências

- A regra não depende de coleta anterior nem de fuso: é presença do evento na `silver`.
- **Limitação aceita:** evento acrescentado com data anterior à janela incremental não
  aparece na resposta e não dispara rebusca; `--full` cobre.
- Cada rebusca é uma linha a mais na `bronze` da mesma coleta — a anterior fica, para prova.

Origem: [spec M1.2 — Ingestão de preços](../specs/M1.2-ingestao-de-precos.md).
