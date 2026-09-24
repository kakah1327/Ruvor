# D-56 — A tabela de métricas é larga e tipada; série ganha tabela própria

**Status:** aceita · 2026-09-24

## Contexto

Métrica de comportamento é um punhado de escalares por ativo — oito retornos, duas
volatilidades, cinco colunas de queda, beta, correlação, momentos, dividendos, volume. O
atalho conhecido é uma tabela chave-valor (`metric_name`, `value`), que aceita métrica nova
sem migration.

## Decisão

`gold.behavior_metric` é **larga**: uma coluna por métrica, com tipo e nulabilidade próprios
— `numeric(18,10)` para retorno e volatilidade, `numeric(18,6)` para dividendo, `numeric(20,2)` para
volume médio, `date` para as datas da queda, `integer` para as contagens. Métrica nova é **migration nova**, de
propósito.

Série não vira coluna: o histograma de retornos mora em `gold.return_histogram_bin`, 42
linhas por métrica, com `(metric, bin_index)` único e `CASCADE` no `metric` — o balde não
tem vida própria.

## Consequências

- O banco valida o tipo, e `NULL` significa "não deu para calcular" ([RF-12](../specs/M1.3-camadas-1-e-2.md)),
  não "chave ausente". Em chave-valor as duas coisas são a mesma linha faltando.
- Acrescentar métrica custa migration e revisão — é o preço, e é o ponto: tabela de métrica
  não deve crescer por descuido.
- `CASCADE` do Django é implementado **em Python**, não vira `ON DELETE CASCADE` no
  PostgreSQL. Apagar métrica por `DELETE` em `psql` esbarra na FK.

Origem: [spec M1.3 — Camadas 1 e 2](../specs/M1.3-camadas-1-e-2.md).
