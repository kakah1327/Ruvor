# D-104 — A auditoria de acesso mora em `core.access_event`, que só cresce; ninguém a lê neste bloco, e o filtro por organização é do primeiro bloco que a ler — restringe a D-41

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

A [ARQUITETURA](../ARQUITETURA.md) diz que acesso e alteração são o único eixo de auditoria que
precisa de mecanismo dedicado. A [D-41](D-41-filtro-por-organizacao-na-primeira-tabela-privada.md)
manda o bloco que cria tabela privada entregar o filtro automático por organização.

## Decisão

`core.access_event` guarda um evento por linha — `signup`, `login`, `login_failed`,
`login_throttled`, `logout`, `password_changed`, `user_created`, `user_updated`,
`temporary_password_reset` —, **na mesma transação** da mudança que descreve, e **nunca** é
alterada nem apagada: o modelo e o `QuerySet` recusam. Nunca guarda senha. **Nenhuma rota a lê neste
bloco**, e por isso o filtro automático por organização que a D-41 pede fica com o **primeiro bloco
que a ler**.

## Consequências

- Restringe a D-41 só para esta tabela, e só enquanto não houver leitor.
- "Quem viu o quê" (leitura) não é registrado: dado público não diz nada, e o dado privado nasce
  no M2.2, que registra a leitura dele.
- `login_failed` e `login_throttled` levam o dono da conta em `target`, não em `actor`: quem
  tentou não é necessariamente ele.

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
