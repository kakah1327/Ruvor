"""Constantes da camada 3, num modulo so.

A spec as chama de `RiskConfig.*`; o que vale e o nome do modulo:
`from apps.risk import config; config.DEFAULT_SEED`. `RiskConfig` ja e o nome da
`AppConfig` em `apps.py`, e duas coisas com o mesmo nome no mesmo app seria confusao.
"""

from __future__ import annotations

DEFAULT_SEED = 42
TRAIN_WINDOW_DAYS = 252

# 503 = train_window + 251. A conta esta na spec: P precos dao P-1 retornos, menos 252 de
# treino, e a Basileia exige 250 observacoes de teste. P-253 >= 250 implica P >= 503.
MIN_SESSIONS = 503

# Float, nao Decimal: e o que o motor consome -- em `-norm.ppf(alpha)`, em
# `np.quantile(..., alpha)`, na perda pinball e como chave de cache do `_quantile_nn`.
# A conversao para a coluna `Decimal(6,4)` acontece na escrita.
ALPHAS = (0.05, 0.01)

BACKTESTS = ("kupiec", "christoffersen", "dq", "basileia")

# O laboratorio (M2.4, RF-03): o periodo de teste da decada se corta em trechos de
# `LAB_YEAR_DAYS` retornos a partir da posicao 0; trecho com menos de `LAB_YEAR_MIN_JUDGED`
# nao e julgado, e so os niveis de `LAB_JUDGED_ALPHAS` tem veredito por trecho.
LAB_YEAR_DAYS = 252  # = REFIT_FREQUENCY_DAYS dos nove modelos (spec, Problema)
LAB_YEAR_MIN_JUDGED = 126  # meio ano de teste
LAB_JUDGED_ALPHAS = (0.05,)  # veredito por ano so a 95% (portao, 2026-10-03)
