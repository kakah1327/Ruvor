"""Logica compartilhada pelos modelos de volatilidade condicional (GARCH, EGARCH): fit
sobre o periodo de treino, depois forecast 1-passo-a-frente com os parametros FIXOS
propagados sobre os retornos reais do periodo de teste. A variancia condicional evolui a
cada dia com a informacao nova (VaR dinamico), mas os coeficientes so mudam quando o
modelo e reestimado — a cada REFIT_FREQUENCY_DAYS, com janela expansiva (treino + todo o
teste ja observado ate ali).

Reestimar periodicamente evita um problema conhecido do EGARCH: sem isso, os parametros
de uma janela de treino curta (252 dias), propagados por anos de teste sem atualizacao,
podem entrar num ciclo de realimentacao (residuo padronizado cresce -> termo
alpha/gamma reage mais forte -> variancia cai ainda mais) que colapsa a variancia
numericamente a zero. O GARCH comum nao sofre disso (a recursao tem um piso estrutural em
`omega`), mas reestimar tambem o mantem alinhado ao regime de mercado mais recente.

Mesmo reestimando, o PRIMEIRO bloco (ajustado só com a janela de treino inicial, a mais
curta e a unica sem alternativa de usar mais dados) ainda pode reincidir nesse colapso
antes do proximo reajuste. Por isso ha tambem um piso minimo de seguranca em `sigma`,
baseado no desvio-padrao historico do treino — so entra em acao nesse cenario extremo.
"""

from __future__ import annotations

import warnings
from abc import abstractmethod

import numpy as np
import pandas as pd
from arch import arch_model
from scipy.stats import norm

from engine.models.base import VaREstimate, VaRModel

SCALE = 100  # arch recomenda retornos em pontos percentuais para estabilidade numerica


class ConditionalVolatilityVaR(VaRModel):
    #: cadencia de reestimacao, em dias uteis — mesma da janela de treino padrao da plataforma
    REFIT_FREQUENCY_DAYS = 252

    def __init__(self, dist: str = "normal"):
        self.dist = dist

    @abstractmethod
    def _arch_kwargs(self) -> dict:
        """kwargs especificos do tipo de volatilidade (vol='GARCH'/'EGARCH', o=0/1 etc)."""

    @abstractmethod
    def _fallback_starting_values(self, variance: float) -> list[list[float]]:
        """Pontos de partida alternativos, na ordem dos parametros do arch, tentados
        apenas quando o SLSQP nao converge a partir do ponto que o arch escolhe sozinho.
        `variance` e a variancia amostral dos retornos (ja escalados por SCALE)."""

    def _fit_arch(self, returns_scaled: pd.Series):
        model = arch_model(
            returns_scaled, mean="Zero", dist=self.dist, **self._arch_kwargs()
        )
        result = model.fit(disp="off")
        if result.convergence_flag == 0:
            return result

        # O ponto de partida padrao do arch depende de uma busca em grade cujo resultado
        # muda com a plataforma (ordem de reducao do BLAS). Quando ela cai num canto ruim,
        # o SLSQP devolve `code 4` e parametros sem sentido (alpha ~ 11, variancia
        # condicional na casa dos milhares), e um resultado nao convergido nao e uma
        # estimativa de maxima verossimilhanca — nao serve. Ver D-46.
        for starting_values in self._fallback_starting_values(returns_scaled.var()):
            retry = model.fit(
                disp="off", starting_values=np.asarray(starting_values, dtype=float)
            )
            if retry.convergence_flag == 0:
                warnings.warn(
                    f"{self.name}: o ajuste convergiu a partir de valores iniciais "
                    f"alternativos {starting_values}, nao do ponto padrao do arch",
                    stacklevel=2,
                )
                return retry
        raise RuntimeError(
            f"{self.name}: o ajuste nao convergiu a partir de nenhum ponto de partida "
            f"(codigo {result.convergence_flag} no ponto padrao do arch)"
        )

    def fit(self, returns: pd.Series) -> ConditionalVolatilityVaR:
        self.train_returns_ = returns
        self.result_ = self._fit_arch(returns * SCALE)
        self.sigma_floor_ = returns.std() * 0.1
        return self

    def _sigma_path(self, returns: pd.Series, horizon: int = 1) -> pd.Series:
        """Serie de sigma (desvio-padrao condicional) walk-forward, sem look-ahead: cada
        ponto so usa parametros e retornos conhecidos ate a data anterior. Reaproveitada
        por `estimate_var` e por modelos hibridos (ex: GARCHNet, Etapa 3) que precisam da
        volatilidade do GARCH como feature, sem precisar de um VaREstimate completo.
        """
        full_returns = pd.concat([self.train_returns_, returns]) * SCALE
        n_train = len(self.train_returns_)

        sigma_1d = np.empty(len(returns))
        params = self.result_.params
        pos = 0
        while pos < len(returns):
            chunk_end = min(pos + self.REFIT_FREQUENCY_DAYS, len(returns))

            model = arch_model(
                full_returns.iloc[: n_train + chunk_end],
                mean="Zero",
                dist=self.dist,
                **self._arch_kwargs(),
            )
            fixed = model.fix(params)
            forecast = fixed.forecast(start=n_train + pos, horizon=1, reindex=False)
            sigma_1d[pos:chunk_end] = np.maximum(
                np.sqrt(forecast.variance.values[:, 0]) / SCALE, self.sigma_floor_
            )

            pos = chunk_end
            if pos < len(returns):
                # janela expansiva: reestima com todo o dado conhecido ate aqui p/ o proximo bloco
                params = self._fit_arch(full_returns.iloc[: n_train + pos]).params

        sigma_h = sigma_1d * (
            horizon**0.5
        )  # aproximacao p/ horizon > 1 (padrao da plataforma e 1 dia)
        return pd.Series(sigma_h, index=returns.index)

    def estimate_var(
        self, returns: pd.Series, alpha: float = 0.05, horizon: int = 1
    ) -> VaREstimate:
        sigma_h = self._sigma_path(returns, horizon=horizon)
        var_series = -norm.ppf(alpha) * sigma_h
        return VaREstimate(
            var_series=var_series, alpha=alpha, horizon=horizon, model_name=self.name
        )

    def full_sigma_series(self, full_returns: pd.Series, horizon: int = 1) -> pd.Series:
        """Serie de sigma cobrindo TODO `full_returns`, que deve comecar exatamente onde
        `train_returns_` comecou (ou seja, e' o proprio `train_returns_`, ou ele
        concatenado com retornos de teste subsequentes). Dentro do periodo de treino usa
        os valores ja ajustados em amostra; dali em diante, o forecast walk-forward de
        `_sigma_path`. Usado por modelos hibridos (ex: GARCHNet, Etapa 3) que precisam da
        volatilidade do GARCH alinhada a uma janela deslizante continua.
        """
        n_train = len(self.train_returns_)
        train_sigma = pd.Series(
            self.result_.conditional_volatility / SCALE,
            index=full_returns.index[:n_train],
        ) * (horizon**0.5)

        test_part = full_returns.iloc[n_train:]
        if len(test_part) == 0:
            return train_sigma
        return pd.concat([train_sigma, self._sigma_path(test_part, horizon=horizon)])
