# D-101 — Cadastro aberto, com organização pessoal; organização real só por comando

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

A [D-24](D-24-organizacao-desde-a-primeira-migration.md) dá a toda conta individual uma
organização pessoal implícita. O M2.1 precisava dizer como uma conta nasce: cadastro aberto, só
por convite ou só pelo operador.

## Decisão

**Qualquer pessoa se cadastra** com e-mail, nome e senha, e ganha uma organização pessoal
(`is_personal`), da qual é `admin`, sozinha. **A organização real, multiusuário, nasce por comando
do operador** (`manage.py create_organization`), com a primeira administradora.

## Consequências

- Organização pessoal não tem gestão de usuários; não vira real pela API.
- Sem verificação de e-mail, o cadastro revela se um e-mail já tem conta (`email_taken`) —
  declarado na spec, contido pelo limite por IP.
- Criar organização real pela API fica para quando houver quem a peça.

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
