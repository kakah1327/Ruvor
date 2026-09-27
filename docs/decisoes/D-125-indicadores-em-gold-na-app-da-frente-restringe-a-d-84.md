# D-125 — Os indicadores fundamentalistas moram em `gold`, na app da frente, e a cerca se amplia; restringe a D-84

**Status:** aceita · 2026-09-27 · restringe a [D-84](D-84-frentes-com-cerca-de-pastas.md)

## Contexto

A [D-84](D-84-frentes-com-cerca-de-pastas.md) deu à frente `fundamentos` uma cerca de pastas —
a app nova e as tabelas novas em `bronze` e `silver` — e delegou o detalhe à tabela de cercas de
[`FRENTES.md`](../FRENTES.md). O M3.1 calcula indicadores (P/L, ROE, capitalização), e
indicador derivado é `gold` pela [D-13](D-13-camadas-bronze-prata-ouro.md), como as métricas do
M1.3 e o risco do M1.4.

Pôr os indicadores em `apps/analytics/`, que já escreve em `gold`, seria escrever na cerca da
`marco1`.

## Decisão

**`gold.fundamental_indicator` pertence a `apps/fundamentals`**, e a cerca da `fundamentos`
passa a incluir tabelas novas em `gold`, da própria app, com nome próprio. A tabela de cercas
de `FRENTES.md` foi alterada na PR da spec.

A linha é **imutável**, como a [D-55](D-55-metrica-de-comportamento-e-imutavel.md) manda para
métrica derivada: uma por (ação, execução), `calculated_at` com um `now()` por execução,
recalcular cria linha. Não tem manifesto, pela
[D-60](D-60-metrica-descritiva-sem-manifesto-restringe-a-d-15.md): não há algoritmo a escolher
nem semente.

## Consequências

- A cerca por pastas da D-84 continua valendo; o que muda é o conteúdo da linha da
  `fundamentos`, e a mudança passou pela revisão que a D-84 pede.
- A leitura de `silver.price` (`asset`, `date`, `close`) é contrato registrado em
  `FRENTES.md`: a `marco1` produz, a `fundamentos` consome.
- Reapresentação de balanço gera indicador novo para o mesmo trimestre, e a linha antiga fica —
  a imutabilidade funcionando.
- Na carga real, `compute_fundamentals` gravou 471 linhas, uma por ação, sem falha e sem
  resultado fora de escala (V-11).

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-20, RF-25; "Contratos com
outras frentes").
