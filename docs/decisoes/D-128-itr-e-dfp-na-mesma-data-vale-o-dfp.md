# D-128 — ITR e DFP na mesma data: vale o DFP

**Status:** aceita · 2026-09-27

## Contexto

A spec do M3.1 afirmava, pela medição de três arquivos, que o ITR não tem 4º trimestre: o
exercício fechado vem só no DFP. A regra do trimestre isolado
([D-123](D-123-resultado-por-trimestre-isolado-e-12-meses-por-soma.md)) e a unicidade de
`silver.financial_statement` em (companhia, `reference_date`) dependiam disso.

A primeira execução real sobre os 22 arquivos (T11, 2026-09-27) reprovou a V-08 com
`IntegrityError` em quatro (companhia, ano): AZZAS 2154 (`22349`) e Orizon (`25550`) em
2021-12-31, Economatica (`26077`) em 2022-09-30, Tenda (`21148`) em 2023-03-31 — ITR e DFP da
mesma companhia com o mesmo `DT_REFER`.

## Decisão

**Vale o DFP** — o demonstrativo anual, auditado (decisão do dono da frente). Em
`conform_year`, **antes** de gerar as linhas, todo ITR cujo `reference_date` também existe num
DFP da mesma companhia no mesmo ano de zip é descartado; o DFP gera a linha como sempre, e o ITR
candidato ao 4º trimestre é procurado entre os que sobraram.

O descarte **não é falha**: o relatório diz `ano {A}: {k} itr descartados por dfp na mesma data
({code_cvm}, ...)`.

## Consequências

- Nasceu o RF-13b da spec e a tarefa 11b do plano; a carga foi refeita do zero e a V-08 passou.
- Na carga real, a linha do relatório saiu para as quatro companhias: `22349` e `25550` em
  2021, `26077` em 2022, `21148` em 2023.
- O caso é raro — quatro das 339 companhias do catálogo em dez anos — e aparece contado a cada
  conformação daqueles anos, não em silêncio.
- A mutação que tira o descarte reprova nos dois testes `test_rf13b_…`: duas linhas geradas no
  `conform_year` e `IntegrityError` no importer.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-13b); plano, tarefa 11b.
