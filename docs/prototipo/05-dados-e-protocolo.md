# 05 — Dados e protocolo experimental

## Fonte de dados

`YFinanceProvider` (`varlab/data/providers/yfinance_provider.py`) — Yahoo Finance via
`yfinance`, com `auto_adjust=True`, que já entrega preços ajustados a splits, agrupamentos
e dividendos. Retorna apenas a coluna `close`, indexada por data.

Trocar de fonte significa implementar `DataProvider.fetch(ticker, start, end) -> DataFrame`
com, no mínimo, a coluna `close`. Nenhum modelo conhece o provider.

Ticker sem dados no período levanta `ValueError` — falha explícita, não série vazia.

### Ativos do experimento comparativo

| Ticker | Ativo | Papel no experimento |
|---|---|---|
| `^BVSP` | Ibovespa | mercado agregado |
| `PETR4.SA` | Petrobras PN | energia |
| `VALE3.SA` | Vale ON | mineração |
| `ITUB4.SA` | Itaú Unibanco PN | financeiro |

Configurados em `BaseConfig.DEFAULT_TICKERS` e expostos por `GET /api/config`. Os três
setores são os de maior peso e liquidez na B3.

### Período

**Janeiro/2015 a dezembro/2024** — dez anos, escolhidos por atravessarem múltiplos regimes
de volatilidade: recessão de 2015–2016, instabilidade política de 2017–2018, choque da
COVID-19 em 2020 e ciclo de alta de juros de 2021–2023.

O período não está fixado em código: é argumento de `--start` / `--end`.

## Limpeza e transformação

`varlab/data/preprocessing.py`:

1. `clean_prices` — descarta linhas com `close <= 0` ou nulo, que quebrariam o logaritmo.
2. `log_returns` — `log(P_t / P_{t-1})`, com o primeiro NaN removido.

⚠️ **Lacuna conhecida (RF-02).** O TCC §3.5 promete "detecção de valores ausentes,
verificação de retornos aberrantes e comparação com fontes alternativas". Só a primeira
existe: não há detecção de outliers nem verificação cruzada de fontes. Ver
[07](07-backlog-specs.md).

## Cache

`varlab/data/cache.py` grava parquet em `~/.varlab/cache/`.

⚠️ **Código morto.** Nada no sistema chama `load_cached` nem `save_cache` — toda execução
rebaixa os dados. Ver [07](07-backlog-specs.md).

---

## Protocolo experimental

### Parâmetros padrão

| Parâmetro | Padrão | Onde muda |
|---|---|---|
| Níveis de confiança | 95% e 99% (`alpha` 0.05 e 0.01), simultâneos | `--alpha` (repetível) |
| Horizonte | 1 dia útil | ❌ não exposto na CLI |
| Janela de treino | 252 dias úteis (1 ano) | `--train-window` |
| Cadência de reestimação | 252 dias úteis | ❌ constante de código |

Os dois níveis são calculados na mesma execução, de propósito: a comparação regulatória
entre 95% e 99% é um resultado do trabalho, não duas execuções separadas.

### Divisão treino / teste

Divisão **única e fixa**, não deslizante:

```
train = returns[:252]      # primeiros 252 dias úteis do período
test  = returns[252:]      # todo o restante
```

Se o período não excede a janela de treino, o runner levanta `ValueError` antes de
qualquer estimação — não haveria dado de teste.

Sobre 2015–2024, isso significa ~1 ano de treino e ~9 anos de teste. É uma janela de
treino curta para um teste longo, e é o que torna a reestimação periódica essencial.

### Reestimação com janela expansiva

Todos os modelos condicionais (GARCH, EGARCH, CAViaR, LSTM, GRU, GARCHNet) percorrem o
teste em blocos de 252 dias úteis e, ao virar cada bloco, reajustam usando **todo o dado
observado até ali** — treino mais teste já percorrido.

O reajuste difere por família:

| Família | Ao virar o bloco |
|---|---|
| GARCH/EGARCH | reestimação completa por máxima verossimilhança |
| CAViaR | reotimização completa, 10 reinícios |
| Redes neurais | continuação do treino em *warm start*, 10 épocas |

### Ausência de look-ahead (RNF-06)

Nenhuma estimativa usa informação posterior à sua data:

- os parâmetros de um bloco vêm de dados anteriores ao início do bloco;
- as previsões dentro do bloco são de 1 passo à frente;
- a seleção de hiperparâmetros usa validação sobre o **fim da janela de treino**, nunca o
  período de teste.

É o requisito mais fácil de violar acidentalmente ao mexer nesta camada, e o que menos
aparece nos resultados quando violado — um modelo com vazamento simplesmente parece bom.

### Alinhamento antes do backtesting

O runner realinha antes de testar:

```python
aligned_returns = test_returns.reindex(estimate.var_series.index).dropna()
var_series = estimate.var_series.reindex(aligned_returns.index)
```

Garante que retorno e VaR estão na mesma data, mesmo que um modelo devolva série mais
curta.

### Isolamento de falhas (RNF-07)

Erro no `fit` marca todos os alphas daquele modelo; erro em `estimate_var` ou no
backtesting marca apenas o par `(modelo, alpha)`. O experimento sempre termina, com o erro
registrado em `ModelRunResult.error` e visível na coluna `error` do ranking.

---

## Custo computacional

Um experimento com os 9 modelos, 1 ticker, período 2015–2024: **20 a 60 minutos em CPU**.

O custo concentra-se nos modelos de ML, e por um motivo estrutural: o treino é por alpha
(2×) e o grid search tem 4 combinações, então uma execução completa de LSTM, GRU e
GARCHNet significa 24 rodadas de treino, mais os reajustes de warm start por bloco.

> **TensorFlow não usa GPU no Windows nativo** a partir da versão 2.11 — exige WSL2 ou o
> plugin DirectML. Para rodar vários tickers, prefira máquina com GPU acessível
> (Linux/WSL2) ou execute um ticker por vez.

Consequência de projeto: **experimento completo não cabe em requisição HTTP síncrona**.
Ver [07](07-backlog-specs.md#rf-17--executar-experimento-pela-interface).

---

## Reprodutibilidade (RNF-05)

Modelos tradicionais, GARCH/EGARCH e CAViaR são determinísticos. **As redes neurais não
são** — a inicialização de pesos do Keras não tem semente fixa, então LSTM, GRU e GARCHNet
produzem números diferentes a cada execução.

O padrão qualitativo se mantém entre execuções, mas os p-valores exatos publicados no TCC
§4.3 não são reproduzíveis hoje. Corrigir isso é pré-requisito para a Etapa 6: os números
do ranking final precisam ser verificáveis. Ver
[07](07-backlog-specs.md#rnf-05--reprodutibilidade-das-redes-neurais).

---

## Verificação cruzada com R

`tools/garch_rcheck/` valida a estimação GARCH contra implementação independente:

```bash
python tools/garch_rcheck/export_for_r.py --ticker PETR4.SA --start 2015-01-01 --end 2024-12-31
Rscript tools/garch_rcheck/rugarch_check.R
```

O script Python exporta a janela de treino (`train_returns.csv`) e os parâmetros estimados
pelo `arch` (`python_arch_params.json`); o script R ajusta a **mesma especificação** —
`sGARCH`/`eGARCH`, média zero, inovações normais — via `rugarch` e imprime coeficientes,
log-verossimilhança e flag de convergência.

Resultado obtido em PETR4.SA, 252 dias (TCC §4.2):

| Modelo | log-verossimilhança Python (`arch`) | R (`rugarch`) | Divergência |
|---|---|---|---|
| GARCH(1,1) | 473,62 | 471,81 | 0,4% |
| EGARCH | 481,60 | 475,17 | 1,4% |

Divergências dessa ordem são compatíveis com diferenças de otimizador sobre uma superfície
de verossimilhança com crista quase plana entre os parâmetros — fenômeno conhecido na
estimação de modelos GARCH.

⚠️ É um procedimento **manual e fora da suíte** (`pytest` não requer R). Os diagnósticos
automatizáveis sem R — convergência e comportamento dos resíduos padronizados — estão em
`tests/models/test_garch_diagnostics.py`.
