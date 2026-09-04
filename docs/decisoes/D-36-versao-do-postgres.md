# D-36 — A versão maior do Postgres é a 18

**Status:** aceita · 2026-09-04

## Contexto

A [spec do F3](../specs/F3-ambiente-local.md) proíbe a etiqueta `latest` e manda fixar a
versão maior das imagens de apoio, confirmando a etiqueta **no registro** em vez de
inventá-la. Para o Postgres, ela vai além e pede que a escolha seja **registrada aqui**: a
versão atravessa para o F4 (migrations), para a hospedagem de produção e para o caminho de
crescimento com TimescaleDB citado na
[ARQUITETURA](../ARQUITETURA.md#caminho-de-crescimento). Hoje não há dado nenhum, então
trocar é grátis; depois do F4, deixa de ser.

## Decisão

O ambiente local usa a imagem oficial **`postgres:18`**. O driver é o `psycopg` 3
(`psycopg[binary]`), como a spec já nomeava.

## Consequências

- **O ponto de montagem mudou na 18.** O volume vai em `/var/lib/postgresql`, e **não** em
  `/var/lib/postgresql/data`, que é o que todo tutorial anterior diz. O `PGDATA` da imagem é
  `/var/lib/postgresql/18/docker`. Com o caminho antigo o contêiner **recusa subir**, com uma
  mensagem sobre compatibilidade com `pg_ctlcluster`. É a forma mais provável de alguém
  quebrar o ambiente ao mexer no `compose.yaml`.
- Verificado na implementação do F3: o servidor se identifica como
  `PostgreSQL 18.6 (Debian 18.6-1.pgdg13+2)` e o `psycopg` 3 conecta nele sem ajuste.
- **O F4 e o bloco de hospedagem herdam a escolha** e devem lê-la daqui, não re-derivá-la do
  `compose.yaml`. Migration gerada contra a 18 e servidor de produção mais antigo é a
  divergência que este registro existe para evitar.
- Trocar a versão maior depois do F4 exige, no mínimo, reexecutar as migrations contra a
  versão nova e recriar o volume `pgdata` — o formato de dados no disco não é compatível
  entre versões maiores.

Origem: [spec F3 — Ambiente local](../specs/F3-ambiente-local.md).
