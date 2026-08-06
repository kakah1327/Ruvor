"""Registro central de modelos de VaR — permite descoberta dinamica por nome/categoria.

Um modelo novo se registra assim, em qualquer arquivo dentro de models/traditional,
models/garch ou models/ml:

    from varlab.models.base import VaRModel, ModelCategory
    from varlab.models.registry import register_model

    @register_model("meu_modelo")
    class MeuModelo(VaRModel):
        category = ModelCategory.ML
        ...

Depois disso `list_models()` e `get_model("meu_modelo")` ja enxergam a classe nova,
sem precisar editar web/, cli.py ou experiments/runner.py.
"""
from __future__ import annotations

from typing import Type

from varlab.models.base import ModelCategory, VaRModel

_REGISTRY: dict[str, Type[VaRModel]] = {}


def register_model(name: str):
    def decorator(cls: Type[VaRModel]) -> Type[VaRModel]:
        if name in _REGISTRY:
            raise ValueError(f"Modelo '{name}' ja registrado por {_REGISTRY[name]!r}")
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_model(name: str) -> Type[VaRModel]:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"Modelo '{name}' nao encontrado. Disponiveis: {sorted(_REGISTRY)}"
        ) from exc


def list_models(category: ModelCategory | None = None) -> list[str]:
    if category is None:
        return sorted(_REGISTRY)
    return sorted(n for n, cls in _REGISTRY.items() if cls.category == category)


def _load_all_model_modules() -> None:
    """Importa todos os submodulos de models/* para disparar o auto-registro.

    Chamado uma vez na inicializacao (app factory / cli). Modulos que precisam de
    dependencia opcional nao instalada (ex: tensorflow para os modelos de ML) sao
    ignorados silenciosamente — o resto do sistema continua funcionando.
    """
    import importlib
    import pkgutil

    import varlab.models.traditional as traditional_pkg
    import varlab.models.garch as garch_pkg
    import varlab.models.ml as ml_pkg

    for pkg in (traditional_pkg, garch_pkg, ml_pkg):
        for _, module_name, _ in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
            try:
                importlib.import_module(module_name)
            except ImportError:
                # dependencia opcional do grupo (garch/ml) nao instalada — ok, so
                # significa que os modelos desse modulo ficam de fora do registry.
                continue
