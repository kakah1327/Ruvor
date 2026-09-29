# D-109 — Toda rota da API tem taxa: por chave, por usuário e, para anônimo, por IP, ajustável por variável

**Status:** aceita · 2026-09-28 · frente `identidade`

## Contexto

O M1.6a abriu a leitura sem login e sem limite. Com a chave (D-108), um cliente automático pode
pedir sem parar, e a leitura anônima também.

## Decisão

`ApiRateThrottle`, em `apps/accounts/throttling.py`, é a `DEFAULT_THROTTLE_CLASSES`. O escopo sai
de quem pediu: a chave conta pelo `prefix` (`api_key`, 600/min), a sessão pelo usuário (`user`,
600/min) e o anônimo pelo IP (`anon`, 60/min). As três taxas vêm de `RUVOR_THROTTLE_API_KEY`,
`RUVOR_THROTTLE_USER` e `RUVOR_THROTTLE_ANON`; ausente ou vazia vale o padrão. `signup`, `login` e
`password` continuam só com o limite `auth` da D-106. Estourou → 429 `too_many_requests`, com
`Retry-After`. A leitura continua sem login.

## Consequências

- A taxa roda depois da autenticação e da permissão: 401 e 403 não contam nem são limitados.
- Em dev, todo pedido do navegador chega com o IP do contêiner `frontend`, e a taxa anônima vira
  global: suba `RUVOR_THROTTLE_ANON` no `.env`.
- Em produção, sem `NUM_PROXIES` certo, a taxa anônima vira teto do site inteiro. A hospedagem
  revê `NUM_PROXIES` antes de expor a API (dívida).
- A suíte fixa as três variáveis vazias em `config/settings_test.py`: ela mede a taxa real, e não
  a do `.env` de dev.

Origem: [spec M4.2 — API pública](../specs/M4.2-api-publica.md).
