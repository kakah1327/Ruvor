# D-08 — Dono do dado no schema desde a primeira migration

**Status:** aceita · 2026-08-29

## Contexto

A plataforma tera usuarios, mas o Marco 1 nao precisa de tela de login. A tentacao e adiar o conceito de propriedade do dado.

## Decisão

**Toda tabela privada nasce sabendo a quem pertence**, desde a primeira migration. As telas de login so aparecem no Marco 2.

## Consequências

- Durante o Marco 1 existe um dono fixo e a interface nunca menciona isso.
- O caro nunca foi a tela de login — e descobrir depois que 15 tabelas nao sabem de quem sao e ter que migrar com dados dentro.
- Ver D-24 para a estrutura de organizacao.
