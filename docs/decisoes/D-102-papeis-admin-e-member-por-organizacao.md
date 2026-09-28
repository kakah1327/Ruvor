# D-102 — Dois papéis por organização, `admin` e `member`; `is_staff` é da plataforma; toda view que exige conta declara `AccountReady`

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

O usuário tinha só `is_staff` e `is_superuser`, que são da plataforma. Nada dizia quem administra
uma organização.

## Decisão

`core.user.role`, escolhas fechadas **`admin`** e **`member`**. `admin` gerencia os usuários da
própria organização; `member` usa o produto. `is_staff` e `is_superuser` não dão poder em
organização nenhuma. **Toda view que exige conta declara `AccountReady`** (autenticado e sem senha
provisória); `IsAuthenticated` puro, só `me`, `password` e `logout` — um teste da fase 2 reprova o
resto.

## Consequências

- Acrescentar papel é aditivo; mudar os dois exige decisão.
- A regra de quem pode gerir mora no serviço, nesta ordem: senha provisória, papel, organização
  pessoal.
- A organização nunca fica sem `admin` ativo: a mudança trava a linha da organização.

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
