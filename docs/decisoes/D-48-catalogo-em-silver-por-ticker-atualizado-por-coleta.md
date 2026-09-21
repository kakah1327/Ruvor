# D-48 — O catálogo conformado mora em `silver`, é um por ticker e é atualizado por coleta

**Status:** aceita · 2026-09-16

## Contexto

O M1.1 é o primeiro bloco a povoar `bronze` e `silver`, e o que ele fizer vira o padrão que o
M1.2 imita. A ARQUITETURA descrevia `silver` como "preços limpos e conformados" e `core` como
dado operacional ([D-37](D-37-esquema-core-para-dado-operacional.md)).

## Decisão

- **`silver.asset`, uma linha por ticker.** O catálogo é dado de domínio derivado de provedor
  externo — "limpo e conformado a partir do cru" é a definição da camada. `core` é o que não
  vem de provedor nenhum. O usuário digita `PETR4`, não "Petrobras"; a companhia é atributo do
  papel até que fundamentos (M3.1) a tornem entidade.
- **Atualizado por coleta**: `upsert` por ticker, inativação por ausência, nunca `delete`.
  `last_seen_run` avança em toda coleta em que o papel aparece; `updated_at` só muda quando uma
  coluna conformada muda.
- **Na `bronze`, o payload é imutável**: `b3_company_listing` e `b3_company_detail` são
  só-acréscimo, e `collection_run` tem uma única transição, `running → ok | failed`. A palavra
  "imutável" da ARQUITETURA significa isso.
- **Conformação transacional**: a `silver` só muda depois de a coleta inteira chegar; falha no
  meio deixa a `bronze` com o coletado e a `silver` como estava.

## Consequências

- O M1.2 herda `collection_run` (acrescenta o próprio `source`) e o padrão coleta → transação
  → `failed` fora da transação.
- Os testes que escrevem no banco usam `@pytest.mark.django_db`; a marca renomeia a conexão
  para `test_<nome>` pelo resto da sessão, e o `test_conexao_com_o_banco` do F3 aceita os dois
  nomes.

Origem: [spec M1.1 — Catálogo de ativos](../specs/M1.1-catalogo-de-ativos.md).
