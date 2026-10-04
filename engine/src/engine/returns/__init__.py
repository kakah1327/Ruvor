"""Modelos de retorno do M5.1: a previsao do retorno de um pregao contra a referencia zero."""

from engine.returns.base import ReturnForecast, ReturnModel
from engine.returns.evaluation import ReturnEvaluation, evaluate
from engine.returns.registry import (
    _load_all_return_model_modules,
    get_return_model,
    list_return_models,
)
from engine.returns.runner import (
    ReturnExperimentConfig,
    ReturnExperimentResult,
    ReturnModelResult,
    run_return_experiment,
)

__all__ = [
    "ReturnEvaluation",
    "ReturnExperimentConfig",
    "ReturnExperimentResult",
    "ReturnForecast",
    "ReturnModel",
    "ReturnModelResult",
    "evaluate",
    "get_return_model",
    "list_return_models",
    "load_all_return_model_modules",
    "run_return_experiment",
]


def load_all_return_model_modules() -> None:
    """Ponto de entrada publico: importa `engine.returns.models` para popular o registry."""
    _load_all_return_model_modules()
