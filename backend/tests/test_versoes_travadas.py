"""V-17 do M1.5b: a imagem do `worker` segue o lock do motor (RF-15), e um retrato de outra
versao de biblioteca nao volta (RF-03).

Mora no backend, e nao em `engine/tests`, de proposito: la ele rodaria sobre o `.venv`
instalado pelo proprio lock e passaria independentemente da imagem. Aqui ele roda no
`worker` -- no dia a dia e na CI -- e guarda o `Dockerfile`: sem o `-c` do lock no
`pip install` do motor, a imagem sai com `numpy` 2.5.3 e `pandas` 3.0.6, e este teste
reprova.

As versoes sao lidas da metadata instalada, que e onde a identidade dos retratos (RF-03)
as le. A segunda metade -- retrato gravado com uma versao diferente nao e reaproveitado, e
o novo e gravado ao lado dele -- usa os ajudantes de `tests/risk/test_snapshots.py`.
"""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

import pytest
from engine.models import load_all_model_modules

from apps.risk.models import ModelSnapshot
from apps.risk.snapshots import library_versions, load_valid, save
from tests.risk.test_snapshots import (
    ALPHA,
    MODELO,
    PREGOES_NA_BORDA,
    chave,
    com_serie,
    retrato,
)

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


# --- a segunda metade: retrato com outra versao de biblioteca --------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("biblioteca", _BIBLIOTECAS)
def test_retrato_de_outra_versao_de_biblioteca_nao_e_reaproveitado_e_o_novo_e_gravado(
    biblioteca: str,
) -> None:
    """Gravado por uma imagem em que so `biblioteca` tinha outra versao: nao volta, e o
    retrato de agora e gravado ao lado dele -- a gravacao idempotente nao o descarta."""
    load_all_model_modules()
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    agora = chave(asset, bars)
    outra = chave(
        asset,
        bars,
        library_versions={**library_versions(), biblioteca: "0.0.0"},
    )
    assert agora.library_versions[biblioteca] == version(biblioteca)
    save(outra, MODELO, ALPHA, bars, [retrato(0, variante=0.5)])

    assert load_valid(agora, MODELO, ALPHA, bars) == []

    save(agora, MODELO, ALPHA, bars, [retrato(0)])

    assert ModelSnapshot.objects.filter(asset=asset).count() == 2
    assert [s.position for s in load_valid(agora, MODELO, ALPHA, bars)] == [0]
