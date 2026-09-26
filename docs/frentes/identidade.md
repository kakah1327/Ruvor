# Frente `identidade`

**Dono:** ⏸ **sem dono.** A frente está pronta para quem entrar no time; até lá, não começa
**Bloco:** M2.1 — Identidade e acesso: autenticação, papéis, permissões e telas de login
([ROADMAP](../ROADMAP.md#marco-2--vira-plataforma)).
**Cerca:** `backend/apps/accounts/` e os testes dela; telas de login só depois do casco do M1.6.
Detalhe em [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-100 a D-119.

---

## Agora

**Etapa:** não começou — espera um dono
**Ramo:** `identidade/M2.1-identidade-e-acesso`, ainda não criado

## Próximo passo

1. Ler, nesta ordem: [`CLAUDE.md`](../../CLAUDE.md), [`PROCESSO.md`](../PROCESSO.md),
   [`aprendizados.md`](../aprendizados.md) e [`FRENTES.md`](../FRENTES.md).
2. Subir o ambiente (`docker compose up`) e rodar a suíte no `worker`, como diz o `CLAUDE.md`.
   Isso prova a máquina antes de qualquer código.
3. Criar o ramo a partir da `main`.
4. **Escrever a spec do M2.1**, conversando com o dono da frente. O modelo de spec mais próximo é
   o do [F4](../specs/F4-fundacao-de-dados.md), que criou o usuário e a organização.

## O que a spec do M2.1 encontra pronta, e precisa ler

- **O usuário e a organização já existem**, desde o F4: `core.user` autentica por e-mail e herda
  `AbstractBaseUser` ([D-39](../decisoes/D-39-usuario-proprio-autentica-por-email.md)); todo
  usuário tem organização obrigatória ([D-24](../decisoes/D-24-organizacao-desde-a-primeira-migration.md));
  a organização fixa do Marco 1 tem `slug` `ruvor`.
- **O usuário é exceção permanente ao filtro por organização**, e o M2.1 precisa isolar a
  listagem de usuários por outro meio ([D-41](../decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md)).
- **Duas dívidas registradas vencem neste bloco** ([ESTADO](../ESTADO.md#dívida-registrada)):
  - `createsuperuser` não funciona: o gerente exige organização e o comando não tem como
    fornecê-la. O M2.1 decide como o primeiro usuário nasce.
  - `gold.risk_run.requested_by` é sempre nulo. O arquivo (`apps/risk/models.py`) é da frente
    `marco1`: combinar com ela na spec quem escreve a linha.
- **O parecer da CVM não bloqueia este bloco**: autenticação não informa nem recomenda
  investimento ([D-84](../decisoes/D-84-frentes-com-cerca-de-pastas.md)). Bloqueia a
  carteira, o M2.2.

## O que esta frente espera de outras

| De | O quê | Estado |
|---|---|---|
| `marco1` | **convenções da API HTTP**: prefixo, versão, formato de erro. A autenticação da API é deste bloco, e precisa casar com elas | 🔴 aberto. Decidir numa decisão própria antes da primeira spec que publicar rota, com as duas frentes na revisão |
| `marco1` | **casco do frontend e kit completo**, para as telas de login | ⬜ vem no M1.6. Até lá, só o backend |

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84 |
