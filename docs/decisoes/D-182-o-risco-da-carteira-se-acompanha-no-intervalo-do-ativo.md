# D-182 — O risco da carteira se acompanha no mesmo intervalo do risco do ativo

**Status:** aceita · 2026-10-03, com a spec do M2.2b · registrada no fecho do bloco, 2026-10-07 · frente `marco1`

## Contexto

O cálculo do risco da carteira roda os nove modelos no `worker` e leva minutos: ~2,5 min no ESTADO, e 188 s na execução
real do M2.2b, com duas ações. A spec do M2.2a sugeria uma consulta de "~2 s … como a do ativo". A tela do ativo,
porém, consulta a cada **5 s** (`POLL_INTERVAL_MS` de `frontend/src/risk/usePolling.ts`, desde o M1.6a).

## Decisão

1. **O risco da carteira é relido a cada 5 s** enquanto o `GET .../risk` trouxer `in_progress`. A consulta para ao
   sair da página, fica suspensa com a aba oculta e pede na hora quando a aba volta.
2. **O `usePolling` passa a ser genérico** e serve às duas telas. A carteira passa o `attempt` da fonte
   (`frontend/src/portfolio/useRiskSource.ts`). Um erro numa releitura (rede, 5xx, 429) mantém o que estava na tela,
   e a consulta continua. O ativo segue como era: um `/risk` em erro para a consulta, e o "tentar de novo" a retoma.

## Consequências

- São 12 leituras por minuto durante o cálculo. A taxa do usuário logado é `RUVOR_THROTTLE_USER`, 600 por minuto.
- O comportamento da tela do ativo não muda: a suíte dela segue verde sem mudança de teste.
