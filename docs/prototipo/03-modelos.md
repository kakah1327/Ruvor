# 03 — Modelos de VaR

9 modelos registrados, em 3 categorias. Todos implementam `VaRModel`
([contrato](02-arquitetura.md#contratos)) e produzem `var_series` positiva alinhada ao
índice do período de teste.

| Nome no registry | Classe | Categoria | Dinâmico | Depende de |
|---|---|---|---|---|
| `parametric` | `ParametricVaR` | traditional | não | scipy |
| `historical` | `HistoricalVaR` | traditional | não | — |
| `monte_carlo` | `MonteCarloVaR` | traditional | não | numpy |
| `garch_1_1` | `Garch11VaR` | garch | sim | arch |
| `egarch` | `EgarchVaR` | garch | sim | arch |
| `lstm` | `LstmVaR` | ml | sim | tensorflow |
| `gru` | `GruVaR` | ml | sim | tensorflow |
| `caviar` | `CaviarVaR` | ml | sim | scipy |
| `garchnet` | `GarchNetVaR` | ml | sim | tensorflow + arch |

"Dinâmico" = o VaR varia ao longo do período de teste. Os três tradicionais produzem um
**valor constante** replicado por toda a série.

---

## Tradicionais

Estimam um único valor a partir da janela de treino e o repetem. São a linha de base
contra a qual os demais são comparados, e seu fracasso no teste de Kupiec em janelas
longas é resultado esperado, não defeito: assumem variância constante por dez anos.

### `parametric` — variância-covariância

Assume retornos normais. Com `mu` e `sigma` (ddof=1) da janela de treino:

```
VaR = -(mu*h + z_alpha * sigma*sqrt(h))        z_alpha = norm.ppf(alpha)
```

### `historical` — simulação histórica

Quantil empírico dos retornos de treino, sem suposição distribucional:

```
VaR = -quantile(train, alpha) * sqrt(h)
```

### `monte_carlo` — simulação de Monte Carlo

Ajusta `N(mu, sigma^2)` ao treino, simula cenários e toma o quantil empírico das perdas
simuladas.

| Parâmetro | Padrão |
|---|---|
| `n_simulations` | 100 000 |
| `random_state` | 42 |

Converge para o `parametric` por construção (simula da mesma normal) — é o que
`tests/models/test_traditional_reference.py` verifica, com tolerância estatística. A
diferença entre os dois é metodológica, não numérica: o Monte Carlo é o veículo para
distribuições sem forma fechada.

**Escalonamento de horizonte:** os três usam a regra da raiz do tempo (`sqrt(h)`). Como o
horizonte padrão da plataforma é 1 dia, ela nunca é exercitada na prática.

---

## Volatilidade condicional

Ambos herdam de `ConditionalVolatilityVaR` (`varlab/models/garch/_conditional.py`), que
concentra toda a lógica; as subclasses só declaram os kwargs da biblioteca `arch`.

```
VaR_t = -z_alpha * sigma_t     sigma_t = previsão 1 passo à frente da vol. condicional
```

| Modelo | Especificação `arch` |
|---|---|
| `garch_1_1` | `vol="GARCH", p=1, q=1` |
| `egarch` | `vol="EGARCH", p=1, o=1, q=1` |

Ambos com média zero (`mean="Zero"`) e inovações normais (`dist="normal"`).

### Escala

Os retornos são multiplicados por `SCALE = 100` antes da estimação e o sigma resultante é
dividido de volta. A `arch` recomenda pontos percentuais por estabilidade numérica.

### Walk-forward com reestimação periódica

`_sigma_path()` percorre o período de teste em blocos de `REFIT_FREQUENCY_DAYS = 252`:

1. Fixa os parâmetros correntes sobre a série completa até o fim do bloco (`model.fix`).
2. Prevê sigma um passo à frente para cada dia do bloco.
3. Ao virar o bloco, **reestima** os parâmetros com toda a informação observada até ali
   (janela expansiva: treino + teste já percorrido).

Não há look-ahead: cada previsão usa apenas parâmetros e retornos anteriores à data.

### Piso de segurança em sigma

`sigma_floor_ = std(train) * 0.1`, aplicado a cada sigma previsto.

Existe por um motivo concreto, documentado no TCC (§4.2): o EGARCH, ao propagar
parâmetros fixos por anos sem reestimação, entra em realimentação — o resíduo padronizado
cresce, os termos assimétricos reagem com mais força, e a variância condicional colapsa
numericamente a zero. O GARCH(1,1) não sofre disso, porque sua recursão tem piso
estrutural na constante `omega`.

A reestimação periódica resolve o caso geral. O piso cobre o resíduo: o **primeiro** bloco
é ajustado apenas com os 252 dias iniciais — a janela mais curta e a única sem alternativa
de usar mais dados — e ainda pode colapsar antes do primeiro reajuste.

### `full_sigma_series()`

Serviço para modelos híbridos: devolve sigma cobrindo treino **e** teste — em amostra no
treino (`result_.conditional_volatility`), walk-forward daí em diante. Usado pelo
GARCHNet.

---

## Machine Learning

### Diferença conceitual em relação ao GARCH

O GARCH prevê a **variância** e assume normalidade para converter em quantil. LSTM, GRU e
o componente neural do GARCHNet preveem **o quantil diretamente**, minimizando a pinball
loss — sem qualquer suposição distribucional:

```
L(y, y_hat) = mean( max( alpha*(y - y_hat), (alpha - 1)*(y - y_hat) ) )
```

Consequência de projeto: **a rede treinada para alpha=5% é uma rede diferente da treinada
para alpha=1%**. Não existe "um modelo" que atenda os dois níveis.

### Base comum: `QuantileNeuralVaR`

`varlab/models/ml/_quantile_nn.py`. Compartilhada por `lstm`, `gru` e `garchnet`. As
subclasses implementam apenas `_features()` e `_build_model()`.

**Fit preguiçoso por alpha.** `fit()` só guarda os retornos de treino. O treino real —
grid search completo mais ajuste final — dispara no primeiro `estimate_var()` de cada
alpha, e fica em cache para não repetir.

**Janelamento.** `WINDOW = 20` dias úteis. A janela `i` prevê o dia `WINDOW + i`.

**Grid search.**

| Hiperparâmetro | Valores |
|---|---|
| `units` | 16, 32 |
| `n_layers` | 1, 2 |

Seleção por menor `val_loss`, com os últimos 15% da janela de treino como validação
(`VAL_FRACTION = 0.15`) e early stopping (`PATIENCE = 5`, `SEARCH_EPOCHS = 20`). A
configuração vencedora é então reajustada sobre a janela de treino inteira.

Fixos, fora do grid: `LEARNING_RATE = 0.001`, `BATCH_SIZE = 32`.

> **Desvio consciente do TCC.** A seção 3.2 previa grid sobre 4 dimensões, incluindo taxa
> de aprendizado e batch size. Reduzido a 2 por custo: o treino é por alpha e por bloco de
> reestimação, então cada combinação custa uma rodada inteira. Já registrado no §4.3 e na
> Matriz de Validação.

**Walk-forward.** Percorre o teste em blocos de `REFIT_FREQUENCY_DAYS = 252`: prevê o
bloco com forward pass (barato), e ao virar o bloco continua o treino em *warm start*
(`REFIT_EPOCHS = 10`) com tudo observado até ali. Mesmo espírito da janela expansiva do
GARCH, sem o custo de retreinar do zero.

**Saída.** `var_series = max(-predicted, 0) * sqrt(h)` — a rede prevê o quantil do retorno
(negativo); a inversão de sinal e o corte em zero garantem a convenção de VaR positivo.

**Contrato de `_features(returns)`:** `returns` sempre começa no início do período de
treino — ou é exatamente `train_returns_`, ou ele concatenado com teste já observado. Isso
permite que subclasses alinhem features que dependem de estado acumulado sem se preocupar
com a fronteira treino/teste.

### `lstm` e `gru`

Features idênticas: `[retorno, |retorno|]`. Diferem apenas na célula recorrente
(`keras.layers.LSTM` vs `keras.layers.GRU`), empilhada `n_layers` vezes, seguida de
`Dense(1)`.

O GRU tem menos parâmetros e treino mais barato, com desempenho competitivo em séries
curtas (Cho et al., 2014).

### `garchnet` — híbrido GARCH + LSTM

Buczynski & Chlebus (2024). Ajusta internamente um `Garch11VaR` sobre a mesma janela de
treino e usa a volatilidade condicional como **terceira feature**:

```
features = [retorno, |retorno|, sigma_garch]
```

Arquitetura idêntica à `lstm`. A rede aprende uma correção não-linear sobre a estimativa
de volatilidade do GARCH.

### `caviar` — regressão quantílica autorregressiva

Engle & Manganelli (2004), especificação *Symmetric Absolute Value*:

```
VaR_t = b0 + b1*VaR_{t-1} + b2*|r_{t-1}|
```

Único modelo de ML sem rede neural. Ajustado por `scipy.optimize.minimize`
(Nelder-Mead) minimizando a pinball loss, com `N_RESTARTS = 10` reinícios — o problema é
não-convexo, como no artigo original.

Reinícios que exploram regiões instáveis da recursão (por exemplo `b1 > 1`) estouram em
overflow e produzem loss não finita; são **descartados**, nunca escolhidos como melhor,
mesmo se forem o primeiro. Se todos os 10 falharem, o modelo levanta `RuntimeError`.

Inicialização: `f0 = -quantile(train, alpha)`; reestimação a cada 252 dias com janela
expansiva, como os demais.

> **Desvio consciente do TCC.** A seção 3.2 previa `statsmodels.QuantReg`. Não é
> aplicável: o termo `VaR_{t-1}` não é variável observada, é a própria saída do modelo, e
> regressão quantílica estática não modela recursão. Já corrigido no §4.3 e na Matriz de
> Validação; a §3.2 permanece desatualizada.

---

## Reprodutibilidade

| Modelo | Determinístico | Fonte de aleatoriedade |
|---|---|---|
| `parametric`, `historical` | ✅ | nenhuma |
| `monte_carlo` | ✅ | `random_state=42` fixo |
| `garch_1_1`, `egarch` | ✅ | otimizador determinístico |
| `caviar` | ✅ | `seed = int(alpha*10000)`, e `+ pos` nos reajustes |
| `lstm`, `gru`, `garchnet` | ❌ | inicialização de pesos do Keras |

> **Correção ao TCC.** O §4.3 e a Matriz de Validação afirmam que "os reinícios aleatórios
> do CAViaR não usam semente fixa". Não procede: `caviar.py` deriva a semente de forma
> determinística a partir de alpha. Apenas as redes neurais são não reprodutíveis.

Ver [07 — RNF-05](07-backlog-specs.md).

---

## Como adicionar um modelo

Um arquivo em `varlab/models/{traditional,garch,ml}/`:

```python
from varlab.models.base import VaRModel, VaREstimate, ModelCategory
from varlab.models.registry import register_model

@register_model("meu_modelo")
class MeuModelo(VaRModel):
    category = ModelCategory.GARCH

    def fit(self, returns):
        self.algo_ = ...
        return self

    def estimate_var(self, returns, alpha=0.05, horizon=1):
        var_series = ...  # positiva, indexada por returns.index
        return VaREstimate(var_series=var_series, alpha=alpha,
                           horizon=horizon, model_name=self.name)
```

Nenhum outro arquivo muda. O modelo passa a aparecer na CLI (`--model meu_modelo`), na
API, no frontend, e é coberto automaticamente pelo teste parametrizado.

Se o modelo depender de biblioteca fora dos extras instalados, ele some do registry em
silêncio — comportamento intencional, ver [02](02-arquitetura.md#carga-dos-módulos).
