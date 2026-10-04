"""Modelos de retorno do M5.1: a previsao do retorno de um pregao contra a referencia zero."""

from engine.returns.registry import (
    _load_all_return_model_modules,
    get_return_model,
    list_return_models,
)

__all__ = ["get_return_model", "list_return_models", "load_all_return_model_modules"]


def load_all_return_model_modules() -> None:
    """Ponto de entrada publico: importa `engine.returns.models` para popular o registry."""
    _load_all_return_model_modules()
