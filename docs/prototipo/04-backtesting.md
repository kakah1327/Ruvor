# 04 — Backtesting

4 instrumentos de validação registrados. Todos implementam `BacktestTest` e recebem
apenas `(returns, var_series, alpha)` — nunca um modelo. É isso que permite validar
qualquer modelo, presente ou futuro, sem tocar nesta camada.

| Nome no registry | Classe | Hipótese nula | Distribuição |
|---|---|---|---|
| `kupiec` | `KupiecTest` | taxa de violação = alpha | qui-quadrado(1) |
| `christoffersen` | `ChristoffersenTest` | violações independentes no tempo | qui-quadrado(1) |
| `dq` | `DynamicQuantileTest` | coeficientes conjuntamente nulos | qui-quadrado(6) |
| `basileia` | `BasileiaZonesTest` | — (classificação regulatória) | binomial |

## Definição de violação

Comum a todos:

```python
violacao = returns < -var_series
```

Coerente com a convenção de `var_series` positiva ([02](02-arquitetura.md#contratos)).

## Nível de significância

`SIGNIFICANCE = 0.05` nos três testes estatísticos. `passed = p_value > 0.05`.

Atenção à leitura: **`passed` significa "não rejeitamos o modelo"**, não "o modelo é bom".
Um p-valor alto pode vir de baixo poder estatístico tanto quanto de boa calibração.

---

## `kupiec` — Proportion of Failures

Kupiec (1995). Testa se a frequência observada de violações é compatível com `alpha`, por
razão de verossimilhanças. Com `n` observações e `x` violações:

```
LR_uc = -2 * ( logL(alpha) - logL(x/n) )
logL(p) = (n-x)*log(1-p) + x*log(p)
```

Implementado com `scipy.special.xlogy`, que trata `0*log(0) = 0` — o caso de zero
violações não produz `NaN`.

A função `unconditional_coverage_lr()` é reaproveitada pelo Christoffersen; é o único
acoplamento entre dois testes, e é deliberado.

`details`: `violations`, `expected` (`n*alpha`), `n_obs`, `violation_rate`.

---

## `christoffersen` — independência

Christoffersen (1998). Verifica se as violações são independentes no tempo (não
clusterizadas), por cadeia de Markov de 1ª ordem sobre o indicador de violação.

Contagens de transição `n00`, `n01`, `n10`, `n11`; probabilidades condicionais
`pi_01 = n01/(n00+n01)` e `pi_11 = n11/(n10+n11)`, contra a incondicional `pi`:

```
LR_ind = -2 * ( logL(pi) - logL(pi_01, pi_11) )
```

**Escopo do veredito:** `statistic`, `p_value` e `passed` referem-se **apenas à
independência**. A cobertura condicional conjunta de Christoffersen
(`LR_cc = LR_uc + LR_ind`, com 2 graus de liberdade) é calculada e publicada em `details`
(`lr_conditional_coverage`, `p_value_conditional_coverage`), mas **não** entra em
`passed`.

Isso é intencional — o teste de cobertura incondicional já é o `kupiec`, e somar os dois
no veredito duplicaria o mesmo sinal. Vale conhecer a distinção ao ler os resultados: o
TCC se refere a este teste como "cobertura condicional", enquanto o campo `passed` reporta
independência.

`details`: `n00`, `n01`, `n10`, `n11`, `lr_conditional_coverage`,
`p_value_conditional_coverage`.

---

## `dq` — Dynamic Quantile

Engle & Manganelli (2004). Regride o indicador de violação centrado sobre suas defasagens
e o VaR contemporâneo, e testa se os coeficientes são conjuntamente nulos (Wald). Captura
cobertura e dependência temporal em um único teste.

```
Hit_t = 1{r_t < -VaR_t} - alpha
Hit_t ~ const + Hit_{t-1..t-4} + VaR_t
DQ = (beta' X'X beta) / (alpha * (1 - alpha))    ~ qui-quadrado(6)
```

`N_LAGS = 4`, portanto 6 regressores (constante + 4 defasagens + VaR contemporâneo).
Estimação por `numpy.linalg.lstsq`.

**Pré-condição:** exige `n - N_LAGS >= n_regressors + 5`, senão levanta `ValueError`. O
runner isola essa falha no par `(modelo, alpha)` afetado.

`details`: `n_lags`, `beta`.

> **Sensibilidade em amostras longas.** O DQ rejeita para praticamente todos os modelos no
> período de 10 anos (TCC §4.4). É resultado esperado, não defeito de implementação: o
> teste tem poder estatístico alto e, em amostra longa, detecta desvios pequenos. Ao
> comparar modelos, o DQ discrimina pouco em séries dessa extensão.

---

## `basileia` — zonas regulatórias

Basel Committee (2004). Não é teste de hipótese: classifica o modelo em faixa regulatória
pela probabilidade binomial acumulada de observar `x` violações.

**Janela fixa de `WINDOW_DAYS = 250` dias úteis**, tomada do **final** da série — o
período mínimo de backtesting exigido por Basileia II. Se o teste tiver menos de 250 dias,
levanta `ValueError`.

| Zona | Critério (`cum_prob = binom.cdf(x, 250, alpha)`) | `passed` |
|---|---|---|
| verde | `< 0.95` | ✅ |
| amarela | `< 0.9999` | ✅ |
| vermelha | caso contrário | ❌ |

`statistic` é a contagem de violações; `p_value` é `1 - cum_prob`.

> **Nota sobre a faixa verde/amarela/vermelha.** O Acordo enuncia as zonas em contagens
> absolutas a 99% (verde ate 4, amarela 5–9, vermelha 10+). A implementação usa os limiares
> de probabilidade acumulada equivalentes, o que generaliza a classificação para `alpha`
> arbitrário — a 95% a contagem correspondente é naturalmente maior. Ler as zonas a 95%
> como se fossem os cortes regulatórios de 99% seria um erro de interpretação.

`details`: `zone`, `violations`, `expected`, `window_days`, `cum_prob`.

---

## Validação da própria camada

`tests/backtesting/test_formulas.py` constrói séries com número de violações **conhecido
de antemão** e confere as estatísticas contra cálculo de referência independente —
inclusive uma reimplementação do LR de Kupiec com `math.log` puro, para não validar a
função contra ela mesma.

`tests/backtesting/test_all_backtests.py` é parametrizado sobre o registry: qualquer teste
novo é automaticamente exercitado pela interface.

---

## Como adicionar um teste

```python
from varlab.backtesting.base import BacktestTest, BacktestResult
from varlab.backtesting.registry import register_backtest

@register_backtest("meu_teste")
class MeuTeste(BacktestTest):
    def run(self, returns, var_series, alpha):
        return BacktestResult(test_name=self.name, statistic=..., p_value=...,
                              passed=..., details={})
```

Passa a valer para `--backtest meu_teste`, para a API e para a suíte parametrizada. O
carregador ignora `base.py` e `registry.py` ao varrer o pacote.
