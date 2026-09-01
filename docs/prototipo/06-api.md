# 06 — API e frontend

## Papel do Flask

O Flask é **API JSON pura** — não renderiza HTML. Tem três consumidores independentes que
não se conhecem: a SPA React, a CLI e a suíte de testes. O contrato abaixo é a única
fronteira entre backend e frontend.

Em produção, depois de `npm run build`, o mesmo processo Flask também serve os estáticos
de `frontend/dist` (detectado na inicialização) — 1 processo em vez de 2.

> **Divergência com o TCC.** A seção 3.2 descreve templates Jinja2. O sistema usa React
> desde a migração; o Apêndice A já registra isso, a §3.2 não. Ver
> [07](07-backlog-specs.md#divergências-entre-o-texto-do-tcc-e-o-código).

## Endpoints

Todos sob o prefixo `/api`, registrados pelo blueprint `api`.

| Método | Rota | Retorno |
|---|---|---|
| GET | `/api/config` | `{tickers: [...], alphas: [...]}` — padrões da plataforma |
| GET | `/api/models` | `["caviar", "egarch", ...]` — nomes registrados, ordenados |
| GET | `/api/backtests` | `["basileia", "christoffersen", ...]` |
| GET | `/api/results` | `[{id, ticker, created_at}]` — runs salvos, mais recentes primeiro |
| GET | `/api/results/<id>` | `{config: {...}, ranking: [...]}` — payload completo, 404 se não existe |
| GET | `/api/results/<id>/download.csv` | ranking como CSV, `Content-Disposition: attachment` |
| GET | `/api/results/<id>/download.json` | payload completo como JSON, indentado |

`/api/models` e `/api/backtests` leem os registries, então **um modelo novo aparece na API
sem alteração nenhuma aqui** — é o RNF-01 em ação.

### Formato de `ranking`

Uma linha por par `(modelo, alpha)`, serializada de `ExperimentResult.ranking_table()`:

```json
{
  "model": "garch_1_1",
  "alpha": 0.05,
  "error": null,
  "kupiec_passed": false,
  "kupiec_p_value": 0.0000123,
  "christoffersen_passed": true,
  "christoffersen_p_value": 0.6964
}
```

As colunas `<teste>_passed` e `<teste>_p_value` existem para cada teste executado. Quando
o par falhou, `error` traz a mensagem e as colunas de teste ficam ausentes.

> Note que o ranking **não carrega a série de VaR nem as violações** — só o veredito
> agregado. É a razão pela qual não há como desenhar o gráfico de VaR a partir de um run
> salvo hoje. Ver [07](07-backlog-specs.md#rf-18--visualização-gráfica).

## A API é somente leitura

**Não existe nenhum endpoint `POST`.** A única forma de gerar um resultado é a CLI:

```bash
varlab run --ticker PETR4.SA --start 2015-01-01 --end 2024-12-31 \
    --model parametric --model garch_1_1 --model lstm \
    --backtest kupiec --backtest christoffersen --backtest dq --backtest basileia \
    --save
```

A web apenas consulta o que foi persistido. É a lacuna funcional mais relevante do sistema
(RF-17), detalhada em [07](07-backlog-specs.md#rf-17--executar-experimento-pela-interface).

## CORS

`flask_cors` liberado em `/api/*` para qualquer origem — adequado a desenvolvimento, com o
Vite em `:5173` e o Flask em `:5000`. **Deve ser restringido antes de qualquer exposição
pública.**

## Configuração

`varlab/web/config.py`, selecionada por `VARLAB_ENV` (`development` | `testing` |
`production`):

| Chave | Valor |
|---|---|
| `SECRET_KEY` | de `VARLAB_SECRET_KEY`, com padrão inseguro em dev |
| `DEFAULT_TICKERS` | `^BVSP`, `PETR4.SA`, `VALE3.SA`, `ITUB4.SA` |
| `DEFAULT_ALPHAS` | `0.05`, `0.01` |

---

## Frontend

SPA React 19 + Vite. `frontend/src/api/client.js` é o **único** arquivo que fala com o
Flask — todo o resto do frontend desconhece a existência da API.

### Rotas

| Rota | Página | Estado |
|---|---|---|
| `/` | `Dashboard` | lista tickers e modelos registrados |
| `/results` | `ResultsList` | lista runs salvos |
| `/results/:runId` | `ResultDetail` | tabela de ranking + links de download |
| `*` | `NotFound` | — |

### Infra de UI já existente

`ErrorBoundary`, `LoadingBar` com store de requisições em voo, `ApiOfflineBanner` com
detecção de API inalcançável, `Skeleton` para carregamento, `ThemeToggle`.

O `client.js` distingue corretamente falha de rede (o `fetch` rejeita) de erro HTTP (o
`fetch` resolve com `res.ok === false`) — o primeiro marca a API como offline, o segundo
não.

### Proxy em desenvolvimento

`vite.config.js` encaminha `/api` para `http://127.0.0.1:5000`. Em produção o
`VITE_API_BASE_URL` fica vazio e as chamadas são de mesma origem.

### Plotly

`plotly.js` e `react-plotly.js` estão em `package.json` mas **não são importados em lugar
nenhum**. Ver [07 — RF-18](07-backlog-specs.md#rf-18--visualização-gráfica).
