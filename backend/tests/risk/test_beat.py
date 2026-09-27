"""O Beat e as tarefas de coleta: V-08, V-09, V-10 e V-10b.

**Nenhum teste chama a B3 nem o Yahoo** (V-12): `call_command` e substituido pelo nome em
`apps.assets.tasks`, que e onde as tarefas o chamam. Nenhum fala com o Redis: o `_enqueue`
substituido e o de `apps.assets.tasks`, proprio do modulo.

**O V-10 roda em subprocesso** porque as settings sao avaliadas uma vez por processo:
trocar a variavel de ambiente dentro da sessao do pytest nao reconstruiria o
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
from typing import Any, NoReturn

import pytest
from django.conf import settings
from django.core.management.base import CommandError

from apps.assets.tasks import _importar_ativos, _importar_precos, _rotina_diaria

# O diretorio de `backend/`, onde `config` e `apps` sao importaveis.
_BACKEND_DIR = Path(__file__).resolve().parents[2]

_SCRIPT = """
import json

import django

django.setup()

from django.conf import settings

schedule = settings.CELERY_BEAT_SCHEDULE["precos"]["schedule"]
print(json.dumps({
    "minute": sorted(schedule.minute),
    "hour": sorted(schedule.hour),
    "day_of_month": sorted(schedule.day_of_month),
    "month_of_year": sorted(schedule.month_of_year),
    "day_of_week": sorted(schedule.day_of_week),
}))
"""


def _settings_em_subprocesso(prices_cron: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings_test",
        "RUVOR_BEAT_PRICES_CRON": prices_cron,
    }
    return subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


# --- V-08: preco e risco com duas entradas; fundamentos e outra corrente (D-127) -----------


def test_beat_tem_as_duas_entradas_de_preco_e_risco_e_a_de_fundamentos() -> None:
    schedule = settings.CELERY_BEAT_SCHEDULE
    assert set(schedule) == {"catalogo", "precos", "fundamentos"}
    assert schedule["catalogo"]["task"] == "apps.assets.tasks.importar_ativos"
    assert schedule["precos"]["task"] == "apps.assets.tasks.rotina_diaria"
    assert (
        schedule["fundamentos"]["task"] == "apps.fundamentals.tasks.rotina_fundamentos"
    )


def test_nenhuma_entrada_do_beat_aponta_para_o_risco() -> None:
    tasks = [str(entry["task"]) for entry in settings.CELERY_BEAT_SCHEDULE.values()]
    assert not [t for t in tasks if t.startswith("apps.risk.tasks.")], tasks


# --- V-09: risco depois de preco, encadeado ------------------------------------------------


def test_rotina_diaria_enfileira_uma_corrente_precos_e_depois_risco(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.assets.tasks._enqueue", recebidos.append)

    _rotina_diaria()

    assert len(recebidos) == 1
    corrente = recebidos[0]
    assert corrente["subtask_type"] == "chain"
    elos = corrente.tasks
    assert [elo.task for elo in elos] == [
        "apps.assets.tasks.importar_precos",
        "apps.risk.tasks.recalcular_cobertos",
    ]
    # Imutavel: com `.s()`, o texto de `importar_precos` chegaria como calculated_at_iso.
    assert elos[1].immutable is True


# --- V-10: horario e configuracao ----------------------------------------------------------


def test_horario_de_precos_vem_da_variavel_com_campos_nomeados() -> None:
    completed = _settings_em_subprocesso("15 21 3 * 2")
    assert completed.returncode == 0, completed.stderr
    campos = json.loads(completed.stdout)
    assert campos["minute"] == [15]
    assert campos["hour"] == [21]
    assert campos["day_of_month"] == [3]
    assert campos["month_of_year"] == list(range(1, 13))
    assert campos["day_of_week"] == [2]


def test_variavel_vazia_vale_o_padrao() -> None:
    completed = _settings_em_subprocesso("")
    assert completed.returncode == 0, completed.stderr
    campos = json.loads(completed.stdout)
    assert campos["minute"] == [30]
    assert campos["hour"] == [19]
    assert campos["day_of_week"] == [1, 2, 3, 4, 5]


def test_variavel_com_tres_campos_reprova_a_configuracao() -> None:
    completed = _settings_em_subprocesso("15 21 *")
    assert completed.returncode != 0
    assert "ImproperlyConfigured" in completed.stderr, completed.stderr


# --- V-10b: o elo nao se rompe por ativo falho ---------------------------------------------


def test_importar_precos_devolve_a_falha_do_comando_em_vez_de_levantar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falha(*args: object, **kwargs: object) -> NoReturn:
        raise CommandError("coleta com falhas: PETR4")

    monkeypatch.setattr("apps.assets.tasks.call_command", falha)

    assert _importar_precos() == "FALHOU: coleta com falhas: PETR4"


def test_importar_precos_propaga_o_que_nao_e_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def quebra(*args: object, **kwargs: object) -> NoReturn:
        raise RuntimeError("a ingestao nao chegou a rodar")

    monkeypatch.setattr("apps.assets.tasks.call_command", quebra)

    with pytest.raises(RuntimeError, match="nao chegou a rodar"):
        _importar_precos()


# --- o caminho feliz, sem rede --------------------------------------------------------------


def _comando_que_escreve(chamadas: list[str]) -> Any:
    def comando(name: str, *args: object, **kwargs: Any) -> None:
        chamadas.append(name)
        kwargs["stdout"].write(f"saida de {name}\n")

    return comando


def test_importar_ativos_devolve_a_saida_do_comando(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas: list[str] = []
    monkeypatch.setattr(
        "apps.assets.tasks.call_command", _comando_que_escreve(chamadas)
    )

    assert _importar_ativos() == "saida de import_assets\n"
    assert chamadas == ["import_assets"]


def test_importar_precos_devolve_a_saida_do_comando(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas: list[str] = []
    monkeypatch.setattr(
        "apps.assets.tasks.call_command", _comando_que_escreve(chamadas)
    )

    assert _importar_precos() == "saida de import_prices\n"
    assert chamadas == ["import_prices"]
