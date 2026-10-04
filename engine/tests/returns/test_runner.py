"""M5.1, T2: `run_return_experiment` com um DataProvider de teste, sem rede.

Um resultado por modelo, na ordem pedida; o modelo que levanta vira `error` e o outro segue;
serie <= treino levanta `ValueError`; a avaliacao e o `next_value` sao os de chamar o modelo
e o `evaluate` a mao, sobre o mesmo corte.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.data.preprocessing import fetch_returns
from engine.returns import (
    ReturnExperimentConfig,
    evaluate,
    get_return_model,
    load_all_return_model_modules,
    run_return_experiment,
)
from engine.returns.models import Ar1Return

TICKER = "TESTE3"
INICIO = "2020-01-01"
FIM = "2024-01-01"
TREINO = 252


def _precos(n: int) -> pd.DataFrame:
    rng = np.random.default_rng(5)
    indice = pd.bdate_range(INICIO, periods=n)
    valores = 100.0 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, n)))
    return pd.DataFrame({"close": valores}, index=indice)


class PrecoFixo:
    """DataProvider estrutural: devolve sempre a mesma serie, sem rede."""

    def __init__(self, precos: pd.DataFrame) -> None:
        self._precos = precos

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        return self._precos.copy()


def _config(nomes: list[str]) -> ReturnExperimentConfig:
    return ReturnExperimentConfig(
        ticker=TICKER,
        start=INICIO,
        end=FIM,
        model_names=nomes,
        train_window_days=TREINO,
    )


@pytest.fixture(autouse=True)
def _registry() -> None:
    load_all_return_model_modules()


@pytest.mark.parametrize(
    "nomes", [["historical_mean", "ar_1"], ["ar_1", "historical_mean"]]
)
def test_um_resultado_por_modelo_na_ordem_pedida(nomes: list[str]) -> None:
    resultado = run_return_experiment(_config(nomes), PrecoFixo(_precos(700)))
    assert [run.model_name for run in resultado.runs] == nomes
    for run in resultado.runs:
        assert run.error is None
        assert run.evaluation is not None
        assert isinstance(run.next_value, float)
    assert resultado.config.model_names == nomes


def test_a_avaliacao_e_o_proximo_pregao_sao_os_da_chamada_a_mao() -> None:
    provider = PrecoFixo(_precos(700))
    resultado = run_return_experiment(_config(["historical_mean", "ar_1"]), provider)

    returns = fetch_returns(provider, TICKER, INICIO, FIM)
    train, test = returns.iloc[:TREINO], returns.iloc[TREINO:]
    assert len(test) == 700 - 1 - TREINO
    for run in resultado.runs:
        previsao = get_return_model(run.model_name)().forecast(train, test)
        assert run.evaluation == evaluate(test, previsao.series)
        assert run.next_value == previsao.next_value


def test_o_modelo_que_levanta_vira_error_e_o_outro_segue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(self, train, test):
        raise RuntimeError("falhou de proposito")

    monkeypatch.setattr(Ar1Return, "forecast", explode)
    resultado = run_return_experiment(
        _config(["ar_1", "historical_mean"]), PrecoFixo(_precos(700))
    )
    falhou, seguiu = resultado.runs
    assert falhou.model_name == "ar_1"
    assert falhou.error == "falhou de proposito"
    assert (falhou.evaluation, falhou.next_value) == (None, None)
    assert seguiu.model_name == "historical_mean"
    assert seguiu.error is None and seguiu.evaluation is not None


def test_nome_fora_do_registry_vira_error() -> None:
    resultado = run_return_experiment(
        _config(["nao_existe", "ar_1"]), PrecoFixo(_precos(700))
    )
    assert resultado.runs[0].error is not None
    assert resultado.runs[1].error is None


@pytest.mark.parametrize("n_precos", [TREINO, TREINO + 1])
def test_serie_ate_o_treino_levanta(n_precos: int) -> None:
    # n_precos precos dao n_precos - 1 retornos: <= 252
    with pytest.raises(ValueError):
        run_return_experiment(_config(["ar_1"]), PrecoFixo(_precos(n_precos)))


def test_um_retorno_alem_do_treino_ja_roda() -> None:
    resultado = run_return_experiment(_config(["ar_1"]), PrecoFixo(_precos(TREINO + 2)))
    assert resultado.runs[0].error is None
