"""O contrato de retratos do motor (M1.5b): restaurar e expor.

Com o motor REAL, sem substituto. A serie tem 252 retornos de treino e 505 de teste: o
teste atravessa os pontos de retreino 252 e 504, e o 504 ainda tem um pregao para prever.

- igualdade no motor (a parte do V-02 que e do motor, RF-07): a `var_series` de uma
  instancia NOVA que restaura os retratos do calculo do zero e igual, ponto a ponto, a do
  calculo do zero -- as tres redes e o `caviar`, nos dois niveis --, e tambem quando so um
  prefixo dos retratos e restaurado e o resto e treinado (RF-06);
- V-05 (parte): o `caviar` restaurado da a mesma serie do `caviar` sem retratos;
- V-06: o retreino a partir do retrato da posicao 0, carregado em PROCESSO NOVO, e igual,
  bit a bit, ao do calculo do zero neste processo -- pesos, otimizador e serie;
- V-18: em subprocesso, com `tensorflow` e `keras` bloqueados, `engine.snapshots` e
  `engine.experiments.runner` importam;
- V-19: o mesmo retrato da posicao 0, retreinado em 252 com duas sementes da execucao
  diferentes, da pesos e trecho 1 diferentes;
- parciais (RF-02): um retreino que levanta em 504 deixa os retratos 0 e 252 no modelo e
  no `ModelRunResult` do runner, junto com o `error`.

Os bytes de um `payload` NAO sao deterministicos (o zip do npz grava a hora); a
comparacao e sempre pelos arrays desempacotados, dtype incluido.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import engine
from engine import seeding
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, run_experiment
from engine.models import get_model, load_all_model_modules
from engine.snapshots import (
    Snapshot,
    pack_network,
    unpack_arrays,
    unpack_network,
)

REDES = ("lstm", "gru", "garchnet")
CAROS = (*REDES, "caviar")
ALPHAS = (0.05, 0.01)
TREINO = 252
TESTE = 505
POSICOES = [0, 252, 504]
#: `REFIT_FREQUENCY_DAYS - WINDOW`: a janela i preve o dia WINDOW + i; o retreino em p usa
#: as janelas ate TREINO - WINDOW + p
JANELAS_NO_RETREINO_504 = TREINO - 20 + 504

DoZero = dict[tuple[str, float], tuple[pd.Series, list[Snapshot]]]


def _retornos() -> pd.Series:
    rng = np.random.default_rng(2026)
    valores = rng.normal(0.0, 0.01, TREINO + TESTE)
    return pd.Series(valores, index=pd.bdate_range("2020-01-01", periods=len(valores)))


def _treino_e_teste() -> tuple[pd.Series, pd.Series]:
    retornos = _retornos()
    return retornos.iloc[:TREINO], retornos.iloc[TREINO:]


def _mesmos_arrays(a: Snapshot, b: Snapshot) -> bool:
    if a.position != b.position:
        return False
    x, y = unpack_arrays(a.payload), unpack_arrays(b.payload)
    return x.keys() == y.keys() and all(
        x[k].dtype == y[k].dtype and np.array_equal(x[k], y[k]) for k in x
    )


@pytest.fixture(autouse=True)
def semente_padrao() -> Iterator[None]:
    seeding.configure(seeding.DEFAULT_SEED)
    yield
    seeding.configure(seeding.DEFAULT_SEED)


@pytest.fixture(scope="module")
def do_zero() -> DoZero:
    """O calculo do zero, uma instancia por modelo e os dois niveis nela, como o runner."""
    load_all_model_modules()
    seeding.configure(seeding.DEFAULT_SEED)
    treino, teste = _treino_e_teste()
    saida: DoZero = {}
    for nome in CAROS:
        modelo = get_model(nome)().fit(treino)
        for alpha in ALPHAS:
            serie = modelo.estimate_var(teste, alpha=alpha).var_series
            saida[(nome, alpha)] = (serie, modelo.snapshots(alpha))
    return saida


def _restaurado(nome: str, alpha: float, retratos: list[Snapshot], teste=None):
    """Instancia NOVA, ajustada no mesmo treino, com `retratos` restaurados."""
    load_all_model_modules()
    treino, teste_padrao = _treino_e_teste()
    modelo = get_model(nome)().fit(treino)
    modelo.restore(alpha, retratos)
    serie = modelo.estimate_var(
        teste_padrao if teste is None else teste, alpha=alpha
    ).var_series
    return modelo, serie


# --- o formato ---------------------------------------------------------------------------


def test_a_ordem_do_npz_e_a_do_sufixo_inteiro_e_nao_a_lexicografica() -> None:
    """Doze variaveis de otimizador, como um LSTM de uma camada: em ordem lexicografica
    `o_10` viria antes de `o_2`."""
    pesos = [np.full(2, float(i)) for i in range(12)]
    otimizador = [np.full(3, float(100 + i)) for i in range(12)]
    estado = unpack_network(pack_network(pesos, otimizador, 32, 2))
    assert [float(p[0]) for p in estado.weights] == [float(i) for i in range(12)]
    assert [float(v[0]) for v in estado.optimizer_variables] == [
        float(100 + i) for i in range(12)
    ]
    assert (estado.units, estado.n_layers) == (32, 2)


def test_o_payload_nao_carrega_pickle() -> None:
    with pytest.raises(ValueError):
        pack_network([np.array([object()], dtype=object)], [], 16, 1)


# --- as posicoes ---------------------------------------------------------------------------


@pytest.mark.parametrize("nome", CAROS)
@pytest.mark.parametrize("alpha", ALPHAS)
def test_o_calculo_do_zero_expoe_um_retrato_por_ponto_de_retreino(
    nome: str, alpha: float, do_zero: DoZero
) -> None:
    _, retratos = do_zero[(nome, alpha)]
    assert [r.position for r in retratos] == POSICOES


# --- igualdade no motor (V-02, parte do motor) e V-05 (parte) -------------------------------


@pytest.mark.parametrize("nome", CAROS)
@pytest.mark.parametrize("alpha", ALPHAS)
def test_restaurar_todos_os_retratos_da_a_mesma_serie(
    nome: str, alpha: float, do_zero: DoZero
) -> None:
    """Igualdade no motor; no `caviar`, e o V-05 (parte)."""
    serie_zero, retratos = do_zero[(nome, alpha)]
    modelo, serie = _restaurado(nome, alpha, retratos)

    pd.testing.assert_series_equal(serie, serie_zero, check_exact=True)
    # nada treinado: o que sai e exatamente o que entrou
    assert modelo.snapshots(alpha) == retratos


@pytest.mark.parametrize("nome", CAROS)
@pytest.mark.parametrize("alpha", ALPHAS)
def test_restaurar_um_prefixo_e_treinar_o_resto_da_a_mesma_serie(
    nome: str, alpha: float, do_zero: DoZero
) -> None:
    """O caminho incremental (RF-06): 0 e 252 restaurados, 504 treinado."""
    serie_zero, retratos = do_zero[(nome, alpha)]
    modelo, serie = _restaurado(nome, alpha, retratos[:2])

    pd.testing.assert_series_equal(serie, serie_zero, check_exact=True)
    novos = modelo.snapshots(alpha)
    assert [r.position for r in novos] == POSICOES
    assert all(_mesmos_arrays(a, b) for a, b in zip(novos, retratos, strict=True))


@pytest.mark.parametrize("nome", ["lstm", "caviar"])
def test_retrato_de_posicao_que_a_serie_nao_alcanca_e_ignorado(
    nome: str, do_zero: DoZero
) -> None:
    """Uma serie de 300 retornos de teste nao chega ao ponto 504: o retrato dele nao e
    restaurado nem devolvido."""
    alpha = 0.05
    serie_zero, retratos = do_zero[(nome, alpha)]
    _, teste = _treino_e_teste()
    modelo, serie = _restaurado(nome, alpha, retratos, teste=teste.iloc[:300])

    pd.testing.assert_series_equal(serie, serie_zero.iloc[:300], check_exact=True)
    assert modelo.snapshots(alpha) == retratos[:2]


# --- V-06: a retomada entre processos -------------------------------------------------------

_SONDA_V06 = """
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from engine import seeding
from engine.models import get_model, load_all_model_modules
from engine.snapshots import Snapshot

pasta = Path(sys.argv[1])
treino_n = int(sys.argv[2])
valores = np.load(pasta / "retornos.npy")
retornos = pd.Series(valores, index=pd.bdate_range("2020-01-01", periods=len(valores)))

load_all_model_modules()
seeding.configure(seeding.DEFAULT_SEED)
for arquivo in sorted(pasta.glob("entrada_*.bin")):
    _, nome, alpha = arquivo.stem.split("_")
    modelo = get_model(nome)().fit(retornos.iloc[:treino_n])
    modelo.restore(float(alpha), [Snapshot(0, arquivo.read_bytes())])
    serie = modelo.estimate_var(retornos.iloc[treino_n:], alpha=float(alpha)).var_series
    np.save(pasta / f"serie_{nome}_{alpha}.npy", serie.to_numpy())
    for retrato in modelo.snapshots(float(alpha)):
        (pasta / f"saida_{nome}_{alpha}_{retrato.position}.bin").write_bytes(
            retrato.payload
        )
"""


@pytest.fixture(scope="module")
def processo_novo(do_zero: DoZero, tmp_path_factory) -> Path:
    """Um subprocesso so, para as tres redes e os dois niveis: carrega o retrato da
    posicao 0 do calculo do zero e retreina 252 e 504."""
    pasta = tmp_path_factory.mktemp("v06")
    np.save(pasta / "retornos.npy", _retornos().to_numpy())
    for nome in REDES:
        for alpha in ALPHAS:
            _, retratos = do_zero[(nome, alpha)]
            (pasta / f"entrada_{nome}_{alpha}.bin").write_bytes(retratos[0].payload)
    saida = subprocess.run(
        [sys.executable, "-c", _SONDA_V06, str(pasta), str(TREINO)],
        capture_output=True,
        text=True,
    )
    # o fim do stderr diz POR QUE o processo novo nao retomou
    assert saida.returncode == 0, saida.stderr[-3000:]
    return pasta


@pytest.mark.parametrize("nome", REDES)
@pytest.mark.parametrize("alpha", ALPHAS)
def test_v06_retreino_em_processo_novo_e_igual_bit_a_bit(
    nome: str, alpha: float, do_zero: DoZero, processo_novo: Path
) -> None:
    serie_zero, retratos = do_zero[(nome, alpha)]

    serie = np.load(processo_novo / f"serie_{nome}_{alpha}.npy")
    assert np.array_equal(serie, serie_zero.to_numpy()), "serie diferente"

    for retrato in retratos[1:]:
        payload = (
            processo_novo / f"saida_{nome}_{alpha}_{retrato.position}.bin"
        ).read_bytes()
        assert _mesmos_arrays(Snapshot(retrato.position, payload), retrato), (
            f"pesos ou otimizador diferentes na posicao {retrato.position}"
        )


# --- V-18: o TensorFlow nao entra por snapshots.py ----------------------------------------

_BLOQUEIO_TF = """
import sys
class _Bloqueio:
    def find_spec(self, nome, caminho=None, alvo=None):
        if nome.split(".")[0] in {"tensorflow", "keras"}:
            raise ImportError("bloqueado para o teste")
        return None
sys.meta_path.insert(0, _Bloqueio())

for proibido in ("tensorflow", "keras"):
    try:
        __import__(proibido)
    except ImportError:
        pass
    else:
        raise SystemExit(f"o bloqueador nao bloqueou {proibido}")

import engine.snapshots
import engine.experiments.runner
"""


def test_v18_snapshots_e_runner_importam_sem_tensorflow_e_keras() -> None:
    saida = subprocess.run(
        [sys.executable, "-c", _BLOQUEIO_TF], capture_output=True, text=True
    )
    assert saida.returncode == 0, saida.stderr


def test_v18_snapshots_nao_importa_tensorflow_nem_keras_nem_dentro_de_funcao() -> None:
    """O subprocesso so pega import executado; import dentro de funcao so a varredura
    estatica pega (aprendizados, "Import diferido escapa")."""
    fonte = (Path(engine.__file__).parent / "snapshots.py").read_text(encoding="utf-8")
    achados = []
    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.Import):
            nomes = [a.name.split(".")[0] for a in no.names]
        elif isinstance(no, ast.ImportFrom):
            nomes = [(no.module or "").split(".")[0]]
        else:
            continue
        achados += [n for n in nomes if n in {"tensorflow", "keras"}]
    assert not achados


# --- V-19: a semente do retreino deriva da semente da execucao ----------------------------


def test_v19_o_mesmo_retrato_com_sementes_diferentes_retreina_diferente(
    do_zero: DoZero,
) -> None:
    alpha = 0.05
    _, retratos = do_zero[("lstm", alpha)]

    resultados = []
    for semente in (7, 8):
        seeding.configure(semente)
        modelo, serie = _restaurado("lstm", alpha, retratos[:1])
        resultados.append((modelo.snapshots(alpha), serie))
    (retratos_a, serie_a), (retratos_b, serie_b) = resultados

    # o mesmo ponto de partida: o trecho 0 e o mesmo
    assert np.array_equal(serie_a.iloc[:252], serie_b.iloc[:252])
    # e o retreino em 252 diverge -- pesos e trecho 1
    pesos_a = unpack_network(retratos_a[1].payload).weights
    pesos_b = unpack_network(retratos_b[1].payload).weights
    assert any(not np.array_equal(a, b) for a, b in zip(pesos_a, pesos_b, strict=True))
    assert not np.array_equal(serie_a.iloc[252:504], serie_b.iloc[252:504])


# --- parciais (RF-02) ---------------------------------------------------------------------


@pytest.fixture
def retreino_de_504_levanta(monkeypatch) -> None:
    """O `model.fit` das redes levanta no retreino de 504, e so nele."""
    from tensorflow import keras

    original = keras.Model.fit

    def fit(self, x=None, *args, **kwargs):
        if x is not None and len(x) == JANELAS_NO_RETREINO_504:
            raise RuntimeError("retreino de 504 falhou (substituto do teste)")
        return original(self, x, *args, **kwargs)

    monkeypatch.setattr(keras.Model, "fit", fit)


def test_parciais_o_modelo_devolve_os_pontos_anteriores_a_falha(
    do_zero: DoZero, retreino_de_504_levanta
) -> None:
    alpha = 0.05
    _, retratos = do_zero[("lstm", alpha)]
    treino, teste = _treino_e_teste()
    modelo = get_model("lstm")().fit(treino)
    modelo.restore(alpha, retratos[:1])

    with pytest.raises(RuntimeError, match="retreino de 504"):
        modelo.estimate_var(teste, alpha=alpha)

    parciais = modelo.snapshots(alpha)
    assert [r.position for r in parciais] == [0, 252]
    # o 252 foi TREINADO aqui, e e o mesmo do calculo do zero
    assert _mesmos_arrays(parciais[1], retratos[1])


class _PrecoFixo:
    def __init__(self, precos: pd.DataFrame) -> None:
        self._precos = precos

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        return self._precos.copy()


def test_parciais_o_runner_leva_o_erro_e_os_retratos(
    do_zero: DoZero, retreino_de_504_levanta
) -> None:
    load_all_model_modules()
    load_all_backtest_modules()
    _, retratos = do_zero[("lstm", 0.05)]
    retornos = _retornos()
    indice = pd.bdate_range("2019-12-31", periods=len(retornos) + 1)
    precos = pd.DataFrame(
        {"close": 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(retornos)]))},
        index=indice,
    )
    config = ExperimentConfig(
        ticker="TESTE3",
        start="2019-12-31",
        end="2023-01-01",
        model_names=["lstm"],
        backtest_names=["kupiec"],
        alphas=[0.05],
        train_window_days=TREINO,
        snapshots={("lstm", 0.05): retratos[:1]},
    )

    (run,) = run_experiment(config, provider=_PrecoFixo(precos)).runs

    assert run.error is not None and "retreino de 504" in run.error
    assert run.estimate is None
    assert [r.position for r in run.snapshots] == [0, 252]


def test_parciais_o_caviar_devolve_os_pontos_anteriores_a_falha(
    do_zero: DoZero, monkeypatch
) -> None:
    from engine.models.ml import caviar

    alpha = 0.05
    _, retratos = do_zero[("caviar", alpha)]
    original = caviar._fit_beta

    def fit_beta(returns, f0, alpha_, seed):
        if seed == int(alpha_ * 10000) + 504:
            raise RuntimeError("reajuste de 504 falhou (substituto do teste)")
        return original(returns, f0, alpha_, seed)

    monkeypatch.setattr(caviar, "_fit_beta", fit_beta)
    treino, teste = _treino_e_teste()
    modelo = get_model("caviar")().fit(treino)

    with pytest.raises(RuntimeError, match="reajuste de 504"):
        modelo.estimate_var(teste, alpha=alpha)

    parciais = modelo.snapshots(alpha)
    assert [r.position for r in parciais] == [0, 252]
    assert all(
        _mesmos_arrays(a, b) for a, b in zip(parciais, retratos[:2], strict=True)
    )
