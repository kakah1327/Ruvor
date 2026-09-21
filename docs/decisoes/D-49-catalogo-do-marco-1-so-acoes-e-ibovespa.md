# D-49 — O catálogo do Marco 1 é só ações e o Ibovespa

**Status:** aceita · 2026-09-15

## Contexto

A listagem da B3 traz 3.525 registros: companhias, fundos, ETFs, BDRs, pré-listagens. O
produto é "risco em ações" ([PRODUTO](../PRODUTO.md)), e a camada 2 compara com o Ibovespa.

## Decisão

Vira `silver.asset` só o código de ação — ON, PN e UNIT, regex `^[A-Z0-9]{4}(3|4|5|6|7|8|11)$`
— de companhia `type == "1"` com `hasQuotation == "S"`, mais a linha fixa do Ibovespa
(`IBOV`, `^BVSP`). FIIs, BDRs, ETFs, debêntures e recibos ficam na `bronze` e não entram.

## Consequências

- **Ações de balcão organizado (sufixo `B`, mercado SOMA) ficam fora** — 8 companhias na
  coleta de 2026-09-21. É decisão de cobertura ([D-19](D-19-cobertura-de-ativos-em-camadas.md))
  ainda não tomada; mudar o regex é uma linha, e o relatório do `import_assets` já conta os
  casos. Registrada como dívida no [ESTADO](../ESTADO.md#dívida-registrada).
- FIIs, BDRs e ETFs são candidatos, não requisitos.
- A composição do Ibovespa tem endpoint próprio na B3 (76 papéis) e é o candidato natural a
  "ativos líquidos" da D-19 — decisão do M1.2 ou posterior.

Origem: [spec M1.1 — Catálogo de ativos](../specs/M1.1-catalogo-de-ativos.md).
