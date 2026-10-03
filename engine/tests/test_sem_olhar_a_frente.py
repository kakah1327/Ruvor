"""O VaR do dia t nao usa o retorno de t nem os posteriores (M1.4b, D-158).

V-01 — a perturbacao: ajusta e estima numa serie sintetica e de novo com os retornos de
teste de `t` em diante trocados por outros; o VaR de todos os dias <= t tem de sair igual.
Para os modelos de volatilidade condicional ha a guarda do piso: se a sigma em `t` cair no
`sigma_floor_`, a perturbacao nao mede nada (o caso que a revisao achou no EGARCH em
t = 100), e o teste reprova alto em vez de passar calado.

V-02 — a janela expansiva dos tradicionais: o VaR do trecho que comeca em `p` e o calculado
a mao sobre `treino + teste[:p]` (o Monte Carlo pelo mesmo gerador, em sequencia), o
trecho 0 e o numero de antes da correcao, e os trechos mudam numa serie com mudanca de
regime.

V-03 — o GARCH contra o `arch`: a sigma do teste em `pos` e a volatilidade condicional do
proprio `arch`, com os parametros fixos do ultimo reajuste anterior a `pos`, sobre a serie
ate `pos` — a definicao, nao a implementacao.

Os modelos entram por `_FABRICAS`; os que tem piso de sigma, tambem por `_COM_PISO`.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import cache

import numpy as np
import pandas as pd
import pytest
from arch import arch_model
from scipy.stats import norm

from engine.models.base import VaRModel
from engine.models.garch._conditional import SCALE, ConditionalVolatilityVaR
from engine.models.garch.egarch import EgarchVaR
from engine.models.garch.garch_1_1 import Garch11VaR
from engine.models.ml.caviar import CaviarVaR
from engine.models.traditional._expanding import REFIT_FREQUENCY_DAYS
from engine.models.traditional.historical import HistoricalVaR
from engine.models.traditional.monte_carlo import MonteCarloVaR
from engine.models.traditional.parametric import ParametricVaR

N_TRAIN = 252
N_TEST = 756  # tres trechos de 252
ALPHA = 0.05
TOLERANCIA_ABSOLUTA = 1e-12
TOLERANCIA_RELATIVA_ARCH = 1e-12
FOLGA_DO_PISO = 1e-9

# meio do trecho 1, primeiro dia do trecho 2, meio do trecho 2 (posicoes do teste)
T_PERTURBACAO = (300, 504, 700)

_FABRICAS: dict[str, Callable[[], VaRModel]] = {
    "historical": HistoricalVaR,
    "parametric": ParametricVaR,
    "monte_carlo": MonteCarloVaR,
    "garch_1_1": Garch11VaR,
    "egarch": EgarchVaR,
    # hiperparametros de producao (N_RESTARTS = 10)
    "caviar": CaviarVaR,
}

# os modelos cuja sigma tem o piso `sigma_floor_` — a guarda do V-01 vale para eles
_COM_PISO = frozenset({"garch_1_1", "egarch"})


def _garch_simulado(semente: int, n: int) -> np.ndarray:
    """Um GARCH(1,1) simulado: volatilidade que muda, para a perturbacao ter o que mover."""
    rng = np.random.default_rng(semente)
    omega, alpha, beta = 1e-6, 0.1, 0.85
    sigma2 = omega / (1 - alpha - beta)
    valores = np.empty(n)
    anterior = 0.0
    for i in range(n):
        sigma2 = omega + alpha * anterior**2 + beta * sigma2
        valores[i] = rng.normal(0.0, np.sqrt(sigma2))
        anterior = valores[i]
    return valores


@cache
def _serie_original() -> pd.Series:
    valores = _garch_simulado(42, N_TRAIN + N_TEST)
    return pd.Series(
        valores, index=pd.bdate_range("2015-01-01", periods=N_TRAIN + N_TEST)
    )


def _serie_perturbada(t: int) -> pd.Series:
    """A serie original com os retornos de teste de `t` em diante trocados por outros."""
    original = _serie_original()
    outra = _garch_simulado(7, N_TRAIN + N_TEST)
    valores = original.to_numpy().copy()
    valores[N_TRAIN + t :] = outra[N_TRAIN + t :]
    return pd.Series(valores, index=original.index)


def _ajusta_e_estima(nome: str, serie: pd.Series) -> tuple[VaRModel, pd.Series]:
    modelo = _FABRICAS[nome]()
    modelo.fit(serie.iloc[:N_TRAIN])
    estimativa = modelo.estimate_var(serie.iloc[N_TRAIN:], alpha=ALPHA)
    return modelo, estimativa.var_series


@cache
def _original(nome: str) -> tuple[VaRModel, pd.Series]:
    """O ajuste e o VaR na serie original, compartilhados pelos tres `t`."""
    return _ajusta_e_estima(nome, _serie_original())


# --- V-01 -------------------------------------------------------------------------------


@pytest.mark.parametrize("t", T_PERTURBACAO)
@pytest.mark.parametrize("nome", sorted(_FABRICAS))
def test_o_var_ate_t_nao_muda_quando_o_futuro_muda(nome: str, t: int) -> None:
    modelo, var_a = _original(nome)

    if nome in _COM_PISO:
        assert isinstance(modelo, ConditionalVolatilityVaR)
        # a sigma reconstituida do VaR, sem chamar `_sigma_path`; a folga relativa existe
        # porque `VaR / z` de uma sigma no piso volta ao piso so a menos de arredondamento
        sigma_t = var_a.iloc[t] / (-norm.ppf(ALPHA))
        assert sigma_t > modelo.sigma_floor_ * (1 + FOLGA_DO_PISO), (
            f"{nome}: a sigma em t={t} ({sigma_t!r}) caiu no piso "
            f"sigma_floor_={modelo.sigma_floor_!r} — a perturbacao nao mede nada aqui; "
            "escolha outro t ou outra serie"
        )

    _, var_b = _ajusta_e_estima(nome, _serie_perturbada(t))

    assert var_a.index.equals(var_b.index)
    diferenca = np.abs(var_a.to_numpy()[: t + 1] - var_b.to_numpy()[: t + 1])
    assert diferenca.max() <= TOLERANCIA_ABSOLUTA, (
        f"{nome}: o VaR ate t={t} mudou quando so os retornos de t em diante mudaram "
        f"(diferenca maxima {diferenca.max()!r}, no dia {int(diferenca.argmax())})"
    )

    if nome in _COM_PISO:
        # a perturbacao chega ao modelo: o VaR depois de t muda (senao o teste e vazio)
        assert np.abs(var_a.to_numpy()[t + 1 :] - var_b.to_numpy()[t + 1 :]).max() > 0


# --- V-02 -------------------------------------------------------------------------------

_TRADICIONAIS = ("historical", "parametric", "monte_carlo")


@cache
def _serie_com_mudanca_de_regime() -> pd.Series:
    """Treino calmo, teste agitado: cada trecho ve mais do regime novo e o VaR tem de subir."""
    rng = np.random.default_rng(11)
    valores = np.concatenate(
        [rng.normal(0.0, 0.01, N_TRAIN), rng.normal(0.0, 0.03, N_TEST)]
    )
    return pd.Series(
        valores, index=pd.bdate_range("2015-01-01", periods=N_TRAIN + N_TEST)
    )


def _var_a_mao(nome: str, serie: pd.Series) -> list[float]:
    """O VaR de cada trecho calculado a mao, com numpy, sobre `treino + teste[:k * R]`."""
    z = norm.ppf(ALPHA)
    gerador = np.random.default_rng(MonteCarloVaR().random_state)
    valores = []
    for k in range(N_TEST // REFIT_FREQUENCY_DAYS):
        conhecidos = serie.to_numpy()[: N_TRAIN + k * REFIT_FREQUENCY_DAYS]
        media, desvio = conhecidos.mean(), conhecidos.std(ddof=1)
        if nome == "historical":
            valores.append(-np.quantile(conhecidos, ALPHA))
        elif nome == "parametric":
            valores.append(-(media + z * desvio))
        else:
            # o mesmo gerador, em sequencia: o trecho k tira depois dos k anteriores
            sorteio = gerador.normal(media, desvio, size=MonteCarloVaR().n_simulations)
            valores.append(-np.quantile(sorteio, ALPHA))
    return [float(v) for v in valores]


def _var_de_antes_da_correcao(nome: str, treino: pd.Series) -> float:
    """O numero do codigo de antes do M1.4b, que so olhava o treino."""
    if nome == "historical":
        return float(-treino.quantile(ALPHA))
    media, desvio = treino.mean(), treino.std(ddof=1)
    if nome == "parametric":
        return float(-(media + norm.ppf(ALPHA) * desvio))
    gerador = np.random.default_rng(MonteCarloVaR().random_state)
    sorteio = gerador.normal(media, desvio, size=MonteCarloVaR().n_simulations)
    return float(-np.quantile(sorteio, ALPHA))


@pytest.mark.parametrize("nome", _TRADICIONAIS)
def test_cada_trecho_usa_o_treino_e_o_teste_ate_o_seu_inicio(nome: str) -> None:
    serie = _serie_com_mudanca_de_regime()
    _, var = _ajusta_e_estima(nome, serie)
    assert var.index.equals(serie.index[N_TRAIN:])

    esperados = _var_a_mao(nome, serie)
    for k, esperado in enumerate(esperados):
        trecho = var.to_numpy()[
            k * REFIT_FREQUENCY_DAYS : (k + 1) * REFIT_FREQUENCY_DAYS
        ]
        assert len(trecho) == REFIT_FREQUENCY_DAYS
        assert (trecho == trecho[0]).all(), f"{nome}: o VaR muda dentro do trecho {k}"
        assert trecho[0] == pytest.approx(esperado, rel=1e-12, abs=0.0), (
            f"{nome}: o trecho {k} nao e o VaR de treino + teste[:{k * REFIT_FREQUENCY_DAYS}]"
        )

    # o trecho 0 e o numero de antes da correcao, bit a bit
    assert var.iloc[0] == _var_de_antes_da_correcao(nome, serie.iloc[:N_TRAIN])

    # a mudanca de regime aparece: cada trecho ve mais do teste agitado
    assert esperados[0] < esperados[1] < esperados[2]


@pytest.mark.parametrize("nome", _TRADICIONAIS)
def test_o_ultimo_trecho_incompleto_tambem_e_reestimado(nome: str) -> None:
    """Um teste de 600 pregoes: o terceiro trecho tem 96 e comeca em 504."""
    serie = _serie_com_mudanca_de_regime().iloc[: N_TRAIN + 600]
    _, var = _ajusta_e_estima(nome, serie)
    assert len(var) == 600
    ultimo = var.to_numpy()[2 * REFIT_FREQUENCY_DAYS :]
    assert len(ultimo) == 96
    assert (ultimo == ultimo[0]).all()
    assert ultimo[0] == pytest.approx(
        _var_a_mao(nome, _serie_com_mudanca_de_regime())[2], rel=1e-12, abs=0.0
    )


# --- V-03 -------------------------------------------------------------------------------


@pytest.mark.parametrize("pos", [0, 100, 252, 400])
@pytest.mark.parametrize("nome", ["garch_1_1", "egarch"])
def test_a_sigma_e_a_volatilidade_condicional_do_arch(nome: str, pos: int) -> None:
    modelo, _ = _original(nome)
    assert isinstance(modelo, ConditionalVolatilityVaR)
    serie = _serie_original()
    teste = serie.iloc[N_TRAIN:]

    # os parametros do ultimo reajuste anterior a `pos`
    if pos < ConditionalVolatilityVaR.REFIT_FREQUENCY_DAYS:
        params = modelo.result_.params
    else:
        params = modelo._fit_arch(serie.iloc[: N_TRAIN + 252] * SCALE).params

    # a serie ate `pos`, inclusive: a volatilidade condicional do dia `pos` no arch e
    # calculada com os retornos ate `pos - 1`
    ate_pos = serie.iloc[: N_TRAIN + pos + 1] * SCALE
    fixo = arch_model(
        ate_pos, mean="Zero", dist=modelo.dist, **modelo._arch_kwargs()
    ).fix(params)
    esperada = max(
        float(np.asarray(fixo.conditional_volatility)[-1]) / SCALE, modelo.sigma_floor_
    )

    obtida = float(modelo._sigma_path(teste).iloc[pos])
    assert obtida == pytest.approx(esperada, rel=TOLERANCIA_RELATIVA_ARCH, abs=0.0)
