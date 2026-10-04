"""V-10: `apps.api` nao importa o motor, nem direta nem indiretamente (RF-10).

A API roda na `web`, que nao tem o motor; os testes rodam no `worker`, que tem. Por isso a
prova nao pode ser "o import falhou": um localizador em `sys.meta_path` recusa os modulos
proibidos e **anota a tentativa**, e o teste reprova se houve alguma — inclusive a que um
`try/except ImportError` no codigo engolisse.

Duas verificacoes, porque nenhuma sozinha fecha o buraco (molde de
`engine/tests/test_modulos_proibidos.py`):
- em execucao, num subprocesso limpo: `django.setup()`, todos os submodulos de `apps.api`
  por `pkgutil.walk_packages` e a resolucao de uma rota de `/api/v1/` por `config.urls`
- estatica, com `ast`: pega o import diferido, dentro do corpo de funcao
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import apps.api

# Pacotes proibidos por inteiro, e modulos proibidos um a um (o resto de `apps.risk` e de
# `apps.assets` — modelos, configuracao — a API pode importar).
PACOTES_PROIBIDOS = frozenset({"engine", "tensorflow", "pandas"})
MODULOS_PROIBIDOS = frozenset(
    {
        "apps.risk.tasks",
        "apps.risk.compute",
        "apps.risk.snapshots",
        "apps.risk.lab",  # M2.4, RF-12: o `/lab` le os modelos e `decade.py`, nunca o calculo
        "apps.assets.tasks",
    }
)

# A rota resolvida pelo `config.urls`: a primeira rota de negocio de `/api/v1/`.
ROTA = "/api/v1/assets"

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_RAIZ_API = Path(apps.api.__file__).parent

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
import pkgutil

import django

django.setup()

import apps.api

importados = []
for _, nome, _ in pkgutil.walk_packages(apps.api.__path__, "apps.api."):
    importlib.import_module(nome)
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


def test_apps_api_e_config_urls_nao_carregam_o_motor() -> None:
    script = _SONDA.format(
        pacotes=set(PACOTES_PROIBIDOS), modulos=set(MODULOS_PROIBIDOS), rota=ROTA
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
    # Contra a sonda inerte: a varredura alcancou os modulos da app, e a rota passou
    # pelo `config.urls` ate a view da busca.
    assert {
        "apps.api.errors",
        "apps.api.serializers",
        "apps.api.urls",
        "apps.api.views",
    } <= set(achado["importados"]), achado
    assert achado["view"] == "apps.api.views.AssetListView", achado


def _proibido(nome: str) -> bool:
    return nome.split(".")[0] in PACOTES_PROIBIDOS or any(
        nome == m or nome.startswith(m + ".") for m in MODULOS_PROIBIDOS
    )


def _pacote_de(arquivo: Path) -> list[str]:
    """As partes do nome do pacote que contem `arquivo`, base do import relativo.

    Vale tambem para `__init__.py`: o pacote dele e o diretorio em que esta.
    """
    return list(arquivo.relative_to(_BACKEND_DIR).with_suffix("").parts[:-1])


def _nomes_importados(arquivo: Path, no: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(no, ast.Import):
        return [a.name for a in no.names]
    base = no.module or ""
    if no.level:
        pacote = _pacote_de(arquivo)
        pacote = pacote[: len(pacote) - (no.level - 1)]
        base = ".".join([*pacote, *([base] if base else [])])
    # `from apps.risk import tasks` importa `apps.risk.tasks`: confere os dois nomes
    return [base, *(f"{base}.{a.name}" for a in no.names)]


def test_nenhum_import_proibido_no_fonte_de_apps_api() -> None:
    arquivos = sorted(_RAIZ_API.rglob("*.py"))
    assert {a.name for a in arquivos} >= {"errors.py", "urls.py", "views.py"}
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
