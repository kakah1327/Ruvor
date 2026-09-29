# D-112 — O filtro automático por organização nasce no M4.2, em `core.api_key`

**Status:** aceita · 2026-09-28 · frente `identidade`

## Contexto

A D-41 manda que a primeira tabela privada nasça com o filtro automático por organização, e que o
bloco que a cria o entregue. `core.api_key` é essa tabela; o M2.2 vem depois.

## Decisão

O mecanismo mora em `apps/accounts/tenancy.py`, Django puro. O contexto é um `ContextVar` com o
`organization_id`. `OrganizationScopedManager`, o gerente padrão da tabela privada, filtra pelo
campo `organization_field` do modelo e, **sem organização no contexto, levanta
`OrganizationScopeMissing`** — falha fechada, nunca "devolve tudo". O gerente base
(`Meta.base_manager_name`) é um `Manager()` sem escopo, para o Django (`save`, `refresh_from_db`,
exclusão); a saída explícita sem escopo (`ApiKey.unscoped`) só em lugar nomeado —
`apps/accounts/authentication.py` —, guardado por teste. O contexto é posto pela autenticação do
pedido (sessão e chave), e o `OrganizationScopeMiddleware` o zera no começo e no fim de cada
pedido; dentro dos serviços, pelo próprio serviço, com `organization_scope(<organização de quem
pede>)`, que funciona igual pela rota, pelo teste, por comando ou numa thread.

## Consequências

- Cumpre a D-41 antes do M2.2, que passa a só aplicá-lo às tabelas dele.
- `core.user` e `core.access_event` ficam fora: o usuário é a fonte da organização, e a
  auditoria segue a D-104.
- Teste usa `force_login`, e não `force_authenticate`: este pula a autenticação, e o contexto não
  é posto.

Origem: [spec M4.2 — API pública](../specs/M4.2-api-publica.md).
