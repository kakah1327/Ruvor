# 02 — Arquitetura

## Princípio central

A modularidade do sistema não vem da separação em pastas, vem de **dois registries com
auto-registro por decorator**. Um modelo ou um teste de backtesting se declara, e todo o
resto do sistema passa a enxergá-lo — CLI, API, frontend e suíte de testes — sem que
nenhum desses módulos seja alterado.

Isso é o que sustenta o RNF-01 e o RNF-04, e é a decisão de projeto mais importante aqui.

## Camadas

```
varlab/
├── data/           coleta e limpeza          → produz pd.Series de log-retornos
├── models/         estimação de VaR          → consome retornos, produz VaREstimate
├── backtesting/    validação estatística     → consome (retornos, var_series, alpha)
├── experiments/    orquestração              → liga as três camadas acima
├── storage/        persistência opcional     → serializa ExperimentResult
├── web/            API JSON (Flask)          → expõe registries e resultados salvos
└── cli.py          entrada headless

frontend/           SPA React (Vite) — consome a API, não conhece o resto
```

A dependência é sempre para baixo. `backtesting/` não importa `models/`; `models/` não
importa `web/`; `experiments/` não importa Flask. Os três consumidores da camada de
orquestração — CLI, API e testes — são intercambiáveis.

## Contratos

### `VaRModel` — `varlab/models/base.py`

```python
class VaRModel(ABC):
    name: str                # preenchido pelo decorator de registro
    category: ModelCategory  # TRADITIONAL | GARCH | ML

    def fit(self, returns: pd.Series) -> "VaRModel": ...
    def estimate_var(self, returns, alpha=0.05, horizon=1) -> VaREstimate: ...
```

`VaREstimate` carrega `var_series`, `alpha`, `horizon` e `model_name`.

**Convenção de sinal:** `var_series` é sempre **positiva** — representa a magnitude da
perda. Uma violação é `returns < -var_series`. Todo modelo deve respeitar isso; a suíte
parametrizada verifica `(var_series >= 0).all()`.

**Semântica do argumento `returns` em `estimate_var`:** é o período de **teste**, e serve
para o modelo saber *para quais datas* produzir estimativa. Modelos estáticos usam apenas
`returns.index`; modelos condicionais usam também os valores, para propagar estado
walk-forward. A série retornada deve estar alinhada a `returns.index`.

### `BacktestTest` — `varlab/backtesting/base.py`

```python
class BacktestTest(ABC):
    name: str
    def run(self, returns, var_series, alpha) -> BacktestResult: ...
```

`BacktestResult` carrega `test_name`, `statistic`, `p_value`, `passed` e um dicionário
`details` livre, onde cada teste publica o que for próprio dele.

O contrato recebe apenas séries — é o que garante que um teste de backtesting nunca
conheça um modelo, e que um modelo novo seja validado sem tocar nesta camada.

## Registries

Ambos seguem o mesmo padrão (`varlab/models/registry.py`, `varlab/backtesting/registry.py`):

```python
@register_model("garch_1_1")
class Garch11VaR(ConditionalVolatilityVaR):
    category = ModelCategory.GARCH
```

O decorator preenche `cls.name` e indexa a classe. Nomes duplicados levantam `ValueError`
no import — colisão é erro de programação, não é silenciada.

### Carga dos módulos

`load_all_model_modules()` varre `models/traditional`, `models/garch` e `models/ml` com
`pkgutil` e importa cada submódulo, disparando os decorators. É chamada uma vez, na
inicialização (app factory do Flask, comando da CLI, topo dos testes).

**`ImportError` é engolido de propósito.** Sem TensorFlow instalado, os módulos de
`models/ml` falham no import e simplesmente não entram no registry; o resto do sistema
continua funcional. É o que permite os grupos opcionais de dependência
(`pip install -e ".[traditional]"` sem arrastar TensorFlow).

O efeito colateral a conhecer: **um erro de sintaxe ou um import quebrado dentro de um
modelo faz esse modelo desaparecer em silêncio**, sem mensagem. Se um modelo não aparece
em `list_models()`, importe o módulo diretamente para ver a exceção real.

## Fluxo de execução de um experimento

`varlab/experiments/runner.py`:

1. `fetch_returns(provider, ticker, start, end)` → série de log-retornos.
2. Valida que o período excede `train_window_days`, senão erro — não haveria teste.
3. Divide: `train = returns[:252]`, `test = returns[252:]`. Split fixo, não deslizante.
4. Para cada modelo: `get_model(nome)().fit(train)` — **um fit por modelo**, reaproveitado
   entre os níveis de confiança.
5. Para cada `alpha`: `estimate_var(test, alpha, horizon)`.
6. Realinha `test_returns` e `var_series` pelo índice da estimativa, descartando NaN.
7. Roda cada teste de backtesting configurado sobre o par alinhado.
8. Agrega em `ExperimentResult`, que expõe `ranking_table()` — 1 linha por
   `(modelo, alpha)`, 1 par de colunas `_passed` / `_p_value` por teste.

Falhas são isoladas em dois níveis: erro no `fit` marca todos os alphas daquele modelo;
erro em `estimate_var` ou no backtesting marca só aquele par `(modelo, alpha)`. O
experimento sempre termina, e o erro fica registrado no `ModelRunResult`.

> **Nota sobre o passo 4:** os modelos de ML têm treino *preguiçoso por alpha* — o `fit`
> só guarda os dados, e o treino real acontece dentro do primeiro `estimate_var` de cada
> alpha. Ver [03 — modelos de ML](03-modelos.md#base-comum-quantileneuralvar).

## Persistência

`ExperimentRunRepository` (ABC) com implementação `SQLiteExperimentRunRepository`.
Banco em `~/.varlab/varlab.db`, tabela única `experiment_runs (id, ticker, created_at,
payload)` — o payload é o JSON de `{config, ranking}`. Schema criado sob demanda.

Trocar de backend significa implementar a interface; nem `web/` nem `cli.py` tocam
SQLAlchemy diretamente.

> Divergência com o TCC: a seção 3.2 afirma que não haveria banco persistente. A
> persistência existe e é usada pela API. Ver [07](07-backlog-specs.md#divergências-entre-o-texto-do-tcc-e-o-código).

## Cache de dados

`varlab/data/cache.py` grava parquet em `~/.varlab/cache/{ticker}_{start}_{end}.parquet`.

⚠️ O módulo está implementado mas **não é chamado** por `fetch_returns` nem pelo
`YFinanceProvider` — hoje toda execução rebaixa os dados da rede. Ver
[07](07-backlog-specs.md).

## Empacotamento

Extras opcionais em `pyproject.toml`, alinhados às etapas:

| Extra | Traz | Necessário para |
|---|---|---|
| `traditional` | numpy, scipy, pandas, yfinance | núcleo — obrigatório |
| `garch` | arch, statsmodels | GARCH, EGARCH, GARCHNet |
| `ml` | tensorflow | LSTM, GRU, GARCHNet |
| `web` | flask, flask-cors, plotly | API |
| `storage` | sqlalchemy | `--save` e endpoints de resultados |
| `dev` | pytest | suíte de testes |

`all` agrega todos. Note que **GARCHNet exige `garch` e `ml` simultaneamente** — ele usa a
volatilidade condicional do GARCH(1,1) como feature.
