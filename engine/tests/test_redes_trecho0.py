"""V-04 do M1.5b: o primeiro trecho das redes nao muda.

O trecho de teste 0 da `var_series` -- os 252 dias previstos pelo treino inicial, antes do
primeiro retreino -- de `lstm`, `gru` e `garchnet`, nos dois niveis, sobre a serie de 552
pontos de `conftest.serie_da_linha_de_base`, com `DEFAULT_SEED`, tem de sair IGUAL, bit a
bit, a referencia capturada com o motor `0.2.0` no `worker` ja travado pelo lock (RF-16).
A semente por retreino (RF-05) muda os trechos seguintes; o primeiro, nunca.

So roda no `worker` (`RUVOR_REFERENCE_ENV=worker`, que o `compose.yaml` define ali e so
ali). Em qualquer outro lugar pula com motivo: o lock congela versao, nao plataforma, e a
linha de base ja provou que Linux e Windows divergem (D-46). Mora fora de `baseline/`,
que a CI exclui. Nenhum job da CI o roda: e verificacao manual, por
`docker compose exec -T worker python -m pytest /repo/engine/tests/test_redes_trecho0.py`.

Dentro do `worker`, referencia ausente ou versao instalada diferente da gravada e FALHA,
nunca pulo.

Captura: `RUVOR_CAPTURE_REFERENCE=1` grava o JSON em vez de comparar, e o teste FALHA de
proposito -- capturar nunca fica verde. Uma referencia gravada errada passaria para sempre;
por isso a forma dela tambem e conferida antes de comparar.
"""

from __future__ import annotations

import json
import math
import os
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path

import pytest
from conftest import serie_da_linha_de_base

from engine import seeding
from engine.models import get_model, load_all_model_modules

REFERENCIA = Path(__file__).parent / "fixtures" / "redes_trecho0.json"

REDES = ("lstm", "gru", "garchnet")
# a ordem do runner (`ExperimentConfig.alphas`); cada alpha semeia o proprio treino
ALPHAS = (0.05, 0.01)
TREINO = 252
# o trecho 0 inteiro: `REFIT_FREQUENCY_DAYS` dos modelos neurais
TRECHO = 252
# as seis bibliotecas que calculam, as mesmas da identidade dos retratos (RF-03)
BIBLIOTECAS = ("tensorflow", "keras", "numpy", "scipy", "pandas", "arch")

pytestmark = pytest.mark.skipif(
    os.environ.get("RUVOR_REFERENCE_ENV") != "worker",
    reason=(
        "a referencia do V-04 e do Linux do `worker`: o lock congela versao, nao "
        "plataforma (D-46). Rode no worker, com RUVOR_REFERENCE_ENV=worker"
    ),
)


@pytest.fixture(autouse=True)
def semente_padrao() -> Iterator[None]:
    seeding.configure(seeding.DEFAULT_SEED)
    yield
    seeding.configure(seeding.DEFAULT_SEED)


def _versoes_instaladas() -> dict[str, str]:
    return {nome: version(nome) for nome in BIBLIOTECAS}


def _trechos() -> dict[str, dict[str, list[float]]]:
    """Instancia NOVA por rede, ajuste no treino e estimativa sobre o teste inteiro -- o
    caminho que passa por `_fit_for_alpha` --, cortada no trecho 0."""
    load_all_model_modules()
    retornos = serie_da_linha_de_base()
    saida: dict[str, dict[str, list[float]]] = {}
    for rede in REDES:
        modelo = get_model(rede)().fit(retornos.iloc[:TREINO])
        saida[rede] = {}
        for alpha in ALPHAS:
            serie = modelo.estimate_var(retornos.iloc[TREINO:], alpha=alpha).var_series
            saida[rede][repr(alpha)] = [float(v) for v in serie.iloc[:TRECHO]]
    return saida


def _confere_forma(referencia: dict) -> None:
    """Tres redes x dois niveis x 252 valores, nenhum NaN, as seis versoes presentes."""
    versoes = referencia.get("library_versions")
    assert isinstance(versoes, dict), "referencia sem library_versions"
    assert set(versoes) == set(BIBLIOTECAS), f"versoes na referencia: {sorted(versoes)}"

    trechos = referencia.get("var_series_trecho0")
    assert isinstance(trechos, dict), "referencia sem var_series_trecho0"
    assert set(trechos) == set(REDES), f"redes na referencia: {sorted(trechos)}"
    for rede in REDES:
        assert set(trechos[rede]) == {repr(a) for a in ALPHAS}, (
            f"{rede}: niveis na referencia {sorted(trechos[rede])}"
        )
        for nivel, valores in trechos[rede].items():
            assert len(valores) == TRECHO, f"{rede} {nivel}: {len(valores)} valores"
            assert all(isinstance(v, float) and not math.isnan(v) for v in valores), (
                f"{rede} {nivel}: valor ausente, nao numerico ou NaN"
            )


def test_o_trecho_0_das_redes_e_igual_a_referencia_do_0_2_0() -> None:
    if os.environ.get("RUVOR_CAPTURE_REFERENCE") == "1":
        referencia = {
            "captured_with_engine": version("ruvor-engine"),
            "seed": seeding.DEFAULT_SEED,
            "library_versions": _versoes_instaladas(),
            "var_series_trecho0": _trechos(),
        }
        _confere_forma(referencia)
        REFERENCIA.parent.mkdir(exist_ok=True)
        # newline="": LF em qualquer plataforma, como o .gitattributes pede
        with open(REFERENCIA, "w", encoding="utf-8", newline="") as arquivo:
            arquivo.write(json.dumps(referencia, indent=2) + "\n")
        pytest.fail("referencia capturada; rode sem a variavel")

    assert REFERENCIA.is_file(), f"referencia do V-04 ausente: {REFERENCIA}"
    referencia = json.loads(REFERENCIA.read_text(encoding="utf-8"))
    _confere_forma(referencia)

    # versao diferente da gravada: a comparacao nao prova nada, e e falha, nao pulo
    assert _versoes_instaladas() == referencia["library_versions"]

    obtidos = _trechos()
    divergentes = [
        f"{rede} {nivel}"
        for rede in REDES
        for nivel in referencia["var_series_trecho0"][rede]
        if obtidos[rede][nivel] != referencia["var_series_trecho0"][rede][nivel]
    ]
    assert not divergentes, f"trecho 0 diferente da referencia do 0.2.0: {divergentes}"
