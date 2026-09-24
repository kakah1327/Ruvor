# D-58 — O cálculo da camada 2 mora no backend, não no motor

**Status:** aceita · 2026-09-24

## Contexto

O repositório tem dois lugares onde cálculo numérico poderia morar: `engine/`, o pacote
isolado com nove modelos de VaR e quatro testes de backtesting, e `backend/`, o Django.
Volatilidade anualizada, maior queda, beta e correlação são cálculo numérico, e a pergunta
"então vai para o motor?" aparece sozinha.

A varredura por `drawdown|beta|volatilit|sharpe` em `engine/src/` não encontra `drawdown` nem
`sharpe` em lugar nenhum; encontra `beta` só como nome de coeficiente interno — vetor do
CAViaR e do teste DQ, parâmetro de persistência do GARCH e do EGARCH — e a volatilidade
**condicional** do GARCH, que é outra coisa. Nenhum é beta de mercado.

## Decisão

As métricas da camada 2 são calculadas no backend, em `backend/apps/analytics/`, num módulo
puro (`metrics.py`) que não importa modelo, não abre transação e não consulta banco — o mesmo
corte que `apps/assets/conform_prices.py` faz. `engine/` continua sendo o ativo científico de
VaR e backtesting, e não ganha função descritiva.

## Consequências

- A ARQUITETURA já havia reservado `backend/apps/analytics/` como "camada 2 —
  comportamento"; o M1.3 só criou o app.
- A regra do [D-17](D-17-monorepo-engine-sem-django.md) segue intacta nos dois sentidos:
  `engine/` não importa Django, e o backend não importa `engine`.
- A fronteira é "descritivo × inferencial", não "fácil × difícil". Quando o M1.4 trouxer VaR,
  o cálculo vem do motor, e é o `analytics` que consome.
- Duplicação aceita e deliberada: `log_returns` existe em
  `engine/src/engine/data/preprocessing.py` e o backend não o usa — o M1.2 já gravou
  `log_return` em `silver.price`.

Origem: [spec M1.3 — Camadas 1 e 2](../specs/M1.3-camadas-1-e-2.md).
