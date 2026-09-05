# D-38 — O `public` guarda o encanamento do Django, e a tabela declara o esquema no `db_table`

**Status:** aceita · 2026-09-04

## Contexto

Com quatro esquemas nomeados ([D-37](D-37-esquema-core-para-dado-operacional.md)), a
expectativa natural é que **tudo** nasça neles e o `public` fique vazio. A escrita da
[spec do F4](../specs/F4-fundacao-de-dados.md) mediu que isso não é implementável sem um
passo de preparação fora do ciclo de migrations.

Medido contra o `postgres:18` do `compose`, num banco de sonda criado e removido:

| `search_path` | `core` existe? | `CREATE TABLE` sem qualificar |
|---|---|---|
| `core` | não | **erro** — `no schema has been selected to create in` |
| `core,public` | não | a tabela nasce em **`public`**, sem aviso |
| `core,public` | sim | a tabela nasce em `core` |

A ordem não resolve: `MigrationExecutor.migrate()` chama `recorder.ensure_schema()`
(`django/db/migrations/executor.py:109`) **antes** de aplicar o plano, sempre que há algo a
aplicar. A `django_migrations` é criada primeiro, e nenhuma migration chega antes dela.

Além disso, o **Django 6.1 não tem opção de esquema**: não existe `db_schema` na árvore, e
`Meta` só oferece `db_table`.

## Decisão

**O `public` guarda o encanamento do Django — `django_migrations`, `django_content_type` e
as tabelas do `auth` — e nunca dado de domínio.** A fronteira é *encanamento contra
domínio*, não *vazio contra cheio*.

**Toda tabela do projeto declara o esquema dentro do próprio `db_table`**, com o
identificador em duas partes:

```python
class Meta:
    db_table = 'core"."organization'
```

## Consequências

- **`migrate` num banco vazio é a única coisa que qualquer ambiente precisa executar.** Sem
  script de inicialização, sem permissão de criação mantida em produção, sem passo que só
  funciona em volume novo. É o que faz o F5 e uma hospedagem ainda não escolhida herdarem
  zero obrigações.
- As duas alternativas foram pesadas e descartadas: esquema criado por script de
  inicialização só roda em volume novo, e quem já tem banco recebe a divisão silenciosa da
  linha 2 da tabela; `CREATE SCHEMA` a cada conexão exige DDL permanente e permissão de
  criação em produção.
- **`ALTER TABLE ... SET SCHEMA` por `RunSQL` não serve.** Ele move a tabela e não move o
  `db_table` do modelo: o ORM continuaria emitindo o nome sem qualificação, e o `search_path`
  voltaria a ser obrigatório em execução.
- O mecanismo funciona porque `quote_name` não requota identificador que já tem aspas
  (`db/backends/postgresql/operations.py:190-192`) e `_create_index_name` parte o
  identificador com `split_identifier` (`db/backends/base/schema.py:1550`). As tabelas M2M
  herdam o esquema sozinhas, porque `strip_quotes` só remove aspas que envolvem a string
  inteira.
- **Medido de ponta a ponta** na revisão da spec, contra o `postgres:18`: as quatro tabelas
  do F4 nascem em `core`, os nomes de índice e restrição saem sem esquema embutido, e o
  `public` recebe exatamente as cinco tabelas de encanamento.
- A garantia viva é a verificação que confere esquema e tabela **contra lista fechada** — não
  contra amostra —, e ela precisa continuar crescendo à medida que M1.1 e M1.2 acrescentam
  tabelas.

Origem: [spec F4 — Fundação de dados](../specs/F4-fundacao-de-dados.md).
