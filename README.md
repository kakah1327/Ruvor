# VaR Lab

Plataforma web de modelagem e backtesting de Value at Risk (VaR), comparando métodos
tradicionais, modelos GARCH/EGARCH e algoritmos de Machine Learning (LSTM, GRU, CAViaR,
GARCHNet), com validação via Kupiec, Christoffersen, teste DQ e zonas de Basileia, sobre
ativos da B3.

Projeto de TCC — Faculdade Impacta Tecnologia.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# instale so o que precisar para a etapa em que estiver:
pip install -e ".[traditional,web,dev]"   # Etapa 1 (dados + VaR tradicional)
pip install -e ".[garch]"                 # quando chegar na Etapa 2 (GARCH/EGARCH)
pip install -e ".[ml]"                    # quando chegar na Etapa 3 (LSTM/GRU/CAViaR/GARCHNet)
pip install -e ".[storage]"               # se quiser persistir runs em SQLite

cp .env.example .env
```

## Rodar

O frontend (React) e a API (Flask) rodam como 2 processos separados em dev:

```bash
# terminal 1: API Flask em :5000 (CORS habilitado para o Vite)
varlab web
# equivalente: flask --app varlab.web.app run --debug

# terminal 2: frontend React em :5173 (proxy /api -> :5000, ver frontend/vite.config.js)
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

Para gerar um build de produção (Flask passa a servir o React embutido, 1 processo só):

```bash
cd frontend && npm run build   # gera frontend/dist
cd .. && varlab web            # Flask detecta frontend/dist e serve tudo em :5000
```

Rodar um experimento headless (sem subir nada de web), imprime a tabela de ranking:

```bash
varlab run --ticker PETR4.SA --start 2015-01-01 --end 2024-12-31 \
    --model parametric --model historical --model monte_carlo --model garch_1_1 --model egarch \
    --model lstm --model gru --model caviar --model garchnet \
    --backtest kupiec --backtest christoffersen --backtest dq --backtest basileia \
    --save
```

Por padrao roda em `alpha=0.05` e `alpha=0.01` simultaneamente (95% e 99%, comparacao
regulatoria) e usa uma janela de treino fixa de 252 dias uteis (1 ano) a partir do inicio
do periodo — ambos configuraveis via `--alpha` (repetir a flag) e `--train-window`.

Nao ha uma etapa de treino separada com pesos salvos em disco: cada `varlab run` faz
fit + estimate + backtest de ponta a ponta, e os modelos de ML retreinam do zero a cada
execucao (grid search + reestimacao periodica a cada `REFIT_FREQUENCY_DAYS`, ver
`varlab/models/ml/_quantile_nn.py`). Um experimento com todos os 9 modelos para 1 ticker
no periodo 2015-2024 leva algo entre 20 e 60 min rodando so em CPU — o TensorFlow **nao
usa GPU no Windows nativo** para versoes >= 2.11 (precisa WSL2 ou o plugin DirectML). Para
rodar varios tickers com os modelos de ML, prefira uma maquina com GPU acessivel ao
TensorFlow (Linux/WSL2) ou rode um ticker por vez.

## Testes

```bash
pytest
```

Os testes em `tests/models/test_all_models.py` e `tests/backtesting/test_all_backtests.py`
são **parametrizados sobre o registry** — qualquer modelo ou teste de backtesting novo que
você adicionar já é validado automaticamente, sem escrever teste novo.

## Arquitetura (modular por design)

```
varlab/
├── data/            # coleta e limpeza de dados (yfinance, cache, retornos)
├── models/           # CORAÇÃO da modularidade: interface comum + registry
│   ├── base.py        #   VaRModel ABC
│   ├── registry.py     #   @register_model("nome") auto-registra o modelo
│   ├── traditional/    #   Etapa 1: paramétrico, histórico, Monte Carlo
│   ├── garch/           #   Etapa 2: GARCH(1,1), EGARCH
│   └── ml/               #   Etapa 3: LSTM, GRU, CAViaR, GARCHNet
├── backtesting/      # Etapa 4: Kupiec, Christoffersen, DQ, Basileia — desacoplado dos modelos
├── experiments/       # Etapa 6: orquestra data -> models -> backtesting (usado por web e CLI)
├── storage/            # persistência opcional de runs (SQLite)
├── web/                 # Etapa 5: Flask — API JSON pura (blueprint `api`), sem HTML
└── cli.py                # `varlab web` / `varlab run ...`

frontend/               # Etapa 5: SPA React (Vite) — consome a API, nao conhece nada do resto
├── src/api/client.js     #   unico arquivo que fala com o Flask
├── src/components/        #   Layout, Card, Chip, Badge, ResultsTable
└── src/pages/               #   Dashboard, ResultsList, ResultDetail
```

A API expõe: `GET /api/config`, `/api/models`, `/api/backtests`, `/api/results`,
`/api/results/<id>`, `/api/results/<id>/download.csv|json`. É o único contrato entre
backend e frontend — nenhum dos dois lados conhece detalhes de implementação do outro,
então trocar o frontend de novo (ou adicionar um app mobile, etc.) não exige tocar em
`varlab/models`, `backtesting`, `experiments` ou `storage`.

### Como adicionar um modelo de VaR novo

Crie um arquivo em `varlab/models/traditional/`, `garch/` ou `ml/` (conforme a
categoria) implementando a interface `VaRModel`:

```python
# varlab/models/garch/meu_modelo.py
from varlab.models.base import VaRModel, VaREstimate, ModelCategory
from varlab.models.registry import register_model

@register_model("meu_modelo")
class MeuModelo(VaRModel):
    category = ModelCategory.GARCH

    def fit(self, returns):
        ...  # guarda o que precisar do periodo de treino (ex: media, desvio, retornos)
        return self

    def estimate_var(self, returns, alpha=0.05, horizon=1):
        # `returns` aqui e o periodo de TESTE — usado para saber para quais datas
        # gerar a serie de VaR (modelos estaticos so usam returns.index; modelos
        # rolling/condicionais podem usar os valores tambem).
        ...
        return VaREstimate(var_series=..., alpha=alpha, horizon=horizon, model_name=self.name)
```

Pronto — o modelo passa a aparecer no frontend, no CLI (`--model meu_modelo`) e é
automaticamente coberto pelo teste parametrizado em `tests/models/`. Nenhum outro arquivo
precisa ser alterado.

O mesmo padrão vale para testes de backtesting em `varlab/backtesting/` (decorator
`@register_backtest("nome")`, implementando `BacktestTest`).

## Cronograma do TCC (referência)

Ver `Cronograma_TCC_II.docx` na pasta do TCC. Mapeamento Etapa → módulo:

| Etapa | Conteúdo | Módulo | Status |
|---|---|---|---|
| E1 | Dados + VaR tradicional | `data/`, `models/traditional/` | ✅ implementado (paramétrico, histórico, Monte Carlo) |
| E2 | GARCH/EGARCH | `models/garch/` | ✅ implementado (GARCH(1,1), EGARCH, reestimacao periodica) |
| E3 | LSTM/GRU/CAViaR/GARCHNet | `models/ml/` | ✅ implementado (quantil direto via pinball loss, walk-forward, grid search) |
| E4 | Backtesting | `backtesting/` | ✅ implementado (Kupiec, Christoffersen, DQ, zonas de Basileia) |
| E5 | Interface web | `web/` (API) + `frontend/` (React) | ✅ implementado |
| E6 | Experimento comparativo | `experiments/runner.py` | ✅ implementado (orquestrador pronto) |
