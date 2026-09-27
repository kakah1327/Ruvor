"""Os retratos: identidade, impressao digital e gravacao (M1.5b, T5), e o calculo
incremental nos dois caminhos (T6).

**A primeira metade** cobre V-07 (as duas metades, **por contagem**), V-08 (os seis
componentes), V-09 (as duas metades) e a borda `position == test_count`. A segunda metade
do V-17 mora em `tests/test_versoes_travadas.py`, que guarda a imagem. Nada nela roda o
motor: os retratos sao fabricados com `pack_beta` sobre um `beta` distinto por posicao, e
comparados pelo que foi desempacotado -- os **bytes** do npz nao sao deterministicos (o zip
grava a hora). O modelo e o `caviar`, um dos quatro caros; os hiperparametros saem do
registry, que e carregado antes de cada teste.

**A segunda metade roda o motor de verdade**, sem substituto: V-02 (com o V-03 dentro),
V-07 levado ao calculo, V-10, V-11, os retratos parciais e a linha de log da tarefa. So o
V-02 roda os quatro modelos caros -- com os nove, porque sao dezoito `risk_result` --, sobre
252 + 503 retornos de teste que crescem um pregao e depois mais um. Os demais testam a
**ligacao** e rodam com `caviar` e **uma** rede (`lstm`), sobre 252 + 254 retornos de teste:
a menor serie que cruza a posicao 252 e ainda tem os precos de indice 504 e 505, que o
V-07 altera. O `run_experiment` e espionado **em `apps.risk.compute`**, o nome que
`run_models` chama, para ler a `var_series` de cada `ModelRunResult`. A contagem de
retratos por (modelo, nivel) e o que decide: a igualdade com o `--full` sozinha nao reprova
um erro de ligacao, porque retreinar sem necessidade da o mesmo numero.

As series sao sinteticas, diarias, com o `adj_close` em seis casas, como em
`test_compute.py`. Nenhum numero esperado vem do codigo sob teste: as posicoes esperadas
sao escritas a mao, e os indices alterados sao `252 + 252` e `252 + 253`, contados aqui.
"""

from __future__ import annotations

import importlib
import logging
import math
import re
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from importlib.metadata import version
from typing import Any

import numpy as np
import pandas as pd
import pytest
from engine import seeding
from engine.experiments.runner import ExperimentResult, run_experiment
from engine.models import load_all_model_modules
from engine.models.ml import caviar as caviar_module
from engine.snapshots import Snapshot, pack_beta, unpack_beta

from apps.assets.models import Asset, CollectionRun, Price
from apps.risk.compute import MODELS, run_compute_risk
from apps.risk.models import ModelSnapshot, RiskResult, RiskRun
from apps.risk.snapshots import (
    SnapshotKey,
    library_versions,
    load_valid,
    save,
)
from apps.risk.tasks import (
    _abrir_execucao,
    _compute_asset_model,
    _fechar_execucao,
    enqueue_compute,
)

pytestmark = pytest.mark.django_db

Q6 = Decimal("0.000001")
AGORA = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
ULTIMO_PREGAO = date(2026, 9, 18)

MODELO = "caviar"
ALPHA = 0.05
JANELA = 252

# 1 + 252 + 600: o periodo de teste tem 600 retornos, e cabem as posicoes 0, 252 e 504
PREGOES_TRES_PONTOS = 1 + JANELA + 600
# 1 + 252 + 504: o periodo de teste tem exatamente 504 retornos -- a borda
PREGOES_NA_BORDA = 1 + JANELA + 504


@pytest.fixture(autouse=True)
def registry() -> Iterator[None]:
    # `load_valid` e `save` leem os hiperparametros de `get_model(nome)()`
    load_all_model_modules()
    yield


def dias_uteis(quantidade: int, fim: date = ULTIMO_PREGAO) -> list[date]:
    datas: list[date] = []
    dia = fim
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    return sorted(datas)


def cria_ativo(ticker: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


def cria_serie(asset: Asset, quantidade: int, *, semente: int = 7) -> None:
    """`quantidade` pregoes, com log-retornos normais de desvio 1% a partir de 100."""
    Price.objects.bulk_create(linhas_da_serie(asset, quantidade, semente=semente))


def linhas_da_serie(asset: Asset, quantidade: int, *, semente: int = 7) -> list[Price]:
    """As linhas de `cria_serie`, sem gravar: o V-02 as grava em tres prefixos."""
    rng = np.random.default_rng(semente)
    coleta = CollectionRun.objects.create(source="teste", started_at=AGORA)
    nivel = 100.0
    valores = [Decimal("100.000000")]
    for retorno in rng.normal(0, 0.01, quantidade - 1):
        nivel *= math.exp(float(retorno))
        valores.append(Decimal(str(nivel)).quantize(Q6))
    return list(
        Price(
            asset=asset,
            date=dia,
            open=adj,
            high=adj,
            low=adj,
            close=adj,
            adj_close=adj,
            volume=1000,
            log_return=None,
            run=coleta,
            updated_at=AGORA,
        )
        for dia, adj in zip(dias_uteis(quantidade), valores, strict=True)
    )


def barras(asset: Asset) -> list[Price]:
    return list(Price.objects.filter(asset=asset).order_by("date"))


def com_serie(ticker: str, quantidade: int) -> tuple[Asset, list[Price]]:
    asset = cria_ativo(ticker)
    cria_serie(asset, quantidade)
    return asset, barras(asset)


def chave(asset: Asset, bars: list[Price], **troca: Any) -> SnapshotKey:
    campos: dict[str, Any] = {
        "asset": asset,
        "seed": 42,
        "engine_version": version("ruvor-engine"),
        "train_window_days": JANELA,
        "first_price_date": bars[0].date,
        "library_versions": library_versions(),
    }
    campos.update(troca)
    return SnapshotKey(**campos)


def beta_de(position: int, variante: float = 0.0) -> np.ndarray:
    return np.array([0.01, 0.9, 0.2], dtype=np.float64) + position + variante


def retrato(position: int, variante: float = 0.0) -> Snapshot:
    return Snapshot(position=position, payload=pack_beta(beta_de(position, variante)))


def posicoes(snaps: list[Snapshot]) -> list[int]:
    return [s.position for s in snaps]


def altera_sexta_casa(bars: list[Price], indice: int) -> None:
    """Soma um na sexta casa do `adj_close` do pregao `indice`, no banco."""
    preco = bars[indice]
    Price.objects.filter(pk=preco.pk).update(adj_close=preco.adj_close + Q6)


# --- V-07: a impressao digital estrita, por contagem ------------------------------------


def _tres_pontos(ticker: str) -> tuple[Asset, list[Price], SnapshotKey]:
    asset, bars = com_serie(ticker, PREGOES_TRES_PONTOS)
    key = chave(asset, bars)
    save(key, MODELO, ALPHA, bars, [retrato(0), retrato(252), retrato(504)])
    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0, 252, 504]
    return asset, bars, key


def test_v07_os_tres_pontos_voltam_com_o_payload_e_o_trained_through() -> None:
    asset, bars, key = _tres_pontos("AAA3")

    validos = load_valid(key, MODELO, ALPHA, bars)

    for snap in validos:
        np.testing.assert_array_equal(unpack_beta(snap.payload), beta_de(snap.position))
    gravados = dict(
        ModelSnapshot.objects.filter(asset=asset).values_list(
            "position", "trained_through"
        )
    )
    # o ultimo preco visto pelo ponto p e o de indice 252 + p
    assert gravados == {
        0: bars[252].date,
        252: bars[504].date,
        504: bars[756].date,
    }


def test_v07a_o_trained_through_de_252_alterado_invalida_252_e_os_seguintes() -> None:
    asset, bars, key = _tres_pontos("AAA3")

    altera_sexta_casa(bars, JANELA + 252)
    bars = barras(asset)

    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0]


def test_v07b_o_pregao_seguinte_ao_trained_through_de_252_preserva_252() -> None:
    asset, bars, key = _tres_pontos("AAA3")

    altera_sexta_casa(bars, JANELA + 253)
    bars = barras(asset)

    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0, 252]


# --- a borda: position == test_count -------------------------------------------------


def test_retrato_na_posicao_igual_a_test_count_nao_e_devolvido() -> None:
    """Com 504 retornos de teste, o retrato da posicao 504 -- gravado por uma rodada mais
    longa -- tem `trained_through` no ultimo pregao e impressao digital que bate, mas nao
    tem trecho nenhum para prever."""
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)
    save(key, MODELO, ALPHA, bars, [retrato(0), retrato(252), retrato(504)])
    assert ModelSnapshot.objects.filter(asset=asset).count() == 3

    assert posicoes(load_valid(key, MODELO, ALPHA, bars)) == [0, 252]


# --- V-08: cada componente da identidade -------------------------------------------------


def _fabricacoes(bars: list[Price]) -> dict[str, dict[str, Any]]:
    versoes = {**library_versions(), "numpy": "0.0.0"}
    return {
        "semente": {"seed": 43},
        "versao do motor": {"engine_version": "0.0.0"},
        "versoes de biblioteca": {
            "library_versions": versoes,
            "library_versions_hash": "f" * 64,
        },
        "hiperparametros": {
            "hyperparameters": {"refit_frequency_days": 252, "n_restarts": 11},
            "hyperparameters_hash": "e" * 64,
        },
        "janela": {"train_window_days": JANELA - 1},
        "primeiro pregao": {"first_price_date": bars[0].date - timedelta(days=1)},
    }


@pytest.mark.parametrize(
    "componente",
    [
        "semente",
        "versao do motor",
        "versoes de biblioteca",
        "hiperparametros",
        "janela",
        "primeiro pregao",
    ],
)
def test_v08_retrato_diferente_so_num_componente_nao_e_reaproveitado_e_o_novo_e_gravado(
    componente: str,
) -> None:
    """O fabricado nasce de uma gravacao com a identidade de agora e tem **um** campo
    trocado depois: e identico em tudo -- inclusive na impressao digital -- menos nele."""
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)
    save(key, MODELO, ALPHA, bars, [retrato(0, variante=0.5)])
    ModelSnapshot.objects.filter(asset=asset).update(**_fabricacoes(bars)[componente])

    assert load_valid(key, MODELO, ALPHA, bars) == []

    save(key, MODELO, ALPHA, bars, [retrato(0)])

    assert ModelSnapshot.objects.filter(asset=asset).count() == 2
    validos = load_valid(key, MODELO, ALPHA, bars)
    assert posicoes(validos) == [0]
    np.testing.assert_array_equal(unpack_beta(validos[0].payload), beta_de(0))


# --- V-09: imutavel e idempotente --------------------------------------------------------


def test_v09_gravar_o_mesmo_retrato_duas_vezes_da_uma_linha_sem_excecao() -> None:
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)
    snap = retrato(0)

    save(key, MODELO, ALPHA, bars, [snap])
    save(key, MODELO, ALPHA, bars, [snap])

    assert ModelSnapshot.objects.filter(asset=asset).count() == 1


def test_v09_mesma_identidade_com_outro_payload_fica_o_primeiro() -> None:
    asset, bars = com_serie("AAA3", PREGOES_NA_BORDA)
    key = chave(asset, bars)

    save(key, MODELO, ALPHA, bars, [retrato(0)])
    save(key, MODELO, ALPHA, bars, [retrato(0, variante=0.5)])

    linha = ModelSnapshot.objects.get(asset=asset)
    np.testing.assert_array_equal(unpack_beta(bytes(linha.payload)), beta_de(0))


# =========================================================================================
# O calculo incremental nos dois caminhos (T6) -- o motor de verdade
# =========================================================================================

# Escritos aqui, e nao importados de `compute.EXPENSIVE`: o esperado nao vem do codigo sob
# teste.
CAROS = ("caviar", "garchnet", "gru", "lstm")
NIVEIS = ("0.0500", "0.0100")

# Os testes de ligacao: um caro barato de treinar e uma rede so.
LIGACAO = ["caviar", "lstm"]
# 1 + 252 + 254: cruza a posicao 252, e os precos de indice 504 e 505 existem
PREGOES_LIGACAO = 1 + JANELA + 254
# 1 + 252 + 503: o V-02 do zero atravessa o ponto 252; +1 chega a 504; +1 cruza 504
PREGOES_V02 = 1 + JANELA + 503

# Os campos que diferem por definicao entre duas execucoes (RF-07). A lista e fechada.
FORA_DO_RESULTADO = {"id", "run", "reused_snapshots", "trained_snapshots"}
FORA_DA_EXECUCAO = {"id", "calculated_at", "finished_at", "full_recompute"}

Par = tuple[int | None, int | None]


class Relogio:
    """Um `now()` que avanca um minuto a cada chamada: `(asset, calculated_at)` e unico."""

    def __init__(self) -> None:
        self.chamadas = 0

    def __call__(self) -> datetime:
        self.chamadas += 1
        return AGORA + timedelta(minutes=self.chamadas)


@pytest.fixture
def motor(monkeypatch: pytest.MonkeyPatch) -> list[ExperimentResult]:
    """Os `ExperimentResult` que o motor devolveu, na ordem: e dali que sai a `var_series`
    inteira, que o `risk_result` nao guarda. O espiao chama o motor de verdade."""
    capturados: list[ExperimentResult] = []

    def capturando(*args: Any, **kwargs: Any) -> ExperimentResult:
        resultado = run_experiment(*args, **kwargs)
        capturados.append(resultado)
        return resultado

    monkeypatch.setattr("apps.risk.compute.run_experiment", capturando)
    return capturados


@pytest.fixture
def fila(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """O duplo do `_enqueue`: guarda o que recebeu e nao fala com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.risk.tasks._enqueue", recebidos.append)
    return recebidos


def calcula(
    motor: list[ExperimentResult],
    modelos: list[str],
    relogio: Relogio,
    *,
    full: bool,
) -> tuple[RiskRun, ExperimentResult]:
    """Uma execucao sincrona sobre `AAA3`: a linha gravada e o que o motor devolveu."""
    antes = len(motor)
    run_compute_risk(["AAA3"], models=modelos, full=full, now=relogio)
    assert len(motor) == antes + 1
    return RiskRun.objects.latest("id"), motor[-1]


def calcula_assincrono(
    fila: list[Any],
    modelos: list[str],
    relogio: Relogio,
    *,
    full: bool,
    seed: int | None = None,
) -> RiskRun:
    """Uma execucao assincrona sobre `AAA3`, seguindo o que foi **enfileirado**: a abertura
    sai da fila do `enqueue_compute`, com os argumentos nomeados, e as tarefas e o fecho,
    do `chord` que a abertura entregou. Sem `seed`, a semente padrao do backend."""
    enqueue_compute(
        ["AAA3"], seed=seed, models=modelos, full=full, calculated_at=relogio()
    )
    (abertura,) = fila
    fila.clear()
    run_id = _abrir_execucao(*abertura.args, **abertura.kwargs)
    assert run_id is not None
    (grupo,) = fila
    fila.clear()
    for tarefa in grupo.tasks:
        _compute_asset_model(*tarefa.args)
    _fechar_execucao([None] * len(grupo.tasks), *grupo.body.args)
    return RiskRun.objects.get(pk=run_id)


def contagens(run: RiskRun) -> dict[tuple[str, str], Par]:
    return {
        (r.model_name, str(r.alpha)): (r.reused_snapshots, r.trained_snapshots)
        for r in run.results.all()
    }


def esperado(modelos: list[str], par: Par) -> dict[tuple[str, str], Par]:
    """`par` nos caros, nulo nos baratos -- "nao se aplica", nao zero (RF-09)."""
    return {
        (nome, nivel): par if nome in CAROS else (None, None)
        for nome in modelos
        for nivel in NIVEIS
    }


def resultados(run: RiskRun) -> list[dict[str, object]]:
    return [
        {
            f.name: getattr(r, f.attname)
            for f in RiskResult._meta.fields
            if f.name not in FORA_DO_RESULTADO
        }
        for r in run.results.order_by("model_name", "alpha")
    ]


def manifesto(run: RiskRun) -> dict[str, object]:
    return {
        f.name: getattr(run, f.attname)
        for f in RiskRun._meta.fields
        if f.name not in FORA_DA_EXECUCAO
    }


def series(resultado: ExperimentResult) -> dict[tuple[str, float], pd.Series]:
    saida: dict[tuple[str, float], pd.Series] = {}
    for r in resultado.runs:
        if r.model_name in CAROS:
            assert r.error is None and r.estimate is not None, r.error
            saida[(r.model_name, r.alpha)] = r.estimate.var_series
    return saida


def confere_igual_ao_full(
    incremental: tuple[RiskRun, ExperimentResult],
    completo: tuple[RiskRun, ExperimentResult],
    modelos: list[str],
) -> None:
    """RF-07: a `var_series` inteira de cada (modelo caro, nivel), ponto a ponto e com
    igualdade exata, e as linhas gravadas campo a campo, fora os excluidos."""
    (run_inc, res_inc), (run_full, res_full) = incremental, completo
    assert (run_inc.full_recompute, run_full.full_recompute) == (False, True)
    serie_inc, serie_full = series(res_inc), series(res_full)
    caros = sorted(set(modelos) & set(CAROS))
    assert sorted(serie_inc) == sorted(serie_full)
    assert len(serie_inc) == 2 * len(caros)
    for chave, valores in serie_inc.items():
        pd.testing.assert_series_equal(valores, serie_full[chave], check_exact=True)
    assert manifesto(run_inc) == manifesto(run_full)
    linhas = resultados(run_inc)
    assert len(linhas) == 2 * len(modelos)
    assert linhas == resultados(run_full)


def espioes_de_treino(m: pytest.MonkeyPatch) -> tuple[list[int], list[int]]:
    """V-03: cada chamada de `keras.Model.fit` -- o treino e o retreino das redes, **nao**
    o `VaRModel.fit`, que roda sempre -- e de `_fit_beta`. Os dois chamam o original.

    O Keras entra por `importlib`: ele nao publica `py.typed`, e o `mypy` estrito do backend
    reprovaria o `import`."""
    keras = importlib.import_module("keras")
    fit_original = keras.Model.fit
    beta_original = caviar_module._fit_beta
    fits: list[int] = []
    betas: list[int] = []

    def fit_espiao(self: Any, *args: Any, **kwargs: Any) -> Any:
        fits.append(1)
        return fit_original(self, *args, **kwargs)

    def beta_espiao(*args: Any, **kwargs: Any) -> Any:
        betas.append(1)
        return beta_original(*args, **kwargs)

    m.setattr(keras.Model, "fit", fit_espiao)
    m.setattr("engine.models.ml.caviar._fit_beta", beta_espiao)
    return fits, betas


def espioes_de_posicao(
    m: pytest.MonkeyPatch,
) -> tuple[list[int], list[tuple[float, int]]]:
    """As posicoes treinadas. Nas redes, pela semeadura: `apply()` abre o treino inicial
    (posicao 0) e `apply(position=p)`, cada retreino. No `caviar`, pelo tamanho da serie que
    `_fit_beta` recebe: `JANELA + p` retornos. Os dois chamam o original -- um espiao que
    substituisse a semeadura deixaria de semear."""
    apply_original = seeding.apply
    beta_original = caviar_module._fit_beta
    redes: list[int] = []
    betas: list[tuple[float, int]] = []

    def apply_espiao(position: int = 0) -> None:
        redes.append(position)
        apply_original(position)

    def beta_espiao(returns: Any, f0: float, alpha: float, seed: int) -> Any:
        betas.append((alpha, len(returns) - JANELA))
        return beta_original(returns, f0, alpha, seed=seed)

    m.setattr("engine.seeding.apply", apply_espiao)
    m.setattr("engine.models.ml.caviar._fit_beta", beta_espiao)
    return redes, betas


# --- V-02 e V-03: incremental igual ao do zero, e o dia comum nao treina -----------------


def test_v02_incremental_igual_ao_full_e_o_dia_comum_nao_treina(
    motor: list[ExperimentResult], monkeypatch: pytest.MonkeyPatch
) -> None:
    """V-02 com os nove, os quatro caros de verdade; o V-03 e afirmado no passo +1.

    **Em cada passo, o incremental roda primeiro e o `--full` depois**: ao contrario, o
    `--full` gravaria o retrato da posicao 504 e o incremental o reaproveitaria, sem
    exercer o retreino a partir de retrato restaurado. A contagem e o que pega "guardar so
    o ultimo retrato": sem o da posicao 0, tudo e retreinado e a igualdade se mantem.
    """
    asset = cria_ativo("AAA3")
    linhas = linhas_da_serie(asset, PREGOES_V02 + 2)
    Price.objects.bulk_create(linhas[:PREGOES_V02])
    relogio = Relogio()
    nove = list(MODELS)

    zero, _ = calcula(motor, nove, relogio, full=False)
    assert zero.test_count == 503
    assert contagens(zero) == esperado(nove, (0, 2))  # posicoes 0 e 252

    # +1 pregao: 504 retornos de teste, sem cruzar ponto
    Price.objects.bulk_create(linhas[PREGOES_V02 : PREGOES_V02 + 1])
    with monkeypatch.context() as m:
        fits, betas = espioes_de_treino(m)
        incremental = calcula(motor, nove, relogio, full=False)
    assert incremental[0].test_count == 504
    # V-03: nada treinado nos quatro, e nenhuma chamada de treino
    assert contagens(incremental[0]) == esperado(nove, (2, 0))
    assert (fits, betas) == ([], [])
    completo = calcula(motor, nove, relogio, full=True)
    assert contagens(completo[0]) == esperado(nove, (0, 2))
    confere_igual_ao_full(incremental, completo, nove)

    # +1 pregao: 505 retornos de teste, cruza o ponto 504 -- um retreino, e so ele
    Price.objects.bulk_create(linhas[PREGOES_V02 + 1 :])
    incremental = calcula(motor, nove, relogio, full=False)
    assert incremental[0].test_count == 505
    assert contagens(incremental[0]) == esperado(nove, (2, 1))
    completo = calcula(motor, nove, relogio, full=True)
    assert contagens(completo[0]) == esperado(nove, (0, 3))
    confere_igual_ao_full(incremental, completo, nove)

    # tres pontos por (modelo caro, nivel), cada um gravado uma vez so
    gravados = list(
        ModelSnapshot.objects.values_list("model_name", "alpha", "position")
    )
    assert sorted(gravados) == sorted(
        (nome, Decimal(nivel), posicao)
        for nome in CAROS
        for nivel in NIVEIS
        for posicao in (0, 252, 504)
    )


# --- V-07 levado ao calculo ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("indice", "par", "treinadas"),
    [
        # (a) o `trained_through` de 252: invalida 252 -- reaproveita 0, treina 252
        (JANELA + 252, (1, 1), [252]),
        # (b) o pregao seguinte: 252 continua valendo -- reaproveita os dois
        (JANELA + 253, (2, 0), []),
    ],
    ids=["a-trained-through", "b-pregao-seguinte"],
)
def test_v07_integrado_a_contagem_decide_e_o_numero_e_o_do_full(
    indice: int,
    par: Par,
    treinadas: list[int],
    motor: list[ExperimentResult],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """As contagens -- as colunas e as posicoes que os espioes viram treinar -- pegam um
    erro de ligacao no `compute` (`bars` errados, `load_valid` nao chamada) que a igualdade
    com o `--full` deixaria passar."""
    _, bars = com_serie("AAA3", PREGOES_LIGACAO)
    relogio = Relogio()
    calcula(motor, LIGACAO, relogio, full=False)

    altera_sexta_casa(bars, indice)
    with monkeypatch.context() as m:
        redes, betas = espioes_de_posicao(m)
        incremental = calcula(motor, LIGACAO, relogio, full=False)

    assert contagens(incremental[0]) == esperado(LIGACAO, par)
    assert sorted(redes) == sorted(treinadas * 2)  # a `lstm`, nos dois niveis
    assert sorted(betas) == sorted(
        (alpha, posicao) for alpha in (0.05, 0.01) for posicao in treinadas
    )
    completo = calcula(motor, LIGACAO, relogio, full=True)
    confere_igual_ao_full(incremental, completo, LIGACAO)


# --- V-10: o `--full` nao le retratos, nos dois caminhos ---------------------------------


def test_v10_full_nao_le_retratos_nem_duplica_nos_dois_caminhos(
    motor: list[ExperimentResult], fila: list[Any]
) -> None:
    com_serie("AAA3", PREGOES_LIGACAO)
    relogio = Relogio()
    primeira, _ = calcula(motor, LIGACAO, relogio, full=False)
    assert contagens(primeira) == esperado(LIGACAO, (0, 2))
    assert ModelSnapshot.objects.count() == 2 * 2 * 2  # modelos x niveis x posicoes

    sincrona, _ = calcula(motor, LIGACAO, relogio, full=True)

    assert sincrona.full_recompute is True
    assert contagens(sincrona) == esperado(LIGACAO, (0, 2))
    assert ModelSnapshot.objects.count() == 8

    # a tarefa por (ativo, modelo) le o `--full` da `risk_run`
    assincrona = calcula_assincrono(fila, LIGACAO, relogio, full=True)

    assert assincrona.full_recompute is True
    assert contagens(assincrona) == esperado(LIGACAO, (0, 2))
    assert ModelSnapshot.objects.count() == 8


# --- a semente da tarefa vem da `risk_run` ---------------------------------------------


def test_tarefa_monta_a_identidade_com_a_semente_da_execucao(fila: list[Any]) -> None:
    """A `SnapshotKey` da tarefa por (ativo, modelo) sai da `risk_run`: com os retratos da
    semente 42 no banco, uma execucao assincrona com a semente 7 nao os reaproveita e grava
    os seus. Uma tarefa que montasse a chave com a semente padrao reaproveitaria os dois."""
    com_serie("AAA3", PREGOES_LIGACAO)
    relogio = Relogio()
    modelos = [MODELO]
    primeira = calcula_assincrono(fila, modelos, relogio, full=False, seed=42)
    assert primeira.seed == 42
    assert contagens(primeira) == esperado(modelos, (0, 2))
    assert sorted(
        ModelSnapshot.objects.values_list("seed", "alpha", "position")
    ) == sorted(
        (42, Decimal(nivel), posicao) for nivel in NIVEIS for posicao in (0, 252)
    )

    segunda = calcula_assincrono(fila, modelos, relogio, full=False, seed=7)

    assert segunda.seed == 7
    assert contagens(segunda) == esperado(modelos, (0, 2))
    assert sorted(
        ModelSnapshot.objects.filter(seed=7).values_list("alpha", "position")
    ) == sorted((Decimal(nivel), posicao) for nivel in NIVEIS for posicao in (0, 252))
    assert ModelSnapshot.objects.count() == 8


# --- V-11: o manifesto diz de onde veio, por nivel ----------------------------------------


def test_v11_o_manifesto_por_nivel_nos_quatro_casos_e_o_log_da_tarefa(
    motor: list[ExperimentResult],
    fila: list[Any],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Os quatro casos do RF-09, com os dois niveis do `caviar` **divergindo**: numa
    primeira rodada o retreino de 252 levanta so no de 1%, que fica com o retrato parcial
    da posicao 0. Contagem indexada por modelo, e nao por (modelo, nivel), daria o mesmo par
    aos dois. O `--full` (0, todos) e o V-10; aqui, `full_recompute` falso nos dois caminhos.
    """
    com_serie("AAA3", PREGOES_LIGACAO)
    relogio = Relogio()
    modelos = ["caviar", "parametric"]
    beta_original = caviar_module._fit_beta

    def quebra_no_retreino(returns: Any, f0: float, alpha: float, seed: int) -> Any:
        if alpha == 0.01 and len(returns) > JANELA:
            raise RuntimeError("retreino quebrado de proposito")
        return beta_original(returns, f0, alpha, seed=seed)

    with monkeypatch.context() as m:
        m.setattr("engine.models.ml.caviar._fit_beta", quebra_no_retreino)
        primeira, _ = calcula(motor, modelos, relogio, full=False)

    assert primeira.full_recompute is False
    assert contagens(primeira) == {
        ("caviar", "0.0500"): (0, 2),  # do zero
        ("caviar", "0.0100"): (None, None),  # o modelo falhou
        ("parametric", "0.0500"): (None, None),  # barato
        ("parametric", "0.0100"): (None, None),
    }
    falho = primeira.results.get(model_name="caviar", alpha=Decimal("0.0100"))
    assert falho.error == "retreino quebrado de proposito"
    assert sorted(ModelSnapshot.objects.values_list("alpha", "position")) == sorted(
        [(Decimal("0.0100"), 0), (Decimal("0.0500"), 0), (Decimal("0.0500"), 252)]
    )

    caplog.set_level(logging.INFO, logger="apps.risk.tasks")
    segunda = calcula_assincrono(fila, modelos, relogio, full=False)

    assert segunda.full_recompute is False
    assert contagens(segunda) == {
        ("caviar", "0.0500"): (2, 0),  # a partir de retratos
        ("caviar", "0.0100"): (1, 1),  # o parcial, e o que faltava
        ("parametric", "0.0500"): (None, None),
        ("parametric", "0.0100"): (None, None),
    }
    linhas = [r.getMessage() for r in caplog.records if r.name == "apps.risk.tasks"]
    assert _uma_linha(
        linhas,
        f"risco AAA3 run={segunda.id} modelo=caviar alpha=0.05 2/0 alpha=0.01 1/1",
    )
    assert _uma_linha(
        linhas,
        f"risco AAA3 run={segunda.id} modelo=parametric alpha=0.05 -/- alpha=0.01 -/-",
    )


def _uma_linha(linhas: list[str], inicio: str) -> bool:
    """Exatamente uma linha de log comeca com `inicio` e termina na duracao, `N.NNs`."""
    padrao = re.compile(re.escape(inicio) + r" \d+\.\d{2}s")
    return sum(1 for linha in linhas if padrao.fullmatch(linha)) == 1


# --- os retratos parciais ------------------------------------------------------------------


def test_retreino_tardio_que_levanta_grava_os_retratos_anteriores_e_o_par_de_erro(
    motor: list[ExperimentResult],
    fila: list[Any],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """RF-02 pelo caminho assincrono: o retreino de 252 levanta nos dois modelos e nos dois
    niveis. O par de erro e gravado -- `error` preenchido, numeros e contagens nulos --, os
    retratos da posicao 0 ficam no banco, e a rodada seguinte os reaproveita."""
    com_serie("AAA3", PREGOES_LIGACAO)
    relogio = Relogio()
    apply_original = seeding.apply
    beta_original = caviar_module._fit_beta

    def apply_quebra(position: int = 0) -> None:
        if position > 0:
            raise RuntimeError("retreino da rede quebrado de proposito")
        apply_original(position)

    def beta_quebra(returns: Any, f0: float, alpha: float, seed: int) -> Any:
        if len(returns) > JANELA:
            raise RuntimeError("retreino do caviar quebrado de proposito")
        return beta_original(returns, f0, alpha, seed=seed)

    caplog.set_level(logging.INFO, logger="apps.risk.tasks")
    with monkeypatch.context() as m:
        m.setattr("engine.seeding.apply", apply_quebra)
        m.setattr("engine.models.ml.caviar._fit_beta", beta_quebra)
        run = calcula_assincrono(fila, LIGACAO, relogio, full=False)

    erros = {
        "lstm": "retreino da rede quebrado de proposito",
        "caviar": "retreino do caviar quebrado de proposito",
    }
    linhas = list(run.results.all())
    assert len(linhas) == 4
    for linha in linhas:
        assert linha.error == erros[linha.model_name]
        assert (linha.var_latest, linha.adequate) == (None, None)
        assert (linha.reused_snapshots, linha.trained_snapshots) == (None, None)
    assert sorted(
        ModelSnapshot.objects.values_list("model_name", "alpha", "position")
    ) == sorted((nome, Decimal(nivel), 0) for nome in LIGACAO for nivel in NIVEIS)
    mensagens = [r.getMessage() for r in caplog.records if r.name == "apps.risk.tasks"]
    for nome in LIGACAO:
        assert _uma_linha(
            mensagens,
            f"risco AAA3 run={run.id} modelo={nome} alpha=0.05 -/- alpha=0.01 -/-",
        )

    seguinte, _ = calcula(motor, LIGACAO, relogio, full=False)

    assert contagens(seguinte) == esperado(LIGACAO, (1, 1))
