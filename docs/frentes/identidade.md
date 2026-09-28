# Frente `identidade`

**Dono:** kakah1327 (Kauã), desde 2026-09-27 — também dono da `fundamentos`, que está parada
**Blocos:** M2.1 — Identidade e acesso (spec e plano como **M2.1a**, em duas fases) → M4.2 —
API pública → M4.1 — Relatórios ([ROADMAP](../ROADMAP.md)).
**Cerca:** `backend/apps/accounts/` e os testes dela. **Sem telas:** toda interface visual —
telas, mockups, kit — é da `marco1` (decisão do darkside171, 2026-09-27), inclusive as de login;
esta frente descreve as rotas que elas consomem.
Detalhe em [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-100 a D-119.

---

## Agora

**Bloco:** M2.1a — Identidade e acesso
**Etapa:** spec e plano da fase 1 aprovados; **fase 1 implementada** (T1 a T8) — faltam as PRs (spec, plano e fase 1); a fase 2 espera o M1.6a
**Ramo:** `identidade/M2.1-identidade-e-acesso`, criado em 2026-09-27 a partir da `main` com o plano do M1.6a (PR #10)

## Próximo passo

1. As PRs da spec (que **passa pela `marco1`**: muda `apps/api/errors.py`, o `REST_FRAMEWORK` e o
   `POST /risk`), do plano e da fase 1. O merge é do dono da frente, com a CI verde (D-85).
2. Combinar com a `marco1` a coluna e a migration de `core.compute_request.requested_by` (RF-26).
3. Quando o M1.6a estiver na `main`: o plano da fase 2, no mesmo arquivo do plano, e a
   implementação dela.

## O que esta frente espera de outras

| De | O quê | Estado |
|---|---|---|
| `marco1` | **convenções da API HTTP** | ✅ [D-86](../decisoes/D-86-convencoes-da-api-http.md) |
| `marco1` | **a base da API** (`apps/api`, o tratador de erro, `REST_FRAMEWORK`) e o `POST /risk` — só a fase 2 espera: as rotas de conta e a permissão nas views de `apps/api` | ⬜ M1.6a, plano aprovado, implementação não começou |
| `marco1` | a migration de `core.compute_request.requested_by` | 🔴 a combinar |

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84 |
| 2026-09-27 | o Kauã assume a frente. Decidido com o dono: M2.1 dividido em M2.1a (backend) e M2.1b (telas); sessão do Django com CSRF; cadastro aberto com organização pessoal; papéis `admin` e `member` por organização; organização real por comando, usuário criado pela administradora com senha provisória; auditoria de eventos de acesso; recuperação de senha por e-mail fora (dívida); `requested_by` preenchido por este bloco, com revisão da `marco1`. Máquina preparada (`docker compose up`). Spec escrita, com as premissas conferidas no DRF 3.18.1 e no Django 6.1.1 |
| 2026-09-27 | **correção de escopo** (decisão do darkside171): as telas não são desta frente — toda interface visual é da `marco1`. Blocos da frente: M2.1 → M4.2 → M4.1; cerca sem telas; o M2.1 não depende do M1.6b. Spec do M2.1a, `FRENTES.md` e `ROADMAP.md` corrigidos |
| 2026-09-27 | spec do M2.1a: revisão 1 reprovou (1 grave, 11 médios, 12 leves), a 2 aprovou; aprovada pelo dono. Plano da fase 1: revisão 1 reprovou (1 grave: a restauração depois do `flush`), a 2 aprovou; aprovado. **Fase 1 implementada**: T1 a T6, 18 mutações reprovando, execução real (14 eventos no `access_event`, bloqueio no Redis banco 1). Suíte com 721 testes. Achado: o `flush` do `transaction=True` não vê as tabelas fora do `public` |
