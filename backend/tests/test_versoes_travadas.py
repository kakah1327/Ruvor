"""V-17 do M1.5b, primeira metade: a imagem do `worker` segue o lock do motor (RF-15).

Mora no backend, e nao em `engine/tests`, de proposito: la ele rodaria sobre o `.venv`
instalado pelo proprio lock e passaria independentemente da imagem. Aqui ele roda no
`worker` -- no dia a dia e na CI -- e guarda o `Dockerfile`: sem o `-c` do lock no
`pip install` do motor, a imagem sai com `numpy` 2.5.3 e `pandas` 3.0.6, e este teste
reprova.

As versoes sao lidas da metadata instalada, que e onde a identidade dos retratos (RF-03)
as le. A segunda metade do V-17 -- retrato com versao diferente nao e reaproveitado -- e
da T5.
"""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

import pytest

# o motor e montado em /repo/engine no `worker` (compose.yaml)
_LOCK = Path("/repo/engine/requirements-lock.txt")

# as seis bibliotecas que calculam, as mesmas da identidade dos retratos (RF-03)
_BIBLIOTECAS = ("tensorflow", "keras", "numpy", "scipy", "pandas", "arch")


def _versoes_do_lock() -> dict[str, str]:
    versoes: dict[str, str] = {}
    for linha in _LOCK.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        nome, _, versao = linha.partition("==")
        versoes[nome.strip().lower()] = versao.strip()
    return versoes


@pytest.mark.parametrize("biblioteca", _BIBLIOTECAS)
def test_versao_instalada_e_a_do_lock(biblioteca: str) -> None:
    lock = _versoes_do_lock()
    assert biblioteca in lock, f"{biblioteca} ausente de {_LOCK}"
    assert version(biblioteca) == lock[biblioteca]
