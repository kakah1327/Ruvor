# D-126 — A companhia vira entidade em `silver.company`, ligada ao ticker por valor, sem FK em `silver.asset`

**Status:** aceita · 2026-09-27

## Contexto

A [D-48](D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md) fez o catálogo por
ticker e deixou a companhia como atributo do papel — `code_cvm`, `cnpj`, nome — "até que
fundamentos a tornem entidade". Fundamento é da companhia, não do ticker: PETR3 e PETR4 têm o
mesmo balanço.

`silver.asset` é tabela da frente `marco1`, com contrato de "só cresce"
([FRENTES.md](../FRENTES.md#contratos-entre-frentes)).

## Decisão

**`silver.company` tem uma linha por `code_cvm`**, normalizado sem zeros à esquerda — o formato
de `silver.asset.code_cvm` —, com `cnpj`, `name`, `account_plan` e `source_reference_date`.
Nome e plano só mudam quando o documento conformado é tão ou mais recente que o gravado:
reconformar um ano antigo não sobrescreve o presente.

**A ligação com o ticker é por valor**, `company.code_cvm = asset.code_cvm`, **sem FK** em
nenhum dos dois sentidos. Só se conformam companhias do catálogo (`kind = stock`); as demais
ficam na `bronze`.

## Consequências

- Nenhuma coluna nova em `silver.asset`, e nenhuma migration na app de outra frente. O que o
  M3.1 lê do catálogo — `code_cvm`, `cnpj`, `ticker`, `kind`, `status` — está declarado no
  contrato.
- Sem FK, o banco não garante a ligação; quem garante é a conformação, que parte do catálogo.
  Código do catálogo que a CVM não conhece é contado no relatório (`sem documento na cvm`), e
  companhia que entra no catálogo depois recebe o histórico inteiro na coleta seguinte.
- Na carga real (2026-09-27), `silver.company` saiu com **339** companhias, igual aos 339
  `code_cvm` distintos das ações do catálogo.
- A `composicao_capital` da CVM não tem `CD_CVM` e se liga à companhia pelo CNPJ do índice do
  mesmo zip.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-07, RF-17, RF-19; "As
tabelas").
