# D-16 — Resultado e imutavel

**Status:** aceita · 2026-08-29

## Contexto

Auditoria costuma exigir responder "quem alterou este numero e quando", o que e caro de rastrear.

## Decisão

**Nunca se atualiza um resultado.** Recalcular gera execucao nova, com manifesto novo. O historico so cresce.

## Consequências

- Elimina a pergunta mais dificil de auditoria, porque ninguem altera nada.
- Torna a auditoria quase gratuita: dado vem da bronze, calculo vem do manifesto, e so acesso e alteracao de configuracao precisam de mecanismo dedicado.
