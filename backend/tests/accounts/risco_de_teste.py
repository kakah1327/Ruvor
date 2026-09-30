"""Construtores de ativo, execucao de risco e resultado para os testes do M4.1 (sem teste).

No molde de `_ativo`, `_execucao` e `_resultado` de `tests/api/test_risco.py`. `conftest` nao
se importa, e os testes de relatorio de varios arquivos precisam dos mesmos dados: moram aqui.

`MODELOS` sao os nove modelos, escritos literalmente, como os de `apps/risk/compute.py:MODELS`
-- sem importar `compute.py`, que importa o motor. `NIVEIS` sao os dois `alpha` de
`apps/risk/config.py:ALPHAS`, na escala da coluna.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from django.utils import timezone

from apps.assets.models import Asset, CollectionRun, Price
from apps.risk.models import RiskResult, RiskRun

MODELOS: tuple[str, ...] = (
    "caviar",
    "egarch",
    "garch_1_1",
    "garchnet",
    "gru",
    "historical",
    "lstm",
    "monte_carlo",
    "parametric",
)

NIVEIS: tuple[str, ...] = ("0.0500", "0.0100")


def ativo(ticker: str) -> Asset:
    """Uma acao ativa do catalogo, com um preco."""
    agora = timezone.now()
    asset = Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )
    Price.objects.create(
        asset=asset,
        date=date(2026, 9, 25),
        open=Decimal("30"),
        high=Decimal("31"),
        low=Decimal("29"),
        close=Decimal("30.5"),
        adj_close=Decimal("30.25"),
        volume=1000,
        log_return=None,
        run=CollectionRun.objects.create(source="teste", started_at=agora),
        updated_at=agora,
    )
    return asset


def execucao(asset: Asset, status: str, calculated_at: datetime) -> RiskRun:
    """Uma execucao de risco do ativo, com a coleta de precos que ela cita. Pede os nove
    modelos; `finished_at` nulo so quando `running`."""
    coleta = CollectionRun.objects.create(
        source="yahoo_chart",
        started_at=calculated_at - timedelta(minutes=10),
        finished_at=calculated_at - timedelta(minutes=9),
        status=CollectionRun.Status.OK,
    )
    return RiskRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=None
        if status == RiskRun.Status.RUNNING
        else calculated_at + timedelta(minutes=2),
        engine_version="0.3.0",
        seed=42,
        train_window_days=252,
        as_of_date=date(2026, 9, 25),
        first_price_date=date(2016, 9, 26),
        price_count=2480,
        train_count=252,
        test_count=2227,
        price_run=coleta,
        requested_by=None,
        status=status,
        requested_models=list(MODELOS),
        full_recompute=False,
    )


def resultado(
    run: RiskRun, model_name: str, alpha: str | Decimal, **campos: Any
) -> RiskResult:
    """Um resultado calculado, sem erro; `campos` sobrepoe qualquer coluna."""
    valores: dict[str, Any] = {
        "model_category": "historical" if model_name == "historical" else "parametric",
        "hyperparameters": {"window": 252},
        "var_latest": Decimal("0.0234"),
        "var_mean": Decimal("0.0212"),
        "violations": 110,
        "expected_violations": Decimal("111.35"),
        "kupiec_passed": True,
        "kupiec_p_value": Decimal("0.8912"),
        "christoffersen_passed": False,
        "christoffersen_p_value": Decimal("0.0123"),
        "dq_passed": True,
        "dq_p_value": Decimal("0.4567"),
        "basel_zone": "green",
        "adequate": False,
        "error": "",
        "reused_snapshots": None,
        "trained_snapshots": None,
    }
    valores.update(campos)
    return RiskResult.objects.create(
        run=run, model_name=model_name, alpha=Decimal(alpha), **valores
    )


def execucao_completa(asset: Asset, calculated_at: datetime) -> RiskRun:
    """A execucao `ok` com os 18 resultados: os nove modelos nos dois niveis."""
    run = execucao(asset, RiskRun.Status.OK, calculated_at)
    for model_name in MODELOS:
        for alpha in NIVEIS:
            resultado(run, model_name, alpha)
    return run
