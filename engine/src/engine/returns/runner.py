"""Orquestrador do retorno (M5.1, RF-05): liga data -> modelos de retorno -> validacao, no
molde de `engine.experiments.runner.run_experiment`.

O corte e o do risco: os `train_window_days` primeiros retornos sao o treino, e o resto e o
teste. A falha de um modelo fica no `error` dele, e os outros seguem.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.data.preprocessing import fetch_returns
from engine.returns.evaluation import ReturnEvaluation, evaluate
from engine.returns.registry import get_return_model


@dataclass
class ReturnExperimentConfig:
    ticker: str
    start: str
    end: str
    model_names: list[str]
    train_window_days: int = 252


@dataclass
class ReturnModelResult:
    model_name: str
    evaluation: ReturnEvaluation | None = None
    next_value: float | None = None
    error: str | None = None


@dataclass
class ReturnExperimentResult:
    config: ReturnExperimentConfig
    runs: list[ReturnModelResult]


def run_return_experiment(
    config: ReturnExperimentConfig, provider
) -> ReturnExperimentResult:
    """Roda cada modelo de `config.model_names`, na ordem pedida, sobre o ativo, e valida a
    previsao de cada um contra a referencia zero."""
    returns = fetch_returns(provider, config.ticker, config.start, config.end)
    if len(returns) <= config.train_window_days:
        raise ValueError(
            f"Periodo tem {len(returns)} dias uteis, insuficiente para a janela de "
            f"treino de {config.train_window_days} dias (nao sobraria dado de teste)"
        )
    train_returns = returns.iloc[: config.train_window_days]
    test_returns = returns.iloc[config.train_window_days :]

    runs: list[ReturnModelResult] = []
    for model_name in config.model_names:
        try:
            forecast = get_return_model(model_name)().forecast(
                train_returns, test_returns
            )
            evaluation = evaluate(test_returns, forecast.series)
        except Exception as exc:  # isola falha de 1 modelo do restante
            runs.append(ReturnModelResult(model_name=model_name, error=str(exc)))
            continue
        runs.append(
            ReturnModelResult(
                model_name=model_name,
                evaluation=evaluation,
                next_value=forecast.next_value,
            )
        )

    return ReturnExperimentResult(config=config, runs=runs)
