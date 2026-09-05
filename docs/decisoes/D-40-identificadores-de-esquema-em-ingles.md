# D-40 — Os identificadores de esquema ficam em inglês

**Status:** aceita · 2026-09-04

## Contexto

O [CLAUDE.md](../../CLAUDE.md#idioma) manda documentação em português e **código em inglês** —
nomes de variável, função e classe. Ele não menciona nome de tabela nem de esquema.

A [D-13](D-13-camadas-bronze-prata-ouro.md) e a
[ARQUITETURA](../ARQUITETURA.md#banco-e-camadas-de-dado) escrevem as camadas em português:
bronze, **prata**, **ouro**.

## Decisão

Os identificadores no banco ficam em **inglês**: `core`, `bronze`, `silver`, `gold`. A prosa
continua dizendo *prata* e *ouro*.

A regra vale para nome de esquema, de tabela e de coluna: nome de esquema é identificador de
código como qualquer outro.

## Consequências

- Não é contradição com a D-13 — é a regra de idioma aplicada ao identificador. O documento
  descreve o conceito; o banco carrega o nome.
- Sem este registro, o M1.2 escreveria `prata` no `db_table` e o esquema ficaria dividido
  entre dois idiomas, o que é pior que qualquer uma das duas escolhas.
- Trocar era barato no F4, quando não há dado. Depois do M1.2, com preços dentro, passa a
  exigir migração.
- **Quem lê o `docs/` e o banco lado a lado precisa da tradução:** `silver` = prata,
  `gold` = ouro. Está aqui para isso.

Origem: [spec F4 — Fundação de dados](../specs/F4-fundacao-de-dados.md).
