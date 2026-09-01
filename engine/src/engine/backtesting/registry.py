"""Registro central de testes de backtesting — mesmo padrao de engine.models.registry."""
from __future__ import annotations

from typing import Type

from engine.backtesting.base import BacktestTest

_REGISTRY: dict[str, Type[BacktestTest]] = {}


def register_backtest(name: str):
    def decorator(cls: Type[BacktestTest]) -> Type[BacktestTest]:
        if name in _REGISTRY:
            raise ValueError(f"Teste '{name}' ja registrado por {_REGISTRY[name]!r}")
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_backtest(name: str) -> Type[BacktestTest]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"Teste '{name}' nao encontrado. Disponiveis: {sorted(_REGISTRY)}"
        ) from exc


def list_backtests() -> list[str]:
    return sorted(_REGISTRY)


def _load_all_backtest_modules() -> None:
    import importlib
    import pkgutil

    import engine.backtesting as backtesting_pkg

    for _, module_name, _ in pkgutil.iter_modules(backtesting_pkg.__path__, backtesting_pkg.__name__ + "."):
        if module_name.rsplit(".", 1)[-1] in {"base", "registry"}:
            continue
        importlib.import_module(module_name)
