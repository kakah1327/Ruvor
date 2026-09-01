# D-24 — Organizacao existe desde a primeira migration

**Status:** aceita · 2026-08-29

## Contexto

Multi-tenancy so sera usada depois da entrega do TCC, mas enxertar isolamento em sistema com dados dentro e caro e arriscado.

## Decisão

Existe a entidade **Organizacao** desde a primeira migration; todo usuario pertence a uma; conta individual ganha organizacao pessoal implicita, invisivel na interface.

## Consequências

- Neste produto o isolamento e pequeno: catalogo, precos e analise por acao sao **compartilhados**; so carteira, alertas, usuarios e chaves de API sao privados.
- **O que isola nao e a coluna, e a consulta filtrar.** Uma classe base aplica o filtro por padrao, para que esquecer deixe de ser possivel.
- Custo agora: meio dia. Custo depois: migrar tabelas com dado real e revisar toda consulta procurando vazamento.
- Escala de pessoa fisica a empresa sem migracao — padrao usado por GitHub e Linear.
