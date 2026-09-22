# D-52 — A janela de preços só cresce: dez anos na primeira carga, nada apagado depois

**Status:** aceita · 2026-09-21

## Contexto

A opção de produto foi "últimos dez anos". Uma janela que descarta o que passa de dez anos
contradiz a `bronze` imutável e o "nunca apagar" da [D-48](D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md).

## Decisão

A carga inicial pede `period1` = data da coleta com `year − 10` (meia-noite em São Paulo);
a incremental pede da última data − 7 dias. Nada em `silver.price` é apagado. Dez anos é piso,
não teto.

## Consequências

- A sobreposição de 7 dias corrige o pregão parcial do dia da coleta e o que o Yahoo revisou.
- Quem quiser mais história roda `--full` com outro `period1` — outro bloco, se for preciso.

Origem: [spec M1.2 — Ingestão de preços](../specs/M1.2-ingestao-de-precos.md).
