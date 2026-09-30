"""RF-05 do M1.6d: o backend nao declara dependencia numerica.

As seis bibliotecas que calculam chegam pelo motor, que so o `worker` instala (D-17); na
`web`, `import tensorflow` falha. Este teste le o `pyproject.toml` do backend e reprova
qualquer entrada de `project.dependencies` ou de cada lista de
`project.optional-dependencies` cujo nome, normalizado, seja uma delas.

So importa a biblioteca padrao: nao pede banco nem motor.
"""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

_TESTES = Path(__file__).resolve().parent
_PYPROJECT = _TESTES.parent / "pyproject.toml"
_VERSOES_TRAVADAS = _TESTES / "test_versoes_travadas.py"

# copia literal de `_BIBLIOTECAS` em `tests/test_versoes_travadas.py`, a da identidade
# dos retratos; nao e importada porque aquele modulo arrasta o motor e o Django. O teste
# `test_a_lista_copiada_e_a_de_test_versoes_travadas` impede que a copia envelheca.
_BIBLIOTECAS = ("tensorflow", "keras", "numpy", "scipy", "pandas", "arch")

_NOME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _nome(requisito: str) -> str:
    """'Pandas[performance]>=2 ; python_version>"3"' -> 'pandas' (PEP 503)."""
    achado = _NOME.match(requisito)
    assert achado is not None, f"requisito ilegivel: {requisito!r}"
    return re.sub(r"[-_.]+", "-", achado.group(1)).lower()


def _requisitos() -> list[tuple[str, str]]:
    """Cada entrada lida, com a origem dela: (origem, requisito)."""
    projeto = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]
    requisitos = [
        ("project.dependencies", requisito)
        for requisito in projeto.get("dependencies", [])
    ]
    for extra, lista in projeto.get("optional-dependencies", {}).items():
        requisitos.extend(
            (f"project.optional-dependencies.{extra}", requisito) for requisito in lista
        )
    return requisitos


def test_o_backend_nao_declara_biblioteca_numerica() -> None:
    proibidas = [
        f"{origem}: {requisito!r}"
        for origem, requisito in _requisitos()
        if _nome(requisito) in _BIBLIOTECAS
    ]
    assert proibidas == [], f"dependencia numerica no backend: {proibidas}"


def test_a_lista_copiada_e_a_de_test_versoes_travadas() -> None:
    arvore = ast.parse(_VERSOES_TRAVADAS.read_text(encoding="utf-8"))
    originais = [
        ast.literal_eval(no.value)
        for no in arvore.body
        if isinstance(no, ast.Assign)
        and any(
            isinstance(alvo, ast.Name) and alvo.id == "_BIBLIOTECAS"
            for alvo in no.targets
        )
    ]
    assert len(originais) == 1, (
        f"_BIBLIOTECAS ausente ou repetida em {_VERSOES_TRAVADAS}"
    )
    assert originais[0] == _BIBLIOTECAS
