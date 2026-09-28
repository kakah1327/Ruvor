# D-92 — Nunca duas execuções do mesmo ativo ao mesmo tempo: a abertura pula o ativo em cálculo

**Status:** aceita · 2026-09-28

## Contexto

Até o M1.6a, a abertura do M1.5 criava uma `risk_run` em `running` sempre que chamada. Com o
cálculo sob demanda ([D-90](D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md)), três
caminhos passam a abri-la — a rotina diária, o `--async` e a cadeia por ticker —, e o `worker`
roda com `--concurrency=2`: a rotina e um pedido do mesmo ativo podiam abrir duas execuções
sobrepostas, cada uma treinando as redes.

## Decisão

1. **A abertura pula o ativo que já tem uma `risk_run` em `running` iniciada há menos de
   `RUVOR_ON_DEMAND_TIMEOUT_MIN`**, e registra o pulo no log do `worker`. Uma `running` mais velha
   que o prazo é tratada como presa e não impede abrir outra.
2. **A consulta e a criação acontecem sob uma trava por ativo** — `pg_advisory_xact_lock` numa
   chave derivada do id do ativo, em espaço separado da trava global do pedido — **dentro de uma
   transação**: fora dela, a trava `xact` se soltaria no fim da própria consulta. A guarda levanta
   se chamada fora de `transaction.atomic`.
3. **O `chord` sai depois do commit** da abertura (`transaction.on_commit`), para que nenhuma
   tarefa por modelo rode antes de a `risk_run` existir para outra conexão.
4. **O fecho do M1.5 passa a ter transação e a mesma trava**: `close_run` e o fechamento dos
   pedidos ligados acontecem juntos, e a abertura não liga um pedido a uma execução que o fecho
   acabou de fechar sem ver o pedido.
5. **Com pedido, o pulo liga**: a abertura chamada com `request_id` sobre um ativo em cálculo
   liga o pedido à `risk_run` em andamento, e ele fecha quando ela fechar.

## Consequências

- **O `compute_risk` síncrono fica fora**: não passa pela abertura, grava a execução já fechada e
  nunca fica `running`. É a ferramenta manual do M1.4, e rodá-lo durante uma execução assíncrona
  do mesmo ativo ainda produz duas execuções — aceito e declarado na
  [spec do M1.6a](../specs/M1.6a-fundacao-da-aplicacao.md#o-compute_risk-síncrono-não-respeita-o-rf-24).
- Se a rotina disparar durante um pedido, ela pula aquele ativo naquele dia; o pregão que a
  coleta da rotina trouxer depois da coleta do pedido espera a rotina seguinte.
- "Presa" é por relógio: uma execução legítima que passe do prazo seria tratada como presa. Hoje
  a rotina inteira leva ~25 s e um ativo novo ~100 s; o prazo é configuração.
- As corridas — duas aberturas, e abertura × fecho sem a trava ou sem a transação — são provadas
  por testes com threads e barreiras, e cada mutação reprova (V-19c).
