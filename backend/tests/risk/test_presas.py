"""A execucao presa (M1.5c): V-15.

**O V-15 roda em subprocesso** porque as settings sao avaliadas uma vez por processo: trocar a
variavel de ambiente dentro da sessao do pytest nao reavaliaria `RUVOR_RISK_STALE_AFTER` nem a
validacao dele. O ambiente do subprocesso e sempre uma **copia** do deste; o padrao e medido com
`RUVOR_RISK_STALE_AFTER_MIN` removida da copia, porque o conteiner a recebe do compose.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# O diretorio de `backend/`, onde `config` e `apps` sao importaveis.
_BACKEND_DIR = Path(__file__).resolve().parents[2]

_SCRIPT = """
import django

django.setup()

from django.conf import settings

print(settings.RUVOR_RISK_STALE_AFTER.total_seconds())
"""


def _settings_em_subprocesso(
    stale_after_min: str | None, on_demand_timeout_min: str
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings_test",
        "RUVOR_ON_DEMAND_TIMEOUT_MIN": on_demand_timeout_min,
    }
    if stale_after_min is None:
        env.pop("RUVOR_RISK_STALE_AFTER_MIN", None)
    else:
        env["RUVOR_RISK_STALE_AFTER_MIN"] = stale_after_min
    return subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


# --- V-15: o prazo e configuracao, e nao pode ser menor que o do pedido sob demanda ---------


def test_prazo_padrao_e_de_seis_horas_sem_a_variavel() -> None:
    proc = _settings_em_subprocesso(None, "30")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "21600.0"


def test_prazo_menor_que_o_do_pedido_sob_demanda_derruba_a_carga() -> None:
    proc = _settings_em_subprocesso("20", "30")
    assert proc.returncode != 0
    assert "RUVOR_RISK_STALE_AFTER_MIN" in proc.stderr
    assert "RUVOR_ON_DEMAND_TIMEOUT_MIN" in proc.stderr


def test_prazo_igual_ao_do_pedido_sob_demanda_e_aceito() -> None:
    proc = _settings_em_subprocesso("30", "30")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "1800.0"
