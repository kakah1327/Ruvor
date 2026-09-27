"""As entradas `fundamentos` (RF-30) e `comunicados` (RF-17 do M3.2) do Beat, no molde do V-10
de `tests/risk/test_beat.py`.

**Roda em subprocesso** porque as settings sao avaliadas uma vez por processo: trocar a
variavel de ambiente dentro da sessao do pytest nao reconstruiria o
`CELERY_BEAT_SCHEDULE`. O valor `"15 21 3 * 2"` e escolhido para que dia do mes e dia da
semana **nao coincidam**: com `crontab(*campos)`, o `3` viraria dia da semana e o `2`,
mes -- tres campos reprovariam.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# O diretorio de `backend/`, onde `config` e `apps` sao importaveis.
_BACKEND_DIR = Path(__file__).resolve().parents[2]

_SCRIPT = """
import json
import sys

import django

django.setup()

from django.conf import settings

entry = settings.CELERY_BEAT_SCHEDULE[sys.argv[1]]
schedule = entry["schedule"]
print(json.dumps({
    "task": entry["task"],
    "minute": sorted(schedule.minute),
    "hour": sorted(schedule.hour),
    "day_of_month": sorted(schedule.day_of_month),
    "month_of_year": sorted(schedule.month_of_year),
    "day_of_week": sorted(schedule.day_of_week),
}))
"""


def _settings_em_subprocesso(
    fundamentals_cron: str,
    *,
    entrada: str = "fundamentos",
    variavel: str = "RUVOR_BEAT_FUNDAMENTALS_CRON",
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings_test",
        variavel: fundamentals_cron,
    }
    return subprocess.run(
        [sys.executable, "-c", _SCRIPT, entrada],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_rf30_horario_de_fundamentos_vem_da_variavel_com_campos_nomeados() -> None:
    completed = _settings_em_subprocesso("15 21 3 * 2")
    assert completed.returncode == 0, completed.stderr
    campos = json.loads(completed.stdout)
    assert campos["task"] == "apps.fundamentals.tasks.rotina_fundamentos"
    assert campos["minute"] == [15]
    assert campos["hour"] == [21]
    assert campos["day_of_month"] == [3]
    assert campos["month_of_year"] == list(range(1, 13))
    assert campos["day_of_week"] == [2]


def test_rf30_variavel_vazia_vale_o_padrao_segunda_as_oito() -> None:
    completed = _settings_em_subprocesso("")
    assert completed.returncode == 0, completed.stderr
    campos = json.loads(completed.stdout)
    assert campos["minute"] == [0]
    assert campos["hour"] == [8]
    assert campos["day_of_month"] == list(range(1, 32))
    assert campos["month_of_year"] == list(range(1, 13))
    assert campos["day_of_week"] == [1]


def test_rf30_variavel_com_tres_campos_reprova_a_configuracao() -> None:
    completed = _settings_em_subprocesso("15 21 *")
    assert completed.returncode != 0
    assert "ImproperlyConfigured" in completed.stderr, completed.stderr


# RF-17 do M3.2: a quarta entrada


def test_rf17_horario_de_comunicados_vem_da_variavel_com_campos_nomeados() -> None:
    completed = _settings_em_subprocesso(
        "15 21 3 * 2",
        entrada="comunicados",
        variavel="RUVOR_BEAT_DISCLOSURES_CRON",
    )
    assert completed.returncode == 0, completed.stderr
    campos = json.loads(completed.stdout)
    assert campos["task"] == "apps.fundamentals.tasks.importar_comunicados"
    assert campos["minute"] == [15]
    assert campos["hour"] == [21]
    assert campos["day_of_month"] == [3]
    assert campos["month_of_year"] == list(range(1, 13))
    assert campos["day_of_week"] == [2]


def test_rf17_variavel_vazia_vale_o_padrao_dias_uteis_as_vinte() -> None:
    completed = _settings_em_subprocesso(
        "", entrada="comunicados", variavel="RUVOR_BEAT_DISCLOSURES_CRON"
    )
    assert completed.returncode == 0, completed.stderr
    campos = json.loads(completed.stdout)
    assert campos["minute"] == [0]
    assert campos["hour"] == [20]
    assert campos["day_of_month"] == list(range(1, 32))
    assert campos["day_of_week"] == [1, 2, 3, 4, 5]
