"""M2.2a, T3: o lado da regra nao importa o DRF (RF-20), o molde de `test_fase1_sem_drf`.

`config`, `locks`, `errors`, `models`, `series` e `services` de `apps/portfolios/` sao Django puro:
o DRF so entra em `serializers` e `views`, por cima.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.accounts.test_configuracao import _importa_drf

_PORTFOLIOS_DIR = Path(__file__).resolve().parents[2] / "apps" / "portfolios"
SEM_DRF = ("config", "locks", "errors", "models", "series", "services")


def _arquivos() -> list[Path]:
    return [_PORTFOLIOS_DIR / f"{nome}.py" for nome in SEM_DRF]


def test_rf20_a_varredura_acha_os_seis_arquivos() -> None:
    # contra a varredura inerte: os seis existem e sao lidos
    assert all(arquivo.is_file() for arquivo in _arquivos())
    assert len(_arquivos()) == 6


def test_rf20_nenhum_dos_seis_importa_o_drf() -> None:
    importam = [
        arquivo.name
        for arquivo in _arquivos()
        if _importa_drf(ast.parse(arquivo.read_text("utf-8")))
    ]
    assert importam == []
