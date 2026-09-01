"""Prova que engine/ nao importa nenhuma biblioteca de plataforma.

Duas verificacoes, porque nenhuma sozinha fecha o buraco:
- inspecao em execucao pega import em nivel de modulo
- varredura estatica pega import diferido, dentro do corpo de funcao
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

import engine

PROIBIDOS = frozenset(
    {"django", "rest_framework", "celery", "flask", "fastapi", "sqlalchemy"}
)
RAIZ_FONTE = Path(engine.__file__).parent

# Importa TODO submodulo do pacote e imprime os proibidos encontrados. Roda em
# subprocesso para que modulos trazidos pelo pytest nao contaminem a medicao.
#
# Registra duas coisas: proibido que chegou a ser CARREGADO, e proibido que o
# codigo TENTOU importar mas nao esta instalado. Sem a segunda, o teste seria
# inerte — nenhum proibido esta instalado neste projeto, entao um `import flask`
# no codigo produziria ModuleNotFoundError, seria engolido, e passaria despercebido.
_SONDA = """
import importlib, pkgutil, sys
import engine

PROIBIDOS = {"django", "rest_framework", "celery", "flask", "fastapi", "sqlalchemy"}
tentados = set()

for _, nome, _ in pkgutil.walk_packages(engine.__path__, engine.__name__ + "."):
    try:
        importlib.import_module(nome)
    except ModuleNotFoundError as erro:
        ausente = (erro.name or "").split(".")[0]
        if ausente in PROIBIDOS:
            tentados.add(ausente)
        # senao: dependencia opcional ausente e esperado — ver D-29
    except ImportError:
        pass

carregados = {m.split(".")[0] for m in sys.modules}
print(",".join(sorted((carregados & PROIBIDOS) | tentados)))
"""

# Simula a ausencia do TensorFlow sem exigir um segundo ambiente.
_BLOQUEIO_TF = """
import sys
class _Bloqueio:
    def find_spec(self, nome, caminho=None, alvo=None):
        if nome.split(".")[0] in {"tensorflow", "keras"}:
            raise ImportError("bloqueado para o teste")
        return None
sys.meta_path.insert(0, _Bloqueio())
"""


def _proibidos_encontrados(prefixo: str = "") -> set[str]:
    saida = subprocess.run(
        [sys.executable, "-c", prefixo + _SONDA],
        capture_output=True,
        text=True,
        check=True,
    )
    achado = saida.stdout.strip()
    return set(achado.split(",")) if achado else set()


@pytest.mark.parametrize(
    "prefixo, condicao",
    [("", "com tensorflow"), (_BLOQUEIO_TF, "sem tensorflow")],
)
def test_nenhum_modulo_proibido_e_carregado(prefixo: str, condicao: str) -> None:
    encontrados = _proibidos_encontrados(prefixo)
    assert not encontrados, f"{condicao}: engine importa {sorted(encontrados)}"


def test_nenhum_import_proibido_no_fonte() -> None:
    achados: list[str] = []
    for arquivo in RAIZ_FONTE.rglob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Import):
                nomes = [a.name.split(".")[0] for a in no.names]
            elif isinstance(no, ast.ImportFrom):
                nomes = [(no.module or "").split(".")[0]]
            else:
                continue
            achados += [
                f"{arquivo.name}:{no.lineno} -> {n}" for n in nomes if n in PROIBIDOS
            ]
    assert not achados, "imports proibidos: " + "; ".join(achados)
