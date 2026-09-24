# D-63 — A semente é fixa, aplicada no início de cada treino, e entra no manifesto

**Status:** aceita · 2026-09-24

## Contexto

Três dos nove modelos — `garchnet`, `lstm` e `gru`, todos sobre
`engine/src/engine/models/ml/_quantile_nn.py` — **não fixavam semente em ponto nenhum**: nem
na inicialização dos pesos, nem no embaralhamento do `fit` do Keras, nem na ordem da busca em
grade. Duas execuções sobre a mesma série davam VaR diferente.

Sem semente não há manifesto possível: a [D-15](D-15-manifesto-de-execucao.md) exige
registrá-la, e um manifesto que não reproduz o número é decoração. A
[D-21](D-21-motor-ml-congelado-ate-etapa-6.md) congela o motor de ML até a Etapa 6 e nomeia
**a semente como a exceção**.

## Decisão

Nasce `engine/src/engine/seeding.py`, com `configure(seed)` e `apply()`. `apply()` usa
`keras.utils.set_random_seed`, que semeia Python, o gerador global legado do NumPy e o
TensorFlow de uma vez.

**O `runner` configura; quem semeia é o treino.** `run_experiment` chama
`seeding.configure(config.seed)` na primeira linha; `_fit_for_alpha` chama `seeding.apply()`
na primeira linha dele. A semente percorre o caminho declarado:

```
compute_risk --seed N  →  config.DEFAULT_SEED (quando omitido)
                       →  ExperimentConfig.seed
                       →  engine.seeding.configure(seed), no runner
                       →  engine.seeding.apply(), no inicio de cada treino
                       →  gold.risk_run.seed grava o valor efetivamente usado
```

A semente **não é injetada no construtor**: três dos nove definem `__init__` próprio e
nenhum aceita `seed` — fazê-los aceitar seria mexer nos construtores, que a D-21 proíbe.

## Consequências

- **Cada (modelo, alpha) é reprodutível isoladamente**, independente da ordem em que os
  alphas foram pedidos ou de quem chamou. Semear no `runner` "antes do `fit`" semearia antes
  de nada acontecer — `QuantileNeuralVaR.fit()` é preguiçoso — e a reprodutibilidade passaria
  a depender de toda a sequência posterior ser idêntica.
- **`apply()` nunca é inerte.** Sem `configure()` prévio, semeia com `DEFAULT_SEED = 42` do
  próprio módulo. É o que faz um teste que chame `get_model(nome)().fit(...)` direto, sem
  `runner`, medir código semeado em vez de ficar verde sobre código não semeado.
- **"Duas execuções" significa duas instâncias novas, nunca duas chamadas na mesma.**
  `_fit_for_alpha` só roda na primeira `estimate_var` de cada alpha; o laço de reajuste roda
  em toda chamada e consome aleatoriedade.
- **O `import tensorflow` fica dentro de `apply()`**, nunca no topo do módulo: `runner.py`
  importa `seeding`, e um import de módulo tornaria o TensorFlow obrigatório para o motor
  inteiro — uma instalação `engine[traditional,garch]` deixaria de importar o runner.
- **Os seis não neurais mantêm as sementes próprias** — `monte_carlo` com `random_state=42`,
  `caviar` derivando de `alpha` e da posição. A coluna `seed` do manifesto é a semente **da
  execução**, a que governa os três neurais; ela não descreve nem substitui as internas dos
  outros.
- Os não neurais usam `np.random.default_rng(...)`, que **não lê** o estado global semeado
  por `set_random_seed` — é por isso que a linha de base numérica continua intacta.
- **A Tabela 1 do TCC foi gerada sem semente fixa** e, para ser reproduzível, precisa ser
  refeita. Está na trilha do TCC, não neste bloco.
- Fixar a semente **não** garante determinismo entre plataformas: o F5 já registrou que a
  linha de base não é portátil. A semente resolve a variação entre execuções na mesma
  máquina, que é o que o manifesto promete.

Origem: [spec M1.4 — Motor de risco](../specs/M1.4-motor-de-risco.md) (RF-01, RF-09).
