# D-143 — A busca ignora acento pela extensão `unaccent` do PostgreSQL

**Status:** aceita · 2026-09-29 · spec do [M1.7](../specs/M1.7-busca-e-catalogo.md)

## Contexto

A busca do M1.6a (RF-12) casa o nome e o nome de pregão sem distinção de caixa, mas com distinção de
acento. O catálogo guarda os textos como a B3 os entrega ([D-47](D-47-fonte-do-catalogo-e-o-site-da-b3.md)),
uns com acento, outros sem ("ITAU UNIBANCO", "ALLIANÇA SAÚDE"), e quem digita não sabe qual é qual. Havia
duas saídas: a extensão `unaccent` do PostgreSQL na consulta, ou uma coluna normalizada em `silver.asset`,
preenchida na conformação.

## Decisão

**A busca aplica `UNACCENT` ao texto do catálogo e ao texto procurado**, pelo lookup `unaccent` do
`django.contrib.postgres`, com a extensão criada por migration em `apps/assets`. O `silver` não ganha
coluna. Decisão do dono da frente, 2026-09-29.

## Consequências

- O banco de qualquer ambiente precisa da extensão `unaccent`. Ela é do `contrib` do PostgreSQL e *trusted*
  desde a versão 13: a hospedagem a herda como requisito.
- A busca não usa índice; com o catálogo na casa das centenas, não precisa. Um índice funcional exigiria
  embrulhar `unaccent`, que não é `IMMUTABLE`.
- A regra vale nos dois sentidos, e a API pública do M4.2 passa a devolver mais resultados para a mesma
  consulta, nunca menos.
