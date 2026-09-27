"""Retratos: o estado treinado de um modelo caro num ponto de retreino (M1.5b, RF-01).

Um retrato por ponto de retreino -- a posicao 0 (o treino inicial) e o inicio de cada trecho
seguinte, em retornos de teste. Com o retrato de cada ponto, a serie inteira do backtest sai
por previsao, sem treino; com os retratos de um prefixo, so o que falta e treinado.

O formato do `payload` e um npz (`numpy.savez`, sem pickle):

- redes (`lstm`, `gru`, `garchnet`): `w_0`..`w_n`, os pesos na ordem de
  `model.get_weights()`; `o_0`..`o_m`, as variaveis do otimizador na ordem de
  `optimizer.variables`; e `config`, o json `{"units": int, "n_layers": int}`.
  A ordem e reconstruida pelo SUFIXO INTEIRO, nunca pela ordem das chaves: em ordem
  lexicografica `o_10` vem antes de `o_2`, e um LSTM de uma camada ja tem 12 variaveis;
- `caviar`: `beta`, float64 com 3 elementos.

So numpy e json. Este modulo NAO importa TensorFlow nem Keras, nem no topo nem dentro de
funcao: o runner o importa, e uma instalacao `engine[traditional,garch]` precisa continuar
importando o runner (RF-11, V-18). Quem le e escreve pesos no modelo e o `_quantile_nn.py`,
que ja importa o TensorFlow -- e e por isso que a logica do formato mora aqui, verificada
pelo mypy, e nao la, na isencao de tipos da D-21.
"""

from __future__ import annotations

import io
import json
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

_WEIGHT = "w_"
_OPTIMIZER = "o_"
_CONFIG = "config"
_BETA = "beta"


@dataclass(frozen=True)
class Snapshot:
    #: 0, 252, 504, ... em retornos de teste
    position: int
    #: o estado treinado, no formato do docstring do modulo
    payload: bytes


@dataclass(frozen=True)
class NetworkState:
    """O que o retrato de uma rede guarda, ja na ordem de restaurar."""

    weights: list[np.ndarray]
    optimizer_variables: list[np.ndarray]
    units: int
    n_layers: int


def pack_arrays(arrays: dict[str, np.ndarray]) -> bytes:
    """npz sem pickle. Os BYTES nao sao deterministicos -- o zip grava a hora de cada
    entrada --; o que e deterministico sao os arrays. Compare por `unpack_arrays`."""
    buffer = io.BytesIO()
    np.savez(buffer, allow_pickle=False, **arrays)
    return buffer.getvalue()


def unpack_arrays(payload: bytes) -> dict[str, np.ndarray]:
    with np.load(io.BytesIO(payload), allow_pickle=False) as arquivo:
        return {nome: arquivo[nome] for nome in arquivo.files}


def _ordered(arrays: dict[str, np.ndarray], prefix: str) -> list[np.ndarray]:
    """Os arrays de `prefix`, na ordem do SUFIXO INTEIRO -- `o_2` antes de `o_10`."""
    indices = sorted(
        int(nome[len(prefix) :]) for nome in arrays if nome.startswith(prefix)
    )
    if indices != list(range(len(indices))):
        raise ValueError(
            f"retrato com indices de '{prefix}' fora de sequencia: {indices}"
        )
    return [arrays[f"{prefix}{i}"] for i in indices]


def pack_network(
    weights: Sequence[np.ndarray],
    optimizer_variables: Sequence[np.ndarray],
    units: int,
    n_layers: int,
) -> bytes:
    arrays: dict[str, np.ndarray] = {}
    for i, peso in enumerate(weights):
        arrays[f"{_WEIGHT}{i}"] = np.asarray(peso)
    for i, variavel in enumerate(optimizer_variables):
        arrays[f"{_OPTIMIZER}{i}"] = np.asarray(variavel)
    arrays[_CONFIG] = np.array(
        json.dumps({"units": int(units), "n_layers": int(n_layers)})
    )
    return pack_arrays(arrays)


def unpack_network(payload: bytes) -> NetworkState:
    arrays = unpack_arrays(payload)
    config = json.loads(str(arrays[_CONFIG]))
    return NetworkState(
        weights=_ordered(arrays, _WEIGHT),
        optimizer_variables=_ordered(arrays, _OPTIMIZER),
        units=int(config["units"]),
        n_layers=int(config["n_layers"]),
    )


def pack_beta(beta: np.ndarray) -> bytes:
    return pack_arrays({_BETA: np.asarray(beta, dtype=np.float64)})


def unpack_beta(payload: bytes) -> np.ndarray:
    beta = unpack_arrays(payload)[_BETA]
    if beta.dtype != np.float64 or beta.shape != (3,):
        raise ValueError(f"retrato do caviar com beta {beta.dtype} {beta.shape}")
    return beta
