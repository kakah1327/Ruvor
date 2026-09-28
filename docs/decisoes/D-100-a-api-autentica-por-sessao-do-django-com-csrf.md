# D-100 — A API autentica por sessão do Django, com CSRF; 401 com `WWW-Authenticate: Session`

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

A [D-86](D-86-convencoes-da-api-http.md) deixou o mecanismo de autenticação para o M2.1: o M1.6a
publica a API com `DEFAULT_AUTHENTICATION_CLASSES` vazio. As alternativas eram sessão do Django,
JWT (`simplejwt`) e o token do DRF. O frontend e a API moram na mesma origem — o Vite repassa
`/api` à `web` em dev, e a hospedagem fará o mesmo.

## Decisão

**A API autentica por sessão do Django**, em cookie `HttpOnly`, com CSRF: o frontend lê o
`csrftoken` e o devolve em `X-CSRFToken`. A classe do DRF é uma subclasse própria da
`SessionAuthentication` que devolve `"Session"` em `authenticate_header` — sem isso, o DRF rebaixa o
401 a 403 (`APIView.handle_exception`) — e que responde `csrf_failed` quando o CSRF falha.
`signup` e `login`, feitos por quem ainda não tem sessão, conferem o CSRF explicitamente: a classe
do DRF só o exige de quem já está logado.

## Consequências

- Sem dependência nova, e a saída encerra a sessão no servidor; token no navegador seria
  problema de armazenamento e de revogação.
- Quem está logado passa a mandar `X-CSRFToken` em todo pedido de escrita, inclusive no
  `POST /risk` do M1.6a, que segue aberto a anônimo sem CSRF.
- Cliente fora do navegador não é deste mecanismo: é do M4.2, com chave própria.
- `Secure` nos cookies segue `RUVOR_SECURE_COOKIES`, desligado no ambiente local (HTTP).

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
