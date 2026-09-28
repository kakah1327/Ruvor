# D-90 — Cálculo sob demanda só para ativo nunca calculado: um pedido aberto por ativo, garantido pelo banco, com teto global estrito e expiração; o pedido fecha com a `risk_run`

**Status:** aceita · 2026-09-28

## Contexto

A [D-19](D-19-cobertura-de-ativos-em-camadas.md) põe a cauda longa do catálogo no cálculo sob
demanda, e até o M1.6a não havia caminho para isso: nada recebia um ticker para coletar preço,
calcular métricas e abrir o risco, e nada impedia dois pedidos simultâneos do mesmo ativo — a
spec do M1.5 adiou essa regra para cá. Um cálculo completo custa ~2,5 min por ativo, com as três
redes treinando, e o `worker` desta máquina tem duas vagas e o teto de 8 GB do WSL.

## Decisão

1. **Só para ativo nunca calculado** (decisão do dono da frente, 2026-09-27). O `POST` num ativo
   que já tem `risk_run` fechada devolve **409 `asset_already_covered`**, com o `/risk` em
   `details`: quem recalcula o coberto é a rotina diária. Ativo que já está em cálculo — por
   pedido ou pela rotina — devolve **202** com o que existe, sem pedido novo.
2. **O pedido é linha no banco**, `core.compute_request`
   ([D-37](D-37-esquema-core-para-dado-operacional.md),
   [D-68](D-68-o-estado-da-execucao-mora-no-banco.md)), com estados em lista fechada — `queued`,
   `running`, `done`, `failed`, `expired` — e um motivo legível sempre que fecha.
3. **Um pedido aberto por ativo**: quem governa é a trava global do `POST`; **a guarda do banco é
   um índice único parcial** sobre o ativo para `queued` e `running`. Se algum caminho inserir sem
   a trava, a restrição barra com `IntegrityError`, e o 500 é o sinal certo.
4. **Teto global estrito**: `RUVOR_ON_DEMAND_MAX` pedidos abertos (padrão 3), decidido sob
   `pg_advisory_xact_lock` numa chave constante — a trava vale com zero pedidos abertos, o que uma
   trava de linha não faria. Passou do teto, 429 `on_demand_queue_full`.
5. **Expiração**: pedido aberto há mais de `RUVOR_ON_DEMAND_TIMEOUT_MIN` (padrão 30) é tratado
   como fechado para a trava e para o teto. Quem grava `expired` é o `POST`, a cadeia e o fecho;
   **o `GET` não escreve** — mostra o estado calculado.
6. **O pedido fecha com a `risk_run`**, no fecho do M1.5, não na abertura — fechar na abertura
   soltaria a trava com o risco ainda rodando. `expired` é final: um pedido vencido não vira
   `done` depois.

## Consequências

- Cada pedido bem-sucedido torna o ativo coberto para sempre
  ([D-51](D-51-cobertura-e-o-que-tem-preco.md)), e a rotina diária passa a recalculá-lo. Não há
  limite por pessoa nem teto de cobertura: **antes de expor a rota**, a hospedagem precisa
  decidir limite por IP ou login ([spec do M1.6a](../specs/M1.6a-fundacao-da-aplicacao.md#sem-limite-por-pessoa-e-a-cobertura-cresce-sem-teto)).
- O teto é conta de uma máquina só, e por isso é configuração.
- O `/risk` expõe o pedido em `request`, ao lado de `latest` e `in_progress`: a tela sabe se o
  cálculo está a caminho, terminou ou falhou, e por quê.
- Na execução real do M1.6a, o `BBDC4`, sem preço até então, foi pedido e calculado em 99,6 s —
  coleta, métricas e risco —, e passou a ser coberto.
