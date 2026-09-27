"""V-03 e V-04 do M1.4: os tres modelos neurais passam a ser reproduziveis.

O caminho exercitado aqui e o do repositorio — `get_model(nome)().fit(...)`, sem
`run_experiment` —, e e de proposito: `engine.seeding.apply()` mora em `_fit_for_alpha`,
entao quem chama o modelo direto tambem roda semeado. Se a semeadura morasse no runner,
este teste ficaria verde sobre codigo nao semeado.

"Duas execucoes" sao duas INSTANCIAS novas, nunca duas chamadas na mesma: `_fit_for_alpha`
so roda na primeira `estimate_var` de cada alpha, e o laco de reajuste consome
aleatoriedade em toda chamada.

Um alpha so (0.05) basta para o V-03: o que ele prova e determinismo, e `_fit_for_alpha`
roda por alpha independentemente. Sao seis treinos ali, mais dois no V-04.

Mas um alpha so NAO distingue os dois pontos de semeadura — com ele o V-03 fica verde
tambem sobre a semeadura no `fit()`, e foi medido. Quem defende essa distincao e
`test_a_ordem_dos_alphas_nao_muda_o_var_de_nenhum_deles`, com dois alphas e mais quatro
treinos.
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


def test_a_ordem_dos_alphas_nao_muda_o_var_de_nenhum_deles() -> None:
    """O ponto de semeadura e `_fit_for_alpha`, nunca o `fit()` (RF-01).

    Com **um** alpha so, os dois pontos sao indistinguiveis: entre o `fit()` preguicoso e
    o unico treino nao ha nada que consuma aleatoriedade, e o V-03 fica verde tambem sobre
    a semeadura no lugar errado — medido. Com **dois** alphas em ordem trocada a diferenca
    aparece: cada `_fit_for_alpha` semeia, entao o segundo treino nao depende do que o
    primeiro consumiu; semeando no `fit()`, o segundo alpha continuaria de onde o primeiro
    parou e mudaria de valor quando a ordem mudasse.

    Escolhido no lugar do espiao que conta `apply()` por alpha porque prova a consequencia
    observavel — o VaR — e nao a forma da chamada; um espiao que substituisse `apply()`
    deixaria de semear, e o que ele mediria seria so a contagem.

    Um modelo neural basta: o ponto de semeadura e da base `QuantileNeuralVaR`, comum aos
    tres. Sao quatro treinos.
    """
    direta = _var_por_alpha("lstm", (0.05, 0.01))
    trocada = _var_por_alpha("lstm", (0.01, 0.05))

    for alpha in (0.05, 0.01):
        pd.testing.assert_series_equal(
            direta[alpha], trocada[alpha], check_exact=True, obj=f"alpha={alpha}"
        )


def _var_por_alpha(nome: str, alphas: tuple[float, ...]) -> dict[float, pd.Series]:
    """Uma instancia so, os alphas pedidos NA ORDEM dada — cada um passa por um
    `_fit_for_alpha` proprio, e o anterior ja consumiu aleatoriedade."""
    load_all_model_modules()
    retornos = serie_da_linha_de_base()
    modelo = get_model(nome)().fit(retornos.iloc[:TREINO])
    teste = retornos.iloc[TREINO:]
    return {
        alpha: modelo.estimate_var(teste, alpha=alpha).var_series for alpha in alphas
    }


def test_sementes_diferentes_dao_var_diferente() -> None:
    """V-04 — senao o V-03 passaria com o modelo devolvendo constante."""
    seeding.configure(11)
    uma = _serie_de_var("lstm")
    seeding.configure(12)
    outra = _serie_de_var("lstm")

    assert not uma.equals(outra)


def test_derive_combina_a_semente_da_execucao_com_a_posicao() -> None:
    """RF-05 do M1.5b — a semente de cada retreino das redes.

    Posicao 0 devolve a semente configurada, sem transformacao: e o que mantem o treino
    inicial igual ao do motor 0.2.0 (V-04). Nas demais, as duas exigencias do RF-05:
    posicoes diferentes dao sementes diferentes, e sementes da execucao diferentes dao
    sementes diferentes na mesma posicao. As posicoes sao as de retreino, multiplos de 252.
    """
    posicoes = (0, 252, 504, 756, 1008)

    seeding.configure(11)
    assert seeding.derive(0) == 11
    da_11 = [seeding.derive(p) for p in posicoes]

    seeding.configure(12)
    assert seeding.derive(0) == 12
    da_12 = [seeding.derive(p) for p in posicoes]

    assert len(set(da_11)) == len(posicoes)
    assert len(set(da_12)) == len(posicoes)
    for posicao, uma, outra in zip(posicoes, da_11, da_12, strict=True):
        assert uma != outra, f"posicao {posicao}"


def test_apply_semeia_com_a_semente_derivada_da_posicao(monkeypatch) -> None:
    """`apply(position)` semeia com `derive(position)`; sem argumento, com a configurada."""
    from tensorflow import keras

    chamadas: list[int] = []
    monkeypatch.setattr(keras.utils, "set_random_seed", chamadas.append)

    seeding.configure(7)
    seeding.apply()
    seeding.apply(position=252)

    assert chamadas == [7, seeding.derive(252)]
