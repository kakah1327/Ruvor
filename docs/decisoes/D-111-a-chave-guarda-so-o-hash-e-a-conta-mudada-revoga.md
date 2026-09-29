# D-111 — A chave guarda só o SHA-256 do segredo, mostrado uma vez; desativar e redefinir a senha revogam as chaves

**Status:** aceita · 2026-09-28 · frente `identidade`

## Contexto

Uma chave (D-108) é uma credencial de longa duração. Se o banco vazar, o segredo não pode sair
com ele; e a pessoa que perde o acesso não pode continuar lendo pela chave.

## Decisão

`core.api_key` guarda o `prefix` (8 hexadecimais, único, a busca), o SHA-256 do segredo, o nome,
os escopos (`["read"]`), `created_at`, `last_used_at` e `revoked_at`. O segredo aparece **uma vez**,
no 201 da criação. A autenticação compara o hash em tempo constante. `last_used_at` é gravado no
máximo uma vez por minuto. Desativar a pessoa e redefinir a senha provisória revogam toda chave
ativa dela, na mesma transação, com `api_key_revoked` e o `via` na auditoria; reativar não
devolve. Trocar a própria senha não revoga.

## Consequências

- Perdeu o segredo, cria outra chave: não há como mostrá-lo de novo.
- SHA-256 sem sal basta: o segredo é aleatório, 32 bytes, e não senha escolhida por gente.

Origem: [spec M4.2 — API pública](../specs/M4.2-api-publica.md).
