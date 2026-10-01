# D-117 — A carteira é uma série única, de pesos fixos rebalanceados a cada pregão, sobre a interseção das datas, que passa pelos nove modelos sem mudar o motor

**Status:** aceita com a aprovação da [spec do M2.2a](../specs/M2.2a-carteira.md) · 2026-09-30 · frente `identidade`

## Contexto

O risco de várias ações juntas não é a soma dos riscos de cada uma
([PRODUTO §6](../PRODUTO.md#6-restrições-de-produto)). A PRODUTO descreve dois caminhos — o
**barato**, que trata a carteira como um ativo só, e o **caro**, que modela a relação entre os
ativos e exige uma família de modelos que o projeto não tem — e recomenda o barato, "ainda não
formalizado".

O motor não sabe o que é um ativo: `run_experiment` pede ao provedor `fetch(ticker, start, end)` com
a coluna `close` e calcula ele mesmo o log-retorno. Cada ação tem o próprio calendário em
`silver.price`: dia sem negócio não tem linha.

## Decisão

1. **O caminho é o barato.** A carteira vira uma série de índice, e essa série passa pelos nove
   modelos e pelos quatro backtests que já existem, com a semente, a janela de treino e os níveis do
   ativo (`apps/risk/config.py`). **O motor não muda.**
2. **A série**: as datas são a **interseção** das datas em que cada ação tem `adj_close > 0`; o
   retorno de cada data é `R_k = Σ (w_i/100) × (adj_i(d_k)/adj_i(d_{k−1}) − 1)` — **retorno simples
   ponderado, pesos fixos, rebalanceados a cada data** —; o índice é `I_0 = 1` e
   `I_k = I_{k−1} × (1 + R_k)`. O motor tira `ln(1 + R_k)`, o log-retorno da carteira.
3. **A série é calculada em `float` do Python, com a biblioteca padrão**
   ([D-59](D-59-sem-dependencia-numerica-nova-no-backend.md)), na mesma ordem de soma na web e no
   `worker`, e o SHA-256 dela vai no manifesto: a mesma versão com os mesmos preços dá o mesmo índice,
   bit a bit.
4. **O piso é o do ativo**: 503 datas (`MIN_SESSIONS`).

## Consequências

- Mudar os pesos obriga a recalcular — a limitação que a PRODUTO já previa.
- O backtest de dez anos é de uma carteira **rebalanceada**, não da que a pessoa comprou e deixou
  derivar. Para VaR de 1 dia a diferença é pequena; compra-e-mantém é aditivo.
- Ponderar o **log**-retorno seria errado: a soma ponderada de log-retornos não é o log-retorno da
  carteira. Um teste com valores escritos à mão o reprova.
- Uma ação listada há pouco encurta a série da carteira inteira, e abaixo de 503 datas não há risco.
- A série única não diz qual ação puxa a perda: isso é a contribuição por ativo (PRODUTO 5.6),
  aditiva. O caminho caro continua fora.
- A PRODUTO §6 e §8 deixam de chamar a escolha de "não formalizada".

Origem: [spec M2.2a — Carteira](../specs/M2.2a-carteira.md) (decisão 3, RF-06, RF-07).
