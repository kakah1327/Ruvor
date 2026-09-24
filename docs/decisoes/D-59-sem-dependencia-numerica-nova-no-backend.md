# D-59 — Sem dependência numérica nova no backend

**Status:** aceita · 2026-09-24

## Contexto

Volatilidade, beta, correlação, assimetria e curtose são o caso de uso canônico de `numpy` e
`pandas`. As dependências de `backend/pyproject.toml` são `django`, `djangorestframework`,
`celery`, `redis` e `psycopg`; a imagem `web` tem 467 MB e é leve de propósito
([D-17](D-17-monorepo-engine-sem-django.md)), enquanto a `worker`, com ML, tem 3,79 GB.

## Decisão

O M1.3 não acrescenta dependência ao backend. O cálculo usa a biblioteca padrão:
`statistics` (`linear_regression`, `correlation`, `fmean`, `stdev`, `pstdev`), `decimal`,
`math` e `calendar`.

A precisão é escolhida por grupo, não uniformizada: retorno, *yield*, dividendo e volume
percorrem `Decimal` do início ao fim; volatilidade, beta, correlação, assimetria e curtose
passam por `float` no `statistics` e voltam a `Decimal` na saída.

## Consequências

- `backend/pyproject.toml` fica **intocado** pelo bloco, e isso é verificado: o critério V-15
  é `git diff --exit-code HEAD -- backend/pyproject.toml` mais um `grep` que recusa
  `import numpy`/`pandas` em `backend/apps/analytics/`. Rodou verde na T4 e de novo na T8,
  com o app completo.
- Os divisores divergem de propósito e não devem ser uniformizados: volatilidade usa `stdev`
  (amostral, `n−1`); assimetria e curtose usam `pstdev` (populacional, `n`), com a curtose
  subtraindo 3.
- O dia em que uma métrica não couber na biblioteca padrão, a decisão se revisa — e o lugar
  natural é o motor, pela [D-58](D-58-calculo-da-camada-2-mora-no-backend.md), não uma
  dependência nova na `web`.

Origem: [spec M1.3 — Camadas 1 e 2](../specs/M1.3-camadas-1-e-2.md).
