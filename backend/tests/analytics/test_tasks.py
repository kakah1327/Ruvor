"""A tarefa de metricas da rotina diaria: V-20 do M1.6a (RF-21).

A corrente `importar_precos -> calcular_metricas -> recalcular_cobertos` e conferida em
`tests/risk/test_beat.py`, junto do teste da `rotina_diaria` que ela substituiu. Aqui fica o
que e da tarefa: o nome registrado no `worker`, e que um ativo falho **nao rompe o elo** --
`_calcular_metricas` devolve `"FALHOU: ..."` em vez de levantar, e o ativo que calculou fica
gravado.

**O nome registrado e conferido em subprocesso**, no molde de `tests/test_celery_registro.py`:
`app.task` registra com `shared=True`, e este modulo importa `apps.analytics.tasks` -- no
processo do pytest o registro apareceria populado sem que a descoberta automatica tivesse
achado o arquivo.

O caminho do ativo falho e o **real**: `run_compute_metrics` de verdade, sobre dado de
teste, com a escrita substituida so para o segundo ativo -- como o V-12 de
`test_compute.py`. Os outros ramos substituem `run_compute_metrics` pelo nome em
`apps.analytics.tasks`, que e onde a tarefa a chama.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import NoReturn

import pytest
from django.utils import timezone

from apps.analytics.compute import (
    AssetResult,
    InvalidTickers,
    MetricsFailed,
    MetricsReport,
    write_metrics,
)
from apps.analytics.metrics import Metrics
from apps.analytics.models import BehaviorMetric
from apps.analytics.tasks import _calcular_metricas
from apps.assets.models import Asset, CollectionRun, Price

# O diretorio de `backend/`, onde `config` e `apps` sao importaveis.
_BACKEND_DIR = Path(__file__).resolve().parents[2]

# A descoberta e preguicosa: sem `import_default_modules()` nada seria importado.
_SCRIPT = """
import django

django.setup()

import config

config.celery_app.loader.import_default_modules()
for name in sorted(config.celery_app.tasks):
    if name.startswith("apps."):
        print(name)
"""

Q10 = Decimal("0.0000000001")


def _make_asset(ticker: str) -> Asset:
    now = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=now,
        updated_at=now,
    )


def _make_prices(asset: Asset, quantidade: int = 30) -> None:
    """Serie mensal crescente, dia 15; o primeiro pregao sem `log_return`, como o
    `import_prices` grava."""
    run = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    now = timezone.now()
    anterior: Decimal | None = None
    linhas = []
    for i in range(quantidade):
        y, m = divmod(2024 * 12 + i, 12)
        adj = Decimal(100 + i)
        log_return = None if anterior is None else (adj / anterior).ln().quantize(Q10)
        linhas.append(
            Price(
                asset=asset,
                date=date(y, m + 1, 15),
                open=adj,
                high=adj,
                low=adj,
                close=adj,
                adj_close=adj,
                volume=1000 + i,
                log_return=log_return,
                run=run,
                updated_at=now,
            )
        )
        anterior = adj
    Price.objects.bulk_create(linhas)


def _report_com_falha() -> MetricsReport:
    falho = AssetResult("BBB3", 30, date(2026, 5, 15), [], "RuntimeError: x", False)
    return MetricsReport([falho], 0.0)


# --- o nome registrado no worker -------------------------------------------------------


def test_calcular_metricas_entra_por_descoberta_automatica() -> None:
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings_test"}
    completed = subprocess.run(
        [sys.executable, "-c", _SCRIPT],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    registered = set(completed.stdout.split())
    assert "apps.analytics.tasks.calcular_metricas" in registered, completed.stdout


# --- V-20: o elo nao se rompe por ativo falho ----------------------------------------------


def test_calcular_metricas_devolve_a_falha_das_metricas_em_vez_de_levantar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falha(tickers: list[str]) -> NoReturn:
        raise MetricsFailed(_report_com_falha())

    monkeypatch.setattr("apps.analytics.tasks.run_compute_metrics", falha)

    saida = _calcular_metricas()

    assert saida.startswith("FALHOU: BBB3\n"), saida
    assert "FALHOU (RuntimeError: x)" in saida, saida


def test_calcular_metricas_devolve_tickers_invalidos_em_vez_de_levantar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalidos(tickers: list[str]) -> NoReturn:
        raise InvalidTickers(["ZZZZ3"])

    monkeypatch.setattr("apps.analytics.tasks.run_compute_metrics", invalidos)

    assert _calcular_metricas() == "FALHOU: ZZZZ3"


def test_calcular_metricas_propaga_o_que_nao_e_falha_de_ativo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def quebra(tickers: list[str]) -> NoReturn:
        raise RuntimeError("o calculo nao chegou a rodar")

    monkeypatch.setattr("apps.analytics.tasks.run_compute_metrics", quebra)

    with pytest.raises(RuntimeError, match="nao chegou a rodar"):
        _calcular_metricas()


@pytest.mark.django_db
def test_calcular_metricas_calcula_os_ativos_com_preco_e_devolve_o_relatorio() -> None:
    _make_prices(_make_asset("AAA3"))

    saida = _calcular_metricas()

    assert not saida.startswith("FALHOU"), saida
    assert "metricas: 1 ativos, 1 ok, 0 falhos, 0 pulados" in saida, saida
    assert list(BehaviorMetric.objects.values_list("asset__ticker", flat=True)) == [
        "AAA3"
    ]


@pytest.mark.django_db
def test_com_um_ativo_falho_o_outro_fica_gravado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for ticker in ("AAA3", "BBB3"):
        _make_prices(_make_asset(ticker))

    def escrita_que_falha_no_segundo(
        asset: Asset, calculated_at: datetime, metrics: Metrics
    ) -> BehaviorMetric:
        if asset.ticker == "BBB3":
            raise RuntimeError("gravacao quebrou")
        return write_metrics(asset, calculated_at, metrics)

    monkeypatch.setattr(
        "apps.analytics.compute.write_metrics", escrita_que_falha_no_segundo
    )

    saida = _calcular_metricas()

    assert saida.startswith("FALHOU: BBB3\n"), saida
    assert set(BehaviorMetric.objects.values_list("asset__ticker", flat=True)) == {
        "AAA3"
    }
