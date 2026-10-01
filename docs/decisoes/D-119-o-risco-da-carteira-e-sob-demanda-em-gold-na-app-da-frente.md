# D-119 — O risco da carteira é sob demanda, em tabelas próprias de `gold` na app da `identidade`, sem retratos, com teto global e um por organização; restringe a D-84

**Status:** aceita com a aprovação da [spec do M2.2a](../specs/M2.2a-carteira.md) · 2026-09-30 · frente `identidade`

## Contexto

O cálculo de risco do ativo está preso ao ativo no backend: `gold.risk_run.asset`,
`gold.model_snapshot.asset` e `core.compute_request.asset` são FK não nulas para `silver.asset`, e a
trava da [D-92](D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md) é por `asset_id`. Essas
tabelas e `apps/risk/` são da `marco1`. A [D-84](D-84-frentes-com-cerca-de-pastas.md) dá a cada
frente uma cerca de pastas, e a da `identidade` era só `backend/apps/accounts/`.

A combinação de pesos que a pessoa montou nunca existiu antes
([D-03](D-03-carteira-montada-pelo-usuario.md)): não há o que pré-calcular, e cada cálculo treina as
quatro redes do zero — os retratos ([D-77](D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md))
são por ativo. A [PRODUTO §6](../PRODUTO.md#6-restrições-de-produto) pede cache agressivo e limite
de análise pesada.

## Decisão

1. **O risco da carteira mora em `gold.portfolio_risk_run` e `gold.portfolio_risk_result`**, da app
   `apps/portfolios`, com o mesmo manifesto e as mesmas colunas de resultado do ativo, e o filtro
   automático por organização. As tabelas da `marco1` não mudam.
2. **A cerca da `identidade` ganha `backend/apps/portfolios/` e `backend/tests/portfolios/`**,
   inclusive as tabelas novas em `core` e em `gold`, da própria app, com nome próprio — como a
   [D-125](D-125-indicadores-em-gold-na-app-da-frente-restringe-a-d-84.md) fez para a `fundamentos`.
   O que a carteira usa da `marco1` — as constantes de `apps/risk/config.py`, `status_for` e os
   quantizadores de `apps/risk/compute.py`, `RiskRun.Status`, e, nos testes de paridade, `MODELS` e
   `_row` — é **lido, nunca escrito**, e vira contrato "só cresce" em `FRENTES.md`.
3. **Sob demanda, e só sob demanda.** Nenhuma rotina recalcula carteira. A mesma versão com a mesma
   série (mesmo `as_of_date`, mesmo SHA-256) não se recalcula: o pedido devolve 409 com a execução que
   já existe.
4. **Sem retratos**: a carteira treina do zero.
5. **Teto**: `RUVOR_PORTFOLIO_COMPUTE_MAX` execuções em andamento ao todo (padrão 2) e uma por
   organização, decididos sob `pg_advisory_xact_lock(7103, 0)`. Execução em andamento há mais de
   `RUVOR_PORTFOLIO_TIMEOUT_MIN` (padrão 60) não conta. A contagem global é a **única** consulta que
   atravessa organizações: uma função nomeada de `apps/portfolios/services.py`, que devolve um
   inteiro, na lista fechada de quem chama `.unscoped`
   ([D-112](D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md)).
6. **Pela fila, no molde do ativo**: uma tarefa de abertura, uma por modelo — os baratos primeiro —
   e o fecho, que só escreve sobre `running`
   ([D-150](D-150-o-fecho-so-escreve-sobre-execucao-em-running.md)); a web cria a execução e
   enfileira pelo nome ([D-89](D-89-a-web-enfileira-pelo-nome-da-tarefa.md)), e não importa o motor.

## Consequências

- Cada cálculo de carteira custa o de um ativo do zero, no `worker` de sempre, na fila da rotina
  diária. O teto é o freio; uma fila própria é aditiva.
- A conversão do resultado do motor em colunas é copiada da `_row` do ativo, e um teste de paridade
  impede a divergência.
- Reaproveitar retratos na carteira exigiria mudar `gold.model_snapshot`, da `marco1`, em bloco
  próprio.
- Execução de carteira presa não é varrida; sai do teto pelo prazo.

Origem: [spec M2.2a — Carteira](../specs/M2.2a-carteira.md) (decisões 2 e 7, RF-04, RF-05, RF-13 a
RF-15, RF-22, RF-23).
