# D-60 — Métrica descritiva de comportamento não carrega manifesto; restringe a D-15

**Status:** aceita · 2026-09-24

## Contexto

A [D-15](D-15-manifesto-de-execucao.md) manda que **todo** resultado registre algoritmo,
versão, hiperparâmetros, base de dados, semente e a pedido de quem. A
[D-16](D-16-resultado-e-imutavel.md), que a [D-55](D-55-metrica-de-comportamento-e-imutavel.md)
estende, fala em "execução nova, **com manifesto novo**".

O M1.3 grava resultado em `gold` **sem** manifesto: `gold.behavior_metric` não tem FK para
coleta nem para execução, e a spec excluiu manifesto do escopo.

## Decisão

A D-15 vale para **resultado de risco** — o que sai de um modelo, com hiperparâmetro e
semente. Métrica descritiva de comportamento fica de fora: ela não tem algoritmo a escolher
nem semente a fixar, e sua reprodutibilidade se resolve com o que a própria linha carrega —
`as_of_date`, `first_price_date`, `price_count`, `statistical_observations` e
`benchmark_observations`.

O manifesto nasce no **M1.4**, onde há algoritmo e semente para manifestar.

## Consequências

- `compute_metrics` não cria `collection_run` nem escreve em `bronze`. Execução que não
  deixa linha de manifesto é, aqui, comportamento correto.
- Quem auditar uma linha de métrica reconstrói a base pelas cinco colunas acima mais
  `silver.price` — com a ressalva da [D-13](D-13-camadas-bronze-prata-ouro.md): o provedor
  reescreve o histórico, então a reconstrução é aproximada por natureza, e é a imutabilidade
  da [D-55](D-55-metrica-de-comportamento-e-imutavel.md) que torna a divergência visível.
- Precedente de forma: a [D-54](D-54-transacao-por-ativo-restringe-a-d-48.md), que restringe
  a D-48 em vez de substituí-la. A D-15 continua íntegra no seu domínio.

Origem: [spec M1.3 — Camadas 1 e 2](../specs/M1.3-camadas-1-e-2.md).
