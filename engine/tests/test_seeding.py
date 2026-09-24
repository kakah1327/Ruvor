"""V-03 e V-04 do M1.4: os tres modelos neurais passam a ser reproduziveis.

O caminho exercitado aqui e o do repositorio — `get_model(nome)().fit(...)`, sem
`run_experiment` —, e e de proposito: `engine.seeding.apply()` mora em `_fit_for_alpha`,
entao quem chama o modelo direto tambem roda semeado. Se a semeadura morasse no runner,
este teste ficaria verde sobre codigo nao semeado.

"Duas execucoes" sao duas INSTANCIAS novas, nunca duas chamadas na mesma: `_fit_for_alpha`
so roda na primeira `estimate_var` de cada alpha, e o laco de reajuste consome
aleatoriedade em toda chamada.

Um alpha so (0.05) basta: o que se prova e determinismo, e `_fit_for_alpha` roda por alpha
independentemente. Sao seis treinos aqui, mais dois no V-04.
"""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd
import pytest
from conftest import serie_da_linha_de_base

from engine import seeding
from engine.models import get_model, load_all_model_modules

MODELOS_NEURAIS = ("garchnet", "lstm", "gru")
ALPHA = 0.05
TREINO = 252


@pytest.fixture(autouse=True)
def semente_padrao() -> Iterator[None]:
    """Devolve o modulo ao estado inicial depois de cada teste — `configure(DEFAULT_SEED)`
    e indistinguivel de nunca ter sido chamado."""
    yield
    seeding.configure(seeding.DEFAULT_SEED)


def _serie_de_var(nome: str) -> pd.Series:
    """Instancia NOVA, ajuste e estimativa: o caminho que passa por `_fit_for_alpha`."""
    load_all_model_modules()
    retornos = serie_da_linha_de_base()
    modelo = get_model(nome)().fit(retornos.iloc[:TREINO])
    return modelo.estimate_var(retornos.iloc[TREINO:], alpha=ALPHA).var_series


def test_apply_sem_configure_semeia_com_o_padrao(monkeypatch) -> None:
    """`apply()` nunca e inerte — sem `configure()` previo, semeia com `DEFAULT_SEED`."""
    from tensorflow import keras

    chamadas: list[int] = []
    monkeypatch.setattr(keras.utils, "set_random_seed", chamadas.append)

    seeding.apply()
    seeding.configure(7)
    seeding.apply()

    assert chamadas == [seeding.DEFAULT_SEED, 7]


@pytest.mark.parametrize("nome", MODELOS_NEURAIS)
def test_duas_instancias_com_a_mesma_semente_dao_var_identico(nome: str) -> None:
    """V-03 — o criterio central do RF-01."""
    primeira = _serie_de_var(nome)
    segunda = _serie_de_var(nome)

    pd.testing.assert_series_equal(primeira, segunda, check_exact=True)


def test_sementes_diferentes_dao_var_diferente() -> None:
    """V-04 — senao o V-03 passaria com o modelo devolvendo constante."""
    seeding.configure(11)
    uma = _serie_de_var("lstm")
    seeding.configure(12)
    outra = _serie_de_var("lstm")

    assert not uma.equals(outra)
