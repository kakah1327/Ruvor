# D-124 — A capitalização soma as classes e é nula quando falta preço de alguma; a escala das ações é inferida pelo LPA

**Status:** aceita · 2026-09-27

## Contexto

A capitalização de mercado ficou fora do M1.3 por falta de fonte. A CVM informa a quantidade de
ações por classe — ON e PN — na `composicao_capital`, que **só existe de 2020 em diante**, e sem
separar PNA de PNB.

E a quantidade **não tem escala declarada**. No DFP 2024 a Petrobras informa 7.442.454.142 ON,
em unidades; a Vale, 4.539.008 ON, que são milhares. Nenhuma coluna diz qual é qual.

## Decisão

**A capitalização é a soma, por classe com quantidade maior que zero, do `close` do ticker da
classe vezes a quantidade.** Ticker da classe é ação ativa do catálogo, da mesma companhia, de
sufixo `3` (ON) ou `4` a `8` (PN); *unit* nunca entra. Quando não dá, o valor é **nulo** e
`market_cap_missing` diz por quê, numa **lista fechada e em ordem fixa** — a primeira que casa
decide: `stale_statement` (balanço a mais de 460 dias), `no_share_count`, `share_scale_unknown`,
`ambiguous_class` (mais de um ticker numa classe), `no_price` (nenhuma classe com preço),
`missing_class_price` (alguma classe sem preço). Nenhum chute de preço para a classe que falta.

Os indicadores por ação (LPA, VPA, P/L, P/VP) têm motivo próprio, também em lista fechada
(`per_share_missing`), e **só existem de 2020 em diante**, porque antes disso não há
quantidade.

**A escala da quantidade é inferida pelo lucro por ação que a própria companhia informa**:
entre `k ∈ {1, 1000}`, a que aproxima lucro ÷ (ações × `k`) do LPA informado, aceita só dentro
de um **fator 2**. Fora disso, ou com algum insumo nulo, zero ou de sinal trocado, a escala e as
quantidades são **nulas** — nulo em vez de chute. **O LPA não cai para a conta `3.99`** quando
falta nas filhas de "Lucro Básico por Ação" (decisão do dono da frente, 2026-09-27): no Itaú ela
traz a soma das classes (16,72 contra 4,20 por ação).

## Consequências

- Na carga real (V-11), VALE3 — só ON, com preço — sai com capitalização; PETR4 e ITUB4 saem com
  `missing_class_price`, porque PETR3 e ITUB3 não tinham preço em `silver.price` — e as duas saem
  com P/L e P/VP, que não dependem das outras classes.
- **A escala sai nula em cerca de um terço dos documentos**, e quase sempre por outra razão que
  não a heurística: no DFP 2024 consolidado, 148 em unidades, 82 em milhares, 51 com o lucro
  zerado (49 resolvidos pela [D-129](D-129-lucro-so-na-mae-vale-a-mae.md)), 43 sem LPA nas filhas,
  6 com `L/E` negativo e só 8 fora do fator 2.
- Companhia com PNA e PNB cai sempre em `ambiguous_class`: separar exige outra fonte.
- Units ficam sem P/L e P/VP; a capitalização e os indicadores da companhia aparecem nelas.
- A capitalização do M1.3 passa a ter fonte, com essas ressalvas.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-15, RF-24, RF-24b;
"Capitalização"; "A escala das ações é inferida, não lida").
