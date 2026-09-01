from engine.models.registry import _load_all_model_modules, get_model, list_models

__all__ = ["get_model", "list_models", "load_all_model_modules"]


def load_all_model_modules() -> None:
    """Ponto de entrada publico: importa models/traditional, garch e ml para popular o registry."""
    _load_all_model_modules()
