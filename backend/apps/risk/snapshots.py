"""A identidade, a impressao digital e a gravacao dos retratos (M1.5b, RF-02, RF-03).

Um retrato so e reaproveitado se **tudo** o que o produziu for igual ao de agora: o ativo,
o modelo, o nivel e a posicao; a semente e a versao do motor; as versoes das seis
bibliotecas que calculam; os hiperparametros; a janela de treino e o primeiro pregao; e a
impressao digital dos precos que o treinaram. `load_valid` compara os onze -- nao so a
impressao digital.

**A identidade vem de parametros explicitos** (`SnapshotKey`), nao de uma `RiskRun`: no
caminho sincrono a execucao so nasce depois do calculo, porque `write_risk` cria a linha
ja com o estado final.

**O `trained_through` e literal, e e onde um erro de um passa calado.** O retreino na
posicao *p* usa os retornos ate o indice `train_window_days + p - 1`, e o retorno *i* vem
dos precos *i* e *i + 1* (`log_returns` faz `shift(1)` e `dropna()`). O ultimo **preco**
visto e o de indice `train_window_days + p` em `bars`.

Retrato e imutavel (RF-02): nada aqui faz `update` nem `delete`. A gravacao e idempotente
-- `ignore_conflicts` sobre a unicidade `model_snapshot_identity` --, e uma segunda
gravacao do mesmo retrato nao insere, nao altera e nao levanta.

Os hiperparametros saem de uma instancia nova, `get_model(nome)().hyperparameters`, como
em `compute._row`: e o que o `risk_result` grava. O registry precisa estar carregado
(`load_all_model_modules()`) antes de `load_valid` e `save`.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from importlib.metadata import version
from typing import Any

from django.db import transaction
from django.utils import timezone
from engine.models import get_model
from engine.snapshots import Snapshot

from apps.assets.models import Asset, Price
from apps.risk.models import ModelSnapshot

#: as seis bibliotecas que calculam (RF-03, RF-15), lidas da metadata instalada
LIBRARIES = ("tensorflow", "keras", "numpy", "scipy", "pandas", "arch")

Q4 = Decimal("0.0001")


@dataclass(frozen=True)
class SnapshotKey:
    """A identidade que NAO depende do modelo nem da posicao."""

    asset: Asset
    seed: int
    engine_version: str
    train_window_days: int
    first_price_date: date
    library_versions: dict[str, str]


def library_versions() -> dict[str, str]:
    """As versoes instaladas das seis bibliotecas, lidas da metadata."""
    return {name: version(name) for name in LIBRARIES}


def canonical_hash(obj: Any) -> str:
    """SHA-256, em hexadecimal, do JSON canonico de `obj`."""
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def price_fingerprint(bars: Sequence[Price], through_index: int) -> str:
    """SHA-256 dos precos de `bars[0]` a `bars[through_index]`, inclusive.

    Cada pregao entra com a data em ISO e o `adj_close` convertido para `float` -- a
    precisao que o motor recebe do `SilverPriceProvider` --, serializado com `repr()`.
    Indice fora da serie levanta: a impressao digital de um prefixo que nao existe nao e
    uma impressao digital.
    """
    if not 0 <= through_index < len(bars):
        raise ValueError(f"indice {through_index} fora da serie de {len(bars)} pregoes")
    digest = hashlib.sha256()
    for bar in bars[: through_index + 1]:
        line = f"{bar.date.isoformat()}|{float(bar.adj_close)!r}\n"
        digest.update(line.encode("ascii"))
    return digest.hexdigest()


def trained_through_index(position: int, train_window_days: int) -> int:
    """O indice, em `bars`, do ultimo preco que o ponto na posicao `position` viu."""
    return train_window_days + position


def _alpha(alpha: float) -> Decimal:
    # O `str` e obrigatorio: `Decimal(0.05)` nao e `0.0500`.
    return Decimal(str(alpha)).quantize(Q4)


def _hyperparameters(model_name: str) -> dict[str, Any]:
    return get_model(model_name)().hyperparameters


def load_valid(
    key: SnapshotKey, model_name: str, alpha: float, bars: Sequence[Price]
) -> list[Snapshot]:
    """Os retratos reaproveitaveis, da posicao 0 em diante, em ordem de posicao.

    De `refit_frequency_days` em `refit_frequency_days`; para no primeiro ausente ou
    invalido, e em `position >= test_count`. A borda e literal: com `position ==
    test_count`, `trained_through_index` e exatamente o ultimo pregao, a impressao digital
    bate, e o retrato seria devolvido sem ter trecho nenhum para prever.
    """
    hyperparameters = _hyperparameters(model_name)
    step = int(hyperparameters["refit_frequency_days"])
    # `log_returns` descarta o primeiro pregao: P precos dao P-1 retornos, e o que sobra
    # depois da janela de treino e o periodo de teste.
    test_count = len(bars) - 1 - key.train_window_days
    rows = ModelSnapshot.objects.filter(
        asset=key.asset,
        model_name=model_name,
        alpha=_alpha(alpha),
        seed=key.seed,
        engine_version=key.engine_version,
        hyperparameters_hash=canonical_hash(hyperparameters),
        library_versions_hash=canonical_hash(key.library_versions),
        train_window_days=key.train_window_days,
        first_price_date=key.first_price_date,
    ).values_list("position", "price_fingerprint", "payload")
    found = {
        (position, fingerprint): bytes(payload)
        for position, fingerprint, payload in rows
    }
    valid: list[Snapshot] = []
    position = 0
    while position < test_count:
        fingerprint = price_fingerprint(
            bars, trained_through_index(position, key.train_window_days)
        )
        payload = found.get((position, fingerprint))
        if payload is None:
            break
        valid.append(Snapshot(position=position, payload=payload))
        position += step
    return valid


def save(
    key: SnapshotKey,
    model_name: str,
    alpha: float,
    bars: Sequence[Price],
    snaps: list[Snapshot],
) -> None:
    """Grava os retratos, em transacao propria, sem alterar nem duplicar nenhum.

    Nao devolve contagem: `ignore_conflicts` nao informa quantas linhas eram novas, e o
    manifesto conta pelo que o motor TREINOU, nao pelo que o banco aceitou.
    """
    if not snaps:
        return
    hyperparameters = _hyperparameters(model_name)
    hyperparameters_hash = canonical_hash(hyperparameters)
    library_versions_hash = canonical_hash(key.library_versions)
    created_at = timezone.now()
    rows = []
    for snap in snaps:
        through = trained_through_index(snap.position, key.train_window_days)
        # antes de `bars[through]`: a impressao digital recusa indice fora da serie, e
        # um indice negativo nao pode virar o pregao do fim da lista
        fingerprint = price_fingerprint(bars, through)
        rows.append(
            ModelSnapshot(
                asset=key.asset,
                model_name=model_name,
                alpha=_alpha(alpha),
                position=snap.position,
                trained_through=bars[through].date,
                seed=key.seed,
                engine_version=key.engine_version,
                train_window_days=key.train_window_days,
                first_price_date=key.first_price_date,
                hyperparameters=hyperparameters,
                hyperparameters_hash=hyperparameters_hash,
                library_versions=key.library_versions,
                library_versions_hash=library_versions_hash,
                price_fingerprint=fingerprint,
                payload=snap.payload,
                payload_bytes=len(snap.payload),
                created_at=created_at,
            )
        )
    with transaction.atomic():
        ModelSnapshot.objects.bulk_create(rows, ignore_conflicts=True)
