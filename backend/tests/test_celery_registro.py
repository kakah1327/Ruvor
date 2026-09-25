"""Prova que as tarefas estao registradas, sem tocar em Redis.

Este modulo importa **so** `config`. Importar `config.tasks` aqui registraria a tarefa
pelo proprio teste, e a assercao passaria a valer para qualquer implementacao — inclusive
uma que nunca registrasse nada no arranque do worker.

Pela mesma razao, a descoberta automatica (V-10d) e conferida em subprocesso: `app.task`
registra com `shared=True`, e basta outro teste da sessao ter importado `apps.risk.tasks`
para o registro aparecer populado sem que `autodiscover_tasks()` tenha sido chamado.
"""

import os
import subprocess
import sys
from pathlib import Path

from celery import Celery

import config

# O diretorio de `backend/`, onde `config` e `apps` sao importaveis.
_BACKEND_DIR = Path(__file__).resolve().parents[1]

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

_RISK_TASKS = {
    "apps.risk.tasks.abrir_execucao",
    "apps.risk.tasks.compute_asset_model",
    "apps.risk.tasks.fechar_execucao",
    "apps.risk.tasks.recalcular_cobertos",
}

_ASSETS_TASKS = {
    "apps.assets.tasks.importar_ativos",
    "apps.assets.tasks.importar_precos",
    "apps.assets.tasks.rotina_diaria",
}


def test_config_expoe_a_aplicacao_celery() -> None:
    assert isinstance(config.celery_app, Celery)


def test_ping_esta_registrada_ao_importar_config() -> None:
    assert "config.tasks.ping" in config.celery_app.tasks


def test_tarefas_de_app_entram_por_descoberta_automatica() -> None:
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
    assert _RISK_TASKS | _ASSETS_TASKS <= registered, completed.stdout
