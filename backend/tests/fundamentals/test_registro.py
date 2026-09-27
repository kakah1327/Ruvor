"""As tres tarefas de fundamentos entram por descoberta automatica (RF-29).

Molde de `test_tarefas_de_app_entram_por_descoberta_automatica`, em
`tests/test_celery_registro.py`: em subprocesso, porque `app.task` registra com
`shared=True`, e basta outro teste da sessao ter importado `apps.fundamentals.tasks` para
o registro aparecer populado sem que `autodiscover_tasks()` tenha sido chamado. Este
modulo, pela mesma razao, nao importa `apps.fundamentals.tasks`.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# O diretorio de `backend/`, onde `config` e `apps` sao importaveis.
_BACKEND_DIR = Path(__file__).resolve().parents[2]

# A descoberta e preguicosa: `app.finalize()` nao importa modulo nenhum, e sem
# `import_default_modules()` o criterio reprovaria quem acertasse.
_SCRIPT = """
import django

django.setup()

import config

config.celery_app.loader.import_default_modules()
for name in sorted(config.celery_app.tasks):
    if name.startswith("apps."):
        print(name)
"""

_FUNDAMENTALS_TASKS = {
    "apps.fundamentals.tasks.importar_fundamentos",
    "apps.fundamentals.tasks.calcular_fundamentos",
    "apps.fundamentals.tasks.rotina_fundamentos",
}


def test_rf29_tarefas_de_fundamentos_entram_por_descoberta_automatica() -> None:
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings_test"}
    completed = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    registered = set(completed.stdout.split())
    assert _FUNDAMENTALS_TASKS <= registered, completed.stdout
