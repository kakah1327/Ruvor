# Frente `identidade`

**Dono:** kakah1327 (Kauã), desde 2026-09-27 — também dono da `fundamentos`, que está parada
**Blocos:** M2.1a — Identidade e acesso (backend) → M2.1b — As telas de acesso
([ROADMAP](../ROADMAP.md#marco-2--vira-plataforma)).
**Cerca:** `backend/apps/accounts/` e os testes dela; telas de login só depois do casco do M1.6.
Detalhe em [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-100 a D-119.

---

## Agora

**Bloco:** M2.1a — Identidade e acesso
**Etapa:** spec em escrita ([`specs/M2.1a-identidade-e-acesso.md`](../specs/M2.1a-identidade-e-acesso.md)); auto-revisão e revisão adversarial pendentes
**Ramo:** `identidade/M2.1-identidade-e-acesso`, criado em 2026-09-27 a partir da `main` com o plano do M1.6a (PR #10)

## Próximo passo

1. Auto-revisão e revisão adversarial da spec; depois o PR dela, que **passa pela `marco1`**:
   muda `apps/api/errors.py`, o `REST_FRAMEWORK` e o `POST /risk` (ver *Contratos com outras
   frentes* na spec).
2. Combinar com a `marco1` a migration de `core.compute_request.requested_by` (RF-26).
3. O plano. A implementação espera o M1.6a na `main` (a base da API e o `POST /risk`).

## O que esta frente espera de outras

| De | O quê | Estado |
|---|---|---|
| `marco1` | **convenções da API HTTP** | ✅ [D-86](../decisoes/D-86-convencoes-da-api-http.md) |
| `marco1` | **a base da API** (`apps/api`, o tratador de erro, `REST_FRAMEWORK`) e o `POST /risk` | ⬜ M1.6a, plano aprovado, implementação não começou |
| `marco1` | a migration de `core.compute_request.requested_by` | 🔴 a combinar |
| `marco1` | **casco do frontend e kit completo**, para as telas do M2.1b | ⬜ M1.6a/M1.6b |

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84 |
| 2026-09-27 | o Kauã assume a frente. Decidido com o dono: M2.1 dividido em M2.1a (backend) e M2.1b (telas); sessão do Django com CSRF; cadastro aberto com organização pessoal; papéis `admin` e `member` por organização; organização real por comando, usuário criado pela administradora com senha provisória; auditoria de eventos de acesso; recuperação de senha por e-mail fora (dívida); `requested_by` preenchido por este bloco, com revisão da `marco1`. Máquina preparada (`docker compose up`). Spec escrita, com as premissas conferidas no DRF 3.18.1 e no Django 6.1.1 |
