# D-123 — O resultado é guardado por trimestre isolado; o 4º trimestre é o DFP menos o ITR anterior; 12 meses é a soma de quatro trimestres

**Status:** aceita · 2026-09-27

## Contexto

Na DRE do ITR, cada conta vem duas vezes para a mesma data: o trimestre isolado e o acumulado
do exercício. O 4º trimestre não tem ITR: o exercício fechado vem só no DFP, que é anual. E
nove companhias do DFP 2024 têm exercício que não fecha em dezembro — a Camil vai de março a
fevereiro, e o 4º trimestre dela cruza o ano do zip.

Os múltiplos pedem lucro de 12 meses, que não existe pronto na fonte.

## Decisão

**`silver.financial_statement` guarda o resultado do trimestre isolado do exercício da
companhia**, uma linha por (companhia, `reference_date`); o balanço é a posição na data.

- No **ITR**, o isolado é a linha de maior `DT_INI_EXERC` para aquela conta e data.
- O **4º trimestre** é o anual do DFP **menos** o acumulado do ITR da mesma companhia com o
  **mesmo `DT_INI_EXERC`** e o maior `DT_REFER` anterior, procurado no zip do ano do DFP **e no
  do ano anterior**. É nulo se esse ITR não existe, se a distância entre os dois fica fora de 88
  a 93 dias, se o campo é nulo num dos dois, ou se os escopos diferem.
- **12 meses** é a soma de quatro trimestres consecutivos — cada intervalo entre 88 e 93 dias —
  do mesmo escopo; buraco, escopo misto ou valor nulo tornam o valor de 12 meses nulo.

A regra é genérica para exercício não civil (decisão do dono da frente), sem tabela de
exceções por companhia.

## Consequências

- O exercício não civil encerrado em 2016 não tem 4º trimestre: o ITR anterior estaria no zip
  de 2015, fora do intervalo.
- Na carga real, a Petrobras tem trimestres sem buraco de 2016-03-31 até o mais recente (V-08),
  e o lucro de 12 meses do 2T26 bateu com a divulgação das três companhias conferidas (V-13).
- Um DFP que valeu a mãe pelo [RF-08b](D-129-lucro-so-na-mae-vale-a-mae.md) pode ser subtraído
  de um ITR que valeu a filha: 29 casos companhia-ano de 2016 a 2025, todos de magnitude
  pequena, medidos na spec.
- A regra supunha que ITR e DFP nunca têm a mesma data. A execução real mostrou que têm, e a
  [D-128](D-128-itr-e-dfp-na-mesma-data-vale-o-dfp.md) decide o caso.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-13, RF-14, RF-21).
