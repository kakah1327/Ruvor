"""O relatorio de risco de um ativo: o conteudo, os bytes, o CSV e o nome do arquivo (M4.1).

**O conteudo** (RF-03) e o formato 1, contrato para sempre: as chaves estao escritas aqui, e so
elas. **Os bytes** (RF-04) sao serializados uma vez, na geracao, e guardados em `core.report`;
nada os serializa de novo. **O CSV** (RF-09) e derivado dos bytes guardados, nunca do banco de
risco.

Decimal vira texto por `format(d, "f")` -- nunca `str()`, que da `0E-10` --, e o texto e o mesmo
que o `/risk` entrega **desde que o `Decimal` venha do banco**, com a escala da coluna. Instante
vira ISO 8601 em UTC. `to_bytes` nao conhece `Decimal` nem `datetime`: um esquecido levanta
`TypeError` no `json.dumps`, e nao vira `float` calado.

**Sem DRF e sem consulta ao banco** (`test_fase1_sem_drf`): recebe os objetos ja lidos -- a
execucao com a `price_run` no `select_related` -- e devolve dados.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from apps.accounts.models import Organization
    from apps.assets.models import Asset
    from apps.risk.models import RiskResult, RiskRun

FORMAT = "ruvor.asset_risk_report"
FORMAT_VERSION = 1
HORIZON_DAYS = 1
# As de `apps/api/views.py`, que este modulo nao importa (DRF); um teste da T3 confere.
CLOSED_RUN_STATUSES: tuple[str, ...] = ("ok", "partial", "failed")

# As colunas de `result` do RF-03, na ordem dele: as do `RiskResultSerializer` menos
# `basel_zone`, `reused_snapshots` e `trained_snapshots`.
RESULT_FIELDS: tuple[str, ...] = (
    "model_name",
    "model_category",
    "alpha",
    "hyperparameters",
    "var_latest",
    "var_mean",
    "violations",
    "expected_violations",
    "kupiec_passed",
    "kupiec_p_value",
    "christoffersen_passed",
    "christoffersen_p_value",
    "dq_passed",
    "dq_p_value",
    "adequate",
    "error",
)

# O cabecalho do CSV (RF-09): `hyperparameters` e objeto, nao cabe numa celula.
CSV_FIELDS: tuple[str, ...] = tuple(f for f in RESULT_FIELDS if f != "hyperparameters")


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")  # nunca str(): 0E-10


def _instant(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(UTC).isoformat()


def _result(result: RiskResult) -> dict[str, Any]:
    return {
        "model_name": result.model_name,
        "model_category": result.model_category,
        "alpha": _decimal(result.alpha),
        "hyperparameters": result.hyperparameters,
        "var_latest": _decimal(result.var_latest),
        "var_mean": _decimal(result.var_mean),
        "violations": result.violations,
        "expected_violations": _decimal(result.expected_violations),
        "kupiec_passed": result.kupiec_passed,
        "kupiec_p_value": _decimal(result.kupiec_p_value),
        "christoffersen_passed": result.christoffersen_passed,
        "christoffersen_p_value": _decimal(result.christoffersen_p_value),
        "dq_passed": result.dq_passed,
        "dq_p_value": _decimal(result.dq_p_value),
        "adequate": result.adequate,
        "error": result.error,
    }


def _summary(results: Sequence[RiskResult]) -> list[dict[str, Any]]:
    """Um nivel por `alpha` presente, em `alpha` decrescente (D-96): calculados sobre os
    `Decimal`, e so entao convertidos."""
    levels: list[dict[str, Any]] = []
    for alpha in sorted({r.alpha for r in results}, reverse=True):
        at_level = [r for r in results if r.alpha == alpha]
        computed = sorted(
            (r for r in at_level if r.var_latest is not None),
            key=lambda r: r.model_name,
        )
        values = [r.var_latest for r in computed if r.var_latest is not None]
        levels.append(
            {
                "alpha": _decimal(alpha),
                "computed": [r.model_name for r in computed],
                "var_min": _decimal(min(values)) if values else None,
                "var_max": _decimal(max(values)) if values else None,
                # lista, sem eleger nenhum (D-65); vazia e resultado legitimo
                "not_rejected": sorted(
                    r.model_name for r in at_level if r.adequate is True
                ),
            }
        )
    return levels


def build_content(
    *,
    report_id: UUID,
    generated_at: datetime,
    organization: Organization,
    requester_name: str,
    asset: Asset,
    run: RiskRun,
    results: Sequence[RiskResult],
) -> dict[str, Any]:
    """O conteudo do formato 1 (RF-03): so `str`, `int`, `bool`, `None`, `list` e `dict`.
    `results` na ordem de entrada -- quem chama entrega em `model_name`, depois `alpha`
    decrescente, a ordem do `/risk`."""
    price_run = run.price_run
    return {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "report_id": str(report_id),
        "generated_at": _instant(generated_at),
        "organization": {"slug": organization.slug, "name": organization.name},
        "requested_by": {"name": requester_name},
        "asset": {
            "ticker": asset.ticker,
            "name": asset.name,
            "trading_name": asset.trading_name,
            "isin": asset.isin,
        },
        "horizon_days": HORIZON_DAYS,
        "risk_run": {
            "id": run.pk,
            "calculated_at": _instant(run.calculated_at),
            "finished_at": _instant(run.finished_at),
            "status": run.status,
            "engine_version": run.engine_version,
            "seed": run.seed,
            "train_window_days": run.train_window_days,
            "as_of_date": run.as_of_date.isoformat(),
            "first_price_date": run.first_price_date.isoformat(),
            "price_count": run.price_count,
            "train_count": run.train_count,
            "test_count": run.test_count,
            "requested_models": run.requested_models,
            "full_recompute": run.full_recompute,
            "price_run": {
                "id": price_run.pk,
                "source": price_run.source,
                "started_at": _instant(price_run.started_at),
                "finished_at": _instant(price_run.finished_at),
            },
        },
        "results": [_result(r) for r in results],
        "summary": _summary(results),
    }


def to_bytes(content: dict[str, Any]) -> bytes:
    return json.dumps(
        content,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):  # antes do int: True e int, e sairia "True"
        return "true" if value else "false"
    return str(value)  # o texto do JSON (decimal) ou o inteiro


def to_csv(content: bytes | memoryview) -> bytes:
    """O CSV dos `results` do conteudo **guardado** (RF-09): RFC 4180, `\\r\\n`, UTF-8 sem BOM."""
    data = json.loads(bytes(content))
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_FIELDS)
    for result in data["results"]:
        writer.writerow([_cell(result[field]) for field in CSV_FIELDS])
    return buffer.getvalue().encode("utf-8")


def filename(ticker: str, as_of_date: str, report_id: str, extension: str) -> str:
    """`ruvor-risco-<TICKER>-<as_of_date>-<8 primeiros do id>.<extensao>` (RF-08)."""
    return f"ruvor-risco-{ticker}-{as_of_date}-{report_id[:8]}.{extension}"
