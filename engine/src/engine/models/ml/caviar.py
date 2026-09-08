"""CAViaR (Engle & Manganelli, 2004), especificacao Symmetric Absolute Value:
`VaR_t = beta0 + beta1*VaR_{t-1} + beta2*|r_{t-1}|`, ajustado minimizando a pinball loss
via otimizacao numerica (scipy.optimize, com multiplos restarts pois o problema e
nao-convexo -- mesma pratica usada no artigo original). `statsmodels.QuantReg` NAO
suporta essa especificacao: o termo recursivo VaR_{t-1} nao e uma variavel observada, e a
propria saida do modelo, o que QuantReg (regressao quantilica estatica/linear) nao modela.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from engine.models.base import ModelCategory, VaREstimate, VaRModel
from engine.models.registry import register_model

REFIT_FREQUENCY_DAYS = 252  # mesma cadencia do GARCH (Etapa 2)
N_RESTARTS = 10


def _propagate(
    beta: np.ndarray, returns: np.ndarray, f0: float, r0: float
) -> np.ndarray:
    f = np.empty(len(returns))
    f_prev, r_prev = f0, r0
    for t in range(len(returns)):
        f_prev = beta[0] + beta[1] * f_prev + beta[2] * abs(r_prev)
        f[t] = f_prev
        r_prev = returns[t]
    return f


def _pinball_loss(
    beta: np.ndarray, returns: np.ndarray, f0: float, alpha: float
) -> float:
    f = _propagate(beta, returns, f0, 0.0)
    err = returns + f  # quer P(r_t < -f_t) = alpha
    return float(np.mean(np.maximum(alpha * err, (alpha - 1) * err)))


def _fit_beta(returns: np.ndarray, f0: float, alpha: float, seed: int) -> np.ndarray:
    """Multiplos restarts (problema nao-convexo). Alguns restarts podem explorar regioes
    instaveis da recursao (ex: beta[1] > 1) e estourar (overflow -> loss nao finita) --
    esses sao descartados, nunca escolhidos como `best`, mesmo se forem o 1o restart."""
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(N_RESTARTS):
        x0 = np.array([f0 * 0.05, 0.85, 0.05]) + rng.normal(0, 0.02, 3)
        with np.errstate(over="ignore", invalid="ignore"):
            result = minimize(
                _pinball_loss, x0, args=(returns, f0, alpha), method="Nelder-Mead"
            )
        if not np.isfinite(result.fun):
            continue
        if best is None or result.fun < best.fun:
            best = result
    if best is None:
        raise RuntimeError(
            f"CAViaR: nenhum dos {N_RESTARTS} restarts convergiu para alpha={alpha}"
        )
    return best.x


@register_model("caviar")
class CaviarVaR(VaRModel):
    category = ModelCategory.ML

    def fit(self, returns: pd.Series) -> "CaviarVaR":
        self.train_returns_ = returns
        self._initial_fit: dict[float, tuple[np.ndarray, float]] = {}
        return self

    def _initial_beta(self, alpha: float) -> tuple[np.ndarray, float]:
        if alpha not in self._initial_fit:
            train = self.train_returns_.to_numpy()
            f0 = -np.quantile(train, alpha)
            beta = _fit_beta(train, f0, alpha, seed=int(alpha * 10000))
            self._initial_fit[alpha] = (beta, f0)
        return self._initial_fit[alpha]

    def estimate_var(
        self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1
    ) -> VaREstimate:
        beta, f0 = self._initial_beta(alpha)
        full_returns = pd.concat([self.train_returns_, returns]).to_numpy()
        n_train = len(self.train_returns_)

        var_values = np.empty(len(returns))
        f_prev, r_prev = f0, (full_returns[n_train - 1] if n_train > 0 else 0.0)
        pos = 0
        while pos < len(returns):
            chunk_end = min(pos + REFIT_FREQUENCY_DAYS, len(returns))
            chunk = full_returns[n_train + pos : n_train + chunk_end]

            f_chunk = _propagate(beta, chunk, f_prev, r_prev)
            var_values[pos:chunk_end] = f_chunk
            f_prev, r_prev = f_chunk[-1], chunk[-1]

            pos = chunk_end
            if pos < len(returns):
                # janela expansiva: reajusta beta com todo o dado conhecido ate aqui
                history = full_returns[: n_train + pos]
                f0_refit = -np.quantile(history, alpha)
                beta = _fit_beta(
                    history, f0_refit, alpha, seed=int(alpha * 10000) + pos
                )

        var_series = pd.Series(
            np.maximum(var_values, 0) * (horizon**0.5), index=returns.index
        )
        return VaREstimate(
            var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name
        )
