# D-39 — O usuário do projeto herda `AbstractBaseUser` e autentica por e-mail

**Status:** aceita · 2026-09-04

## Contexto

As telas de login são do Marco 2 ([D-08](D-08-dono-do-dado-no-schema.md)), o que tenta adiar
também o modelo de usuário. Mas **trocar o `AUTH_USER_MODEL` do Django é barato exatamente
uma vez: antes da primeira migration.** Depois, muda com migração de dados sobre chaves
estrangeiras espalhadas por todo o esquema.

O F4 é o bloco da primeira migration. Era agora ou com dado dentro.

## Decisão

O projeto define **modelo de usuário próprio**, apontado por `AUTH_USER_MODEL`, presente na
primeira migration. Ele herda **`AbstractBaseUser` e `PermissionsMixin`** — não
`AbstractUser` — e o `USERNAME_FIELD` é o **e-mail**.

O usuário tem vínculo **obrigatório** com uma organização, com `PROTECT`.

## Consequências

- `AbstractUser` traria `username` como identificador e `first_name`/`last_name`. Trocar o
  `USERNAME_FIELD` depois é justamente a migração cara que esta decisão evita — e o produto
  autentica por e-mail, que é o que o M2.1 vai construir.
- `PermissionsMixin` entra junto porque, sem ele, o `auth` ficaria instalado pela metade:
  presente para sustentar o `AUTH_USER_MODEL`, inútil para qualquer outra coisa. É aditivo e
  barato agora; depois, é migração sobre a tabela de usuário.
- `django.contrib.auth` e `django.contrib.contenttypes` entram em `INSTALLED_APPS` no F4.
  **Nenhum middleware é exigido:** a checagem de `AuthenticationMiddleware` (`auth.E013`) só
  dispara com `LoginRequiredMiddleware` presente, e ela não está. Sessão e autenticação de
  requisição continuam sendo do M2.1.
- Como o `User` do projeto é `swappable`, a tabela `auth_user` **não nasce**. Do `auth`
  sobram `auth_permission`, `auth_group` e `auth_group_permissions`.
- Existe um gerente com `create_user` e `create_superuser` que **exigem organização** — sem
  ele, `createsuperuser` não teria como criar usuário válido.
- O campo que distingue organização pessoal de organização real ([D-24](D-24-organizacao-desde-a-primeira-migration.md))
  **não** entra no F4: nada o lê, e acrescentar coluna depois é migration aditiva barata. É
  do M2.1.

Origem: [spec F4 — Fundação de dados](../specs/F4-fundacao-de-dados.md).
