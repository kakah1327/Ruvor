"""V-19d do M1.6a: o `mypy` enxerga os tipos do Celery, sem isencao.

Com o `celery-types` instalado (D-134), um override que devolvesse `celery` ou `celery.*`
ao `ignore_missing_imports` nao faria o `mypy` reprovar nada: ele segue limpo, so que sem
verificar as tarefas. Este teste le a configuracao e reprova a isencao.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _modulos_isentos() -> list[str]:
    config = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    overrides = config["tool"]["mypy"].get("overrides", [])
    modulos: list[str] = []
    for override in overrides:
        module = override.get("module", [])
        modulos.extend([module] if isinstance(module, str) else module)
    return modulos


def test_nenhum_override_do_mypy_isenta_o_celery() -> None:
    isentos = [
        nome
        for nome in _modulos_isentos()
        if nome == "celery" or nome.startswith("celery.")
    ]
    assert isentos == [], f"override do mypy isenta o Celery: {isentos}"
