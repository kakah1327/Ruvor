"""V-05b do M1.4: o `runner` alterado devolve os mesmos numeros.

Este arquivo mora FORA de `engine/tests/baseline/` de proposito: o trabalho `motor` da CI
roda `pytest engine/tests --ignore=engine/tests/baseline`, entao um V-05b la dentro seria
excluido em silencio. O V-05 guarda os modelos e roda so no hospedeiro; o V-05b guarda o
caminho do runner e roda em toda parte.

A comparacao NAO e contra `engine/tests/baseline/valores.json`, e isso e decisao da spec:

1. a linha de base e de RETORNOS e o runner quer PRECOS — reconstruir precos por
   `exp(cumsum(r))` e voltar por `log` nao e bit-exato, reintroduz ruido de ~1e-16;
2. o EGARCH daquela serie e patologicamente sensivel: o ESTADO registra o VaR subindo de
   8% a 113% por uma diferenca de 2,1e-6.

Entao o V-05b compara `run_experiment` com a CHAMADA DIRETA aos mesmos modelos, no mesmo
processo e sobre a mesma serie de precos. Igualdade exata, sem tolerancia, sem herdar
divida alheia — a pergunta e "o caminho novo mudou algum numero?", nao "o motor e portatil".

Os seis nao neurais, e so eles: incluir as redes transformaria um criterio barato em
minutos de CI, e a semente delas e o V-03 que guarda.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine import seeding
from engine.backtesting import get_backtest, load_all_backtest_modules
from engine.data.preprocessing import clean_prices, log_returns
from engine.experiments.runner import (
    ExperimentConfig,
    ModelRunResult,
    run_experiment,
)
from engine.models import get_model, load_all_model_modules

#: os seis que a linha de base cobre; as redes ficam com o V-03
MODELOS_NAO_NEURAIS = [
    "parametric",
    "historical",
    "monte_carlo",
    "garch_1_1",
    "egarch",
    "caviar",
]
BACKTESTS = ["kupiec", "christoffersen", "dq", "basileia"]
ALPHAS = [0.05, 0.01]
TREINO = 252
N_PRECOS = 553  # 552 retornos: 252 de treino e 300 de teste, a forma da linha de base

#: (modelo, alpha) -> (serie de VaR, {backtest: (passou, p_valor)})
Referencia = dict[tuple[str, float], tuple[pd.Series, dict[str, tuple[bool, float]]]]

TICKER = "TESTE3"
INICIO = "2020-01-01"
FIM = "2022-02-11"


def _precos() -> pd.DataFrame:
    """Serie de PRECOS sintetica — e o que o contrato do DataProvider entrega ao runner."""
    rng = np.random.default_rng(42)
    indice = pd.bdate_range(INICIO, periods=N_PRECOS)
    valores = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, N_PRECOS)))
    return pd.DataFrame({"close": valores}, index=indice)


class PrecoFixo:
    """DataProvider estrutural: devolve sempre a mesma serie, sem rede."""

    def __init__(self, precos: pd.DataFrame) -> None:
        self._precos = precos
        self.chamadas: list[tuple[str, str, str]] = []

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        self.chamadas.append((ticker, start, end))
        return self._precos.copy()


def _config(**trocas) -> ExperimentConfig:
    campos = {
        "ticker": TICKER,
        "start": INICIO,
        "end": FIM,
        "model_names": list(MODELOS_NAO_NEURAIS),
        "backtest_names": list(BACKTESTS),
        "alphas": list(ALPHAS),
        "train_window_days": TREINO,
    }
    return ExperimentConfig(**{**campos, **trocas})


def _direto() -> Referencia:
    """A chamada direta aos mesmos modelos, no mesmo processo — o lado de referencia.

    Reproduz o pipeline do runner sem passar por ele: `clean_prices` -> `log_returns` ->
    corte em `TREINO` -> `fit` -> `estimate_var` -> o mesmo alinhamento antes dos backtests.
    """
    load_all_model_modules()
    load_all_backtest_modules()

    retornos = log_returns(clean_prices(_precos())["close"])
    treino = retornos.iloc[:TREINO]
    teste = retornos.iloc[TREINO:]

    esperado = {}
    for nome in MODELOS_NAO_NEURAIS:
        modelo = get_model(nome)().fit(treino)
        for alpha in ALPHAS:
            estimativa = modelo.estimate_var(teste, alpha=alpha, horizon=1)
            alinhados = teste.reindex(estimativa.var_series.index).dropna()
            var_series = estimativa.var_series.reindex(alinhados.index)
            backtests = {
                bt: (resultado.passed, resultado.p_value)
                for bt in BACKTESTS
                for resultado in [get_backtest(bt)().run(alinhados, var_series, alpha)]
            }
            esperado[(nome, alpha)] = (var_series, backtests)
    return esperado


@pytest.fixture(scope="module")
def resultado_do_runner() -> dict[tuple[str, float], ModelRunResult]:
    load_all_model_modules()
    load_all_backtest_modules()
    resultado = run_experiment(_config(), provider=PrecoFixo(_precos()))
    return {(run.model_name, run.alpha): run for run in resultado.runs}


def test_o_runner_roda_os_seis_sem_erro(resultado_do_runner) -> None:
    """Sem isto, um runner que falhasse em tudo passaria nos testes de igualdade abaixo
    apenas por nao ter numero nenhum para comparar."""
    assert len(resultado_do_runner) == len(MODELOS_NAO_NEURAIS) * len(ALPHAS)
    assert [run.error for run in resultado_do_runner.values()] == [None] * 12


@pytest.mark.parametrize("nome", MODELOS_NAO_NEURAIS)
@pytest.mark.parametrize("alpha", ALPHAS)
def test_var_e_backtests_batem_com_a_chamada_direta(
    nome: str, alpha: float, resultado_do_runner, referencia
) -> None:
    """V-05b — igualdade EXATA entre o caminho do runner e a chamada direta."""
    run = resultado_do_runner[(nome, alpha)]
    var_esperada, backtests_esperados = referencia[(nome, alpha)]

    assert run.estimate is not None, (
        "a alteracao 3 do RF-02: o VaR precisa sair do runner"
    )
    var_do_runner = run.estimate.var_series.reindex(var_esperada.index)
    pd.testing.assert_series_equal(var_do_runner, var_esperada, check_exact=True)

    do_runner = {bt.test_name: (bt.passed, bt.p_value) for bt in run.backtests}
    assert do_runner == backtests_esperados


@pytest.fixture(scope="module")
def referencia() -> Referencia:
    return _direto()


def test_a_estimativa_devolvida_e_a_que_produziu_os_backtests(
    resultado_do_runner,
) -> None:
    """O campo novo nao pode ser um VaR recalculado por fora: o indice do teste e o
    alinhamento tem de ser os do proprio experimento."""
    run = resultado_do_runner[("historical", 0.05)]
    assert run.estimate is not None
    assert run.estimate.model_name == "historical"
    assert run.estimate.alpha == 0.05
    assert run.estimate.horizon == 1


def test_o_padrao_de_seed_e_o_do_motor() -> None:
    assert _config().seed == seeding.DEFAULT_SEED


def test_o_runner_configura_a_semente_e_nao_a_aplica(monkeypatch) -> None:
    """O runner CONFIGURA, nao semeia — quem semeia e `_fit_for_alpha`, porque o `fit()`
    dos neurais e preguicoso e semear aqui semearia antes de o treino existir."""
    from engine.experiments import runner as modulo

    configuradas: list[int] = []
    aplicadas: list[None] = []
    monkeypatch.setattr(modulo.seeding, "configure", configuradas.append)
    monkeypatch.setattr(modulo.seeding, "apply", lambda: aplicadas.append(None))

    run_experiment(
        _config(seed=7, model_names=["historical"], backtest_names=["kupiec"]),
        provider=PrecoFixo(_precos()),
    )

    assert configuradas == [7]
    assert aplicadas == []
