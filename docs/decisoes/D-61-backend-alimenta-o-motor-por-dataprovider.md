# D-61 — O backend alimenta o motor por um `DataProvider`, e o motor não aprende a plataforma

**Status:** aceita · 2026-09-24

## Contexto

O M1.4 é o primeiro bloco em que a plataforma **consome** o motor. A
[D-17](D-17-monorepo-engine-sem-django.md) manda que `engine/` nunca importe Django, e um
teste do motor prova isso (`engine/tests/test_modulos_proibidos.py`). Havia duas rotas: dar
ao motor um leitor de `silver.price` — que o faria conhecer o ORM —, ou o backend
implementar o contrato que o motor já pede.

O contrato já existia e é estreito: `engine/src/engine/data/providers/base.py` define
`DataProvider.fetch(ticker, start, end)` devolvendo um `DataFrame` com a coluna `close`, e
`run_experiment(config, provider)` recebe o provedor **por parâmetro**.

## Decisão

O backend implementa o contrato. `backend/apps/risk/provider.py` traz
`SilverPriceProvider`, que lê `silver.price` pelo ORM e devolve o `DataFrame` que o motor
espera. O motor não aprende o que são `Asset`, `Price` ou `silver`, e nenhuma linha do motor
é alterada para que a costura exista.

O `SilverPriceProvider` é um `DataProvider` honesto: **filtra pelo intervalo pedido**, em vez
de ignorá-lo porque o único chamador de hoje passa a janela inteira.

## Consequências

- `apps/risk/provider.py` é o único arquivo do repositório que conhece os dois lados. Quem
  precisar de outra fonte escreve outro provedor, e o motor segue igual.
- O intervalo do provedor é **fechado dos dois lados** (`date__lte=end`), ao contrário do
  `YFinanceProvider` do motor, que delega ao `yf.download` e tem `end` exclusivo. Um `end`
  exclusivo engoliria o último pregão e faria o `as_of_date` do manifesto sair errado.
- O `adj_close` é convertido para `float` antes de entrar no `DataFrame`: `Decimal` na coluna
  produz `dtype=object` e o `np.log` do `log_returns` quebra.
- Série vazia devolve `DataFrame` vazio, não levanta. Quem decide o que fazer com ativo sem
  preço é o `compute.py`, pelo piso de `MIN_SESSIONS`.
- O backend passa a importar `pandas` — mas **não o declara como dependência**: ele chega
  pelo motor, que só é instalado no `worker`. Preserva a
  [D-59](D-59-sem-dependencia-numerica-nova-no-backend.md) no que ela protege, que é o peso
  da imagem `web`.

Origem: [spec M1.4 — Motor de risco](../specs/M1.4-motor-de-risco.md) (RF-04, RF-06).
