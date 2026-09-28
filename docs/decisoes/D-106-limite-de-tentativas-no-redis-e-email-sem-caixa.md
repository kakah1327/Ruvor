# D-106 — O limite de tentativas conta no cache do Django, no Redis, num banco próprio: por IP e por (e-mail, IP); o e-mail é único sem diferença de caixa

**Status:** aceita · 2026-09-27 · frente `identidade`

## Contexto

Sem `CACHES`, o cache do Django é o de memória, por processo: cada processo contaria à parte. O
banco 0 do Redis é o broker e o backend de resultados do Celery, e o `clear()` do `RedisCache` é
`flushdb`. E o e-mail diferenciava caixa: `Ana@x.com` e `ana@x.com` seriam duas contas.

## Decisão

`CACHES["default"]` é o `RedisCache` em `RUVOR_CACHE_URL`, **banco 1** por padrão, `KEY_PREFIX`
`ruvor`; nenhum código de `apps/` chama `cache.clear()`, e a suíte usa o cache de memória. A entrada
bloqueia **por (e-mail, IP)** — 5 falhas em 15 minutos bloqueiam o par por 15 minutos, mesmo com a
senha certa —, e a fase 2 soma o limite do DRF **por IP** (10 por minuto). O e-mail é guardado e
comparado em minúsculas, e o banco garante com `UniqueConstraint(Lower("email"))`.

## Consequências

- A chave é o par para que ninguém trave, de outro endereço, a conta alheia; quem troca de IP é
  contido só pelo limite por IP.
- Sem hospedagem, o IP é o `REMOTE_ADDR`: em dev, o do contêiner do Vite, e o limite por IP vira
  global. `NUM_PROXIES` é revisto com a hospedagem.

Origem: [spec M2.1a — Identidade e acesso](../specs/M2.1a-identidade-e-acesso.md).
