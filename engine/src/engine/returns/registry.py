"""Registro dos modelos de retorno (M5.1, RF-05) — o molde de `engine.models.registry`,
num dicionario **proprio**: o registry do VaR nao ve os modelos de retorno, e
`engine.models.list_models()` continua com os nove.

    from engine.returns.base import ReturnModel
    from engine.returns.registry import register_return_model

    @register_return_model("meu_modelo")
    class MeuModelo(ReturnModel):
        ...
"""

from __future__ import annotations

from collections.abc import Callable

from engine.returns.base import ReturnModel

_REGISTRY: dict[str, type[ReturnModel]] = {}


def register_return_model(
    name: str,
) -> Callable[[type[ReturnModel]], type[ReturnModel]]:
    def decorator(cls: type[ReturnModel]) -> type[ReturnModel]:
        if name in _REGISTRY:
            raise ValueError(
                f"Modelo de retorno '{name}' ja registrado por {_REGISTRY[name]!r}"
            )
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_return_model(name: str) -> type[ReturnModel]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"Modelo de retorno '{name}' nao encontrado. Disponiveis: {sorted(_REGISTRY)}"
        ) from exc


def list_return_models() -> list[str]:
    return sorted(_REGISTRY)


def _load_all_return_model_modules() -> None:
    """Importa `engine.returns.models` para disparar o auto-registro (um modulo so)."""
    import importlib

    importlib.import_module("engine.returns.models")
