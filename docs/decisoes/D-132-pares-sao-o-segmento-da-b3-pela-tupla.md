# D-132 — Os pares são o segmento da B3, ou o subsetor, pela tupla; a posição é o percentil

**Status:** aceita · 2026-09-27

## Contexto

A comparação com os pares não pede fonte nova: o catálogo traz a classificação da B3
(`silver.asset.sector`, `subsector`, `segment`, M1.1) e o M3.1 deixou os indicadores de ~470
ações em `gold`. Medido no catálogo em 2026-09-27, **o nome não identifica o grupo**: "Serviços
Diversos" é segmento em três subsetores de dois setores, e há subsetores de mesmo nome em setores
diferentes. Pela tupla, 43 dos 83 segmentos têm 3 ou mais companhias.

## Decisão

- **O grupo de uma ação** são as companhias (por `code_cvm`, uma vez cada) do mesmo segmento —
  a tupla (setor, subsetor, segmento) —, a própria incluída. Com menos de 3, as do mesmo
  subsetor — a tupla (setor, subsetor). Com menos de 3 de novo, não há grupo (`none`). **Nunca o
  nome sozinho.**
- A classificação de uma companhia é a do ticker de menor ordem dela com indicador na execução.
- Para cada um de seis indicadores (`roe`, `net_margin`, `ebit_margin`, `net_debt_to_equity`,
  `pe`, `pb`), um valor por companhia. Com a ação sem o valor, ou menos de 3 valores, nulo; senão
  a **mediana** (a própria incluída), o **percentil** — estritamente menores / (n − 1), de 0 a 1
  — e a contagem.
- Tudo em `Decimal`, gravado em `gold.peer_comparison`, uma linha imutável por (ação, execução),
  com o mesmo `calculated_at` dos indicadores. A comparação lê **as linhas gravadas** nesta
  execução, não os valores calculados: a ação que falhou não entra no grupo de ninguém.

## Consequências

- Na execução real de 2026-09-27: 390 ações comparadas no segmento, 64 no subsetor e 17 sem
  grupo, de 12 companhias — o mesmo número medido no catálogo.
- `pe` e `pb` saem quase sempre nulos enquanto só 4 ativos têm preço: as colunas existem e se
  preenchem quando a cobertura de preços crescer.
- Classificação setorial própria, se um dia existir, é outra decisão.

Origem: [spec M3.2 — Contexto](../specs/M3.2-contexto.md) (RF-10 a RF-15).
