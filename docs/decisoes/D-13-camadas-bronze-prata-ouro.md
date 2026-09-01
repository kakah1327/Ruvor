# D-13 — Bronze, prata e ouro como esquemas dentro do PostgreSQL

**Status:** aceita · 2026-08-29

## Contexto

Surgiu a questao de usar arquitetura de lakehouse com camadas medalhao. O volume nao justifica: ~400 papeis x ~2.500 pregoes = ~1 milhao de linhas, algumas centenas de MB. Mesmo com todas as acoes do mundo seriam ~125 milhoes de linhas — territorio confortavel de PostgreSQL.

## Decisão

**PostgreSQL**, com bronze / prata / ouro implementadas como **esquemas internos**. Sem lakehouse, sem Spark.

## Consequências

- A separacao em camadas serve para **linhagem**, nao para volume — e e o que resolve o requisito de auditoria.
- **Bronze e obrigatoria** neste dominio: o historico de precos e reescrito retroativamente a cada dividendo ou desdobramento. Guardando so o preco ajustado, resultados historicos mudam sozinhos e nao podem ser reproduzidos.
- Caminho de crescimento sem trocar de banco: TimescaleDB ou DuckDB + Parquet.
