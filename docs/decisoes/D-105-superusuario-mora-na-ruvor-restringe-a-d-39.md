# D-105 — O superusuário mora na organização `ruvor`, como `admin` — restringe a D-39

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

A [D-39](D-39-usuario-proprio-autentica-por-email.md) deu ao gerente um `create_superuser` que
exige organização. O `createsuperuser` do Django não tem como passá-la, e falhava com `ValueError`
— dívida registrada desde o F4.

## Decisão

`create_superuser` **sem** organização põe o superusuário na `ruvor`, a organização fixa da
plataforma, com `role` `admin`. `create_user` continua recusando a falta de organização.

## Consequências

- `createsuperuser`, inclusive `--noinput` com as `DJANGO_SUPERUSER_*`, funciona; a dívida está
  paga.
- A `0003` de `accounts` promove a `admin` todo superusuário que já existia.
- O superusuário não tem superfície: não há Django Admin nem rota de equipe.

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
