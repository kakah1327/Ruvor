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

**Bloco:** M4.1 — Relatórios. O M4.2 fechou e entrou na `main` (PR #15, 2026-09-29); o M2.1a tem
as duas fases na `main` menos a `requested_by`, que espera a migration da `marco1`
**Etapa:** spec do M4.1 aprovada pelo dono; plano aprovado pelo dono; **T0 executada** (linha de base verde); próxima, a T1
**Ramo:** `identidade/M4.1-relatorios`

## Próximo passo

1. Executar o M4.1, T0 a T6.
2. A migration de `core.compute_request.requested_by` (RF-26 do M2.1a), pedida à `marco1` no
   contrato literal do plano da fase 2. Com ela na `main`: a T14, as mutações 32 e 33 e a T16 do
   M2.1a.

## O que esta frente espera de outras

| De | O quê | Estado |
|---|---|---|
| `marco1` | **convenções da API HTTP** | ✅ [D-86](../decisoes/D-86-convencoes-da-api-http.md) |
| `marco1` | **a base da API** (`apps/api`, o tratador de erro, `REST_FRAMEWORK`) e o `POST /risk` — só a fase 2 espera: as rotas de conta e a permissão nas views de `apps/api` | ✅ M1.6a na `main` (PR #12, 2026-09-28) |
| `marco1` | a migration de `core.compute_request.requested_by` | 🔴 a pedir — contrato no [plano da fase 2](../planos/M2.1a-identidade-e-acesso.md#pré-condição-externa--a-coluna-requested_by) |

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84 |
| 2026-09-27 | o Kauã assume a frente. Decidido com o dono: M2.1 dividido em M2.1a (backend) e M2.1b (telas); sessão do Django com CSRF; cadastro aberto com organização pessoal; papéis `admin` e `member` por organização; organização real por comando, usuário criado pela administradora com senha provisória; auditoria de eventos de acesso; recuperação de senha por e-mail fora (dívida); `requested_by` preenchido por este bloco, com revisão da `marco1`. Máquina preparada (`docker compose up`). Spec escrita, com as premissas conferidas no DRF 3.18.1 e no Django 6.1.1 |
| 2026-09-27 | **correção de escopo** (decisão do darkside171): as telas não são desta frente — toda interface visual é da `marco1`. Blocos da frente: M2.1 → M4.2 → M4.1; cerca sem telas; o M2.1 não depende do M1.6b. Spec do M2.1a, `FRENTES.md` e `ROADMAP.md` corrigidos |
| 2026-09-27 | spec do M2.1a: revisão 1 reprovou (1 grave, 11 médios, 12 leves), a 2 aprovou; aprovada pelo dono. Plano da fase 1: revisão 1 reprovou (1 grave: a restauração depois do `flush`), a 2 aprovou; aprovado. **Fase 1 implementada**: T1 a T6, 18 mutações reprovando, execução real (14 eventos no `access_event`, bloqueio no Redis banco 1). Suíte com 721 testes. Achado: o `flush` do `transaction=True` não vê as tabelas fora do `public` |
| 2026-09-28 | PR #11 (spec, plano e fase 1) e PR #12 (M1.6a) na `main`; a fase 2 está desbloqueada. Ramo atualizado com a `main`. Plano da fase 2 escrito, em rascunho: T9 a T16, com três armadilhas do DRF 3.18.1 conferidas no código (import circular da classe de autenticação, `ScopedRateThrottle` conta por usuário, o tratador não põe cabeçalho) |
| 2026-09-28 | Plano da fase 2 aprovado (revisão 1 aprovou, 5 médios e 11 leves absorvidos). **T9 a T13 implementadas**, um commit cada: o `banco_limpo`, o tratador com 401/400/429 e os cabeçalhos, a sessão com CSRF na API, `AccountReady`, o limite `auth` por IP, as rotas `auth/*` e `organization/users*`. Suíte com 1021 testes, verde; mypy e ruff limpos; 15 mutações reprovando; V-25 pelo proxy do Vite (9 eventos no `access_event`, IP do contêiner `frontend`). A T14 espera a migration da `marco1` |
| 2026-09-28 | M4.2: spec e plano aprovados pelo dono, com duas decisões de direção (o filtro automático por organização nasce aqui, e a taxa anônima fica em 60 por minuto, ajustável) e uma errata (o `settings_test.py` no inventário). **T0 a T5 executadas:** drf-spectacular 0.30.0, que gera e valida no Django 6.1.1; o contexto da organização; `core.api_key` com o gerente que falha fechado; os serviços de chave; a autenticação por `Bearer`; o alcance da chave. Suíte com 1093 testes, verde. Uma rodada da T2 teve 1 falha por edição feita durante a suíte, não do estado da T2 |
| 2026-09-28 | M4.2: **T6 a T10 executadas.** As rotas `api-keys*`; a taxa em toda rota (`ApiRateThrottle`, as três variáveis, `settings_test.py` fixando-as vazias); o esquema OpenAPI em `/api/v1/schema`, com `AutoSchema` próprio e `ENUM_NAME_OVERRIDES` para os dois `kind` e os dois `status`. Suíte com 1147 testes, verde; 19 mutações reprovando; V-16 pelo proxy do Vite. D-108 a D-112. A porta do PostgreSQL (`55432`) caiu numa faixa reservada do Windows depois de reiniciar: `.env` local com `15432` |
| 2026-09-29 | M4.2 mesclado na `main` (PR #15). M4.1 aberto, decidido com o dono: o relatório de risco do ativo (camada 3), JSON como original e CSV derivado, PDF fora; guardado e imutável em `core.report`, com o SHA-256 dos bytes; gerar pela sessão, listar e baixar pela sessão ou pela chave; o relatório é de toda a organização; no conteúdo, só o nome de quem pediu, e o e-mail na coluna. Spec escrita; revisão 1 reprovou (1 grave, 5 médios, 7 leves), a 2 aprovou; aprovada pelo dono. Plano escrito; revisão 1 reprovou (2 graves, 1 médio, 8 leves), a 2 aprovou; aprovado pelo dono |
| 2026-09-29 | M4.1: plano escrito; revisão 1 reprovou (2 graves: o `operationId` de lista e item que colide, e a comparação de bytes cega à troca por `Response`), a 2 aprovou; aprovado pelo dono. **T0 executada**: ramo na `main` `ad86c04`; `migrate` sem nada a aplicar, `makemigrations --check` limpo, `spectacular --validate --fail-on-warn` com 0, `mypy` sem erros em 211 arquivos, `ruff` limpo, suíte com `1215 passed` em 15 min 46 s |
