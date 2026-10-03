"""M2.2a, T6: o lado do `worker` (RF-22; V-22, o lado do `worker`).

`PORTFOLIO_MODELS` e uma copia de `apps.risk.compute.MODELS`: a paridade e conferida aqui, no
`worker`, que e onde aquele modulo importa. E as tres tarefas da carteira -- e o nome que
`apps/portfolios/services.py` passa a `send_task`, lido por `ast` -- estao no registro do Celery,
num subprocesso proprio, no molde de `_REGISTRO` de `tests/api/test_pedido.py`.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

from apps.portfolios import config as portfolio_config
from apps.risk.compute import MODELS

_BACKEND_DIR = Path(__file__).resolve().parents[2]
SERVICES = _BACKEND_DIR / "apps" / "portfolios" / "services.py"
TAREFAS = {
    "apps.portfolios.tasks.abrir_risco_carteira",
    "apps.portfolios.tasks.calcular_modelo_carteira",
    "apps.portfolios.tasks.fechar_risco_carteira",
}

_REGISTRO = """
import django

django.setup()

import config

config.celery_app.loader.import_default_modules()
for name in sorted(config.celery_app.tasks):
    print(name)
"""


def test_v22_portfolio_models_e_a_copia_de_models() -> None:
    assert portfolio_config.PORTFOLIO_MODELS == MODELS


def _nomes_do_send_task() -> set[str]:
    nomes: set[str] = set()
    for no in ast.walk(ast.parse(SERVICES.read_text(encoding="utf-8"))):
        if (
            isinstance(no, ast.Call)
            and isinstance(no.func, ast.Attribute)
            and no.func.attr == "send_task"
        ):
            primeiro = no.args[0] if no.args else None
            assert isinstance(primeiro, ast.Constant), no.lineno
            assert isinstance(primeiro.value, str), no.lineno
            nomes.add(primeiro.value)
    return nomes


def test_v22_as_tarefas_e_o_nome_do_send_task_estao_no_registro() -> None:
    nomes = _nomes_do_send_task()
    assert nomes == {"apps.portfolios.tasks.abrir_risco_carteira"}

    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings_test"}
    completed = subprocess.run(
        [sys.executable, "-c", _REGISTRO],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    registrados = set(completed.stdout.split())
    assert TAREFAS | nomes <= registrados, completed.stdout
