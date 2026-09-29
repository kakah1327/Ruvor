# D-108 — A API aceita chave pessoal de leitura; estende a D-100

**Status:** aceita · 2026-09-28 · frente `identidade`

## Contexto

A D-100 deixou a sessão do Django com CSRF como a única autenticação da API, e o cliente fora do
navegador para o M4.2. Um script ou uma planilha não guarda cookie nem faz o passo do CSRF.

## Decisão

Uma pessoa logada cria chaves pessoais, até 10 ativas, em `POST /api/v1/api-keys`, e as revoga em
`DELETE /api/v1/api-keys/{prefix}`. A chave vai em `Authorization: Bearer rvr_<prefix>_<corpo>`,
pela `ApiKeyAuthentication`, depois da sessão em `DEFAULT_AUTHENTICATION_CLASSES`. Ela **age como
a dona** e **só lê**: alcança a view que declara `api_key_scope = "read"`, e só por método seguro.
**O padrão é recusar** — view sem o atributo, ou com `None`, responde 403 `api_key_not_allowed`.
Toda view sob `/api/` declara o atributo no próprio corpo, e um teste sobre o resolvedor confere.
Qualquer falha da chave é o mesmo 401 `invalid_api_key`. A chave não passa pelo CSRF: não é cookie.

## Consequências

- Conta, gestão e as próprias chaves só pela sessão: uma chave vazada não cria outra nem muda
  conta.
- Toda view nova declara `api_key_scope`; quem esquecer tem a chave recusada, e o teste de
  declaração reprova.
- Recusa de alcance conta como uso da chave (`last_used_at`), porque a autenticação já passou.

Origem: [spec M4.2 — API pública](../specs/M4.2-api-publica.md).
