"""M2.2a, T5: o lado da web da carteira nao carrega o motor (RF-22; V-22, o lado da web).

No molde de `tests/api/test_sem_motor.py`: a suite roda no `worker`, que tem o motor, entao a prova
nao pode ser "o import falhou". Um localizador em `sys.meta_path` recusa os modulos proibidos e
**anota a tentativa**, num subprocesso limpo: `django.setup()`, os modulos do lado da web de
`apps.portfolios` e a resolucao de `/api/v1/portfolios` por `config.urls`. E, estatica, por `ast`,
para o import dentro de funcao.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.api.test_sem_motor import _nomes_importados

PACOTES_PROIBIDOS = frozenset({"engine", "tensorflow", "pandas"})
MODULOS_PROIBIDOS = frozenset(
    {
        "apps.risk.compute",
        "apps.risk.tasks",
        "apps.risk.snapshots",
        "apps.assets.tasks",
        "apps.portfolios.tasks",
        "apps.portfolios.provider",
        "apps.portfolios.compute",
    }
)
LADO_DA_WEB = (
    "config",
    "locks",
    "errors",
    "models",
    "series",
    "services",
    "serializers",
    "views",
    "urls",
    "apps",
)
ROTA = "/api/v1/portfolios"

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PORTFOLIOS_DIR = _BACKEND_DIR / "apps" / "portfolios"

_SONDA = """
import sys

PACOTES = {pacotes!r}
MODULOS = {modulos!r}
tentados = set()


def proibido(nome):
    return nome.split(".")[0] in PACOTES or any(
        nome == m or nome.startswith(m + ".") for m in MODULOS
    )


class _Bloqueio:
    def find_spec(self, nome, caminho=None, alvo=None):
        if proibido(nome):
            tentados.add(nome)
            raise ImportError("bloqueado para o teste: " + nome)
        return None


sys.meta_path.insert(0, _Bloqueio())

import importlib
import json

import django

django.setup()

importados = []
for nome in {modulos_da_web!r}:
    importlib.import_module("apps.portfolios." + nome)
    importados.append(nome)

from django.urls import resolve

casamento = resolve({rota!r})
print(json.dumps({{
    "tentados": sorted(tentados),
    "carregados": sorted(m for m in sys.modules if proibido(m)),
    "importados": importados,
    "view": casamento.func.view_class.__module__ + "." + casamento.func.view_class.__name__,
}}))
"""


def _proibido(nome: str) -> bool:
    return nome.split(".")[0] in PACOTES_PROIBIDOS or any(
        nome == m or nome.startswith(m + ".") for m in MODULOS_PROIBIDOS
    )


def test_v22_o_lado_da_web_e_a_rota_nao_carregam_o_motor() -> None:
    script = _SONDA.format(
        pacotes=set(PACOTES_PROIBIDOS),
        modulos=set(MODULOS_PROIBIDOS),
        modulos_da_web=list(LADO_DA_WEB),
        rota=ROTA,
    )
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings_test"}
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    achado = json.loads(completed.stdout.strip().splitlines()[-1])

    assert achado["tentados"] == [], achado
    assert achado["carregados"] == [], achado
    # contra a sonda inerte: os dez modulos e a rota ate a view da lista
    assert achado["importados"] == list(LADO_DA_WEB), achado
    assert achado["view"] == "apps.portfolios.views.PortfoliosView", achado


def test_v22_nenhum_import_proibido_no_fonte_do_lado_da_web() -> None:
    arquivos = [_PORTFOLIOS_DIR / f"{nome}.py" for nome in LADO_DA_WEB]
    arquivos += sorted((_PORTFOLIOS_DIR / "migrations").glob("*.py"))
    assert all(a.is_file() for a in arquivos)
    achados: list[str] = []
    for arquivo in arquivos:
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if not isinstance(no, ast.Import | ast.ImportFrom):
                continue
            achados += [
                f"{arquivo.name}:{no.lineno} -> {nome}"
                for nome in _nomes_importados(arquivo, no)
                if _proibido(nome)
            ]
    assert not achados, "imports proibidos: " + "; ".join(achados)
