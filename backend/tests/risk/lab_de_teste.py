"""Os dados e o motor de troca dos testes do laboratorio (M2.4, T3) -- sem teste.

`conftest` nao se importa, e os tres arquivos `test_lab_anos.py`, `test_lab_calculo.py` e
`test_lab_escrita.py` precisam dos mesmos dados: moram aqui, no molde de
`tests/accounts/risco_de_teste.py`.

**A serie rala**: um pregao a cada `passo` dias de calendario, com log-retornos normais de
semente fixa a partir de 100 -- o `adj_close` sempre maior que zero. Com 800 pregoes a cada 5
dias, a decada (dez anos depois do primeiro) tem ~731 e a serie inteira 800: o teste da decada
cruza o retreino de 252 e o da inteira, o de 504.

**O ponto de troca** e `apps.risk.compute.run_experiment`, o nome que `run_models` chama (como
em `tests/risk/`). `motor_parcial` o substitui por um que roda o motor **real** so para os
modelos de `reais` e devolve, para os outros, `ModelRunResult` sinteticos: o VaR constante
sobre o periodo de teste e os backtests do motor sobre ele -- as violacoes do Kupiec batem com
as dos trechos por construcao. Nenhum teste treina as redes.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
import pytest
from django.utils import timezone
from engine.backtesting import get_backtest
from engine.data.preprocessing import fetch_returns
from engine.experiments import runner
from engine.experiments.runner import ExperimentConfig, ExperimentResult, ModelRunResult
from engine.models.base import VaREstimate

from apps.assets.models import Asset, CollectionRun, Price

Q6 = Decimal("0.000001")
INICIO = date(2015, 1, 5)


def ativo(ticker: str = "LABS3", *, status: str = Asset.Status.ACTIVE) -> Asset:
    agora = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )


def serie_rala(
    asset: Asset,
    quantidade: int = 800,
    *,
    passo: int = 5,
    inicio: date = INICIO,
    semente: int = 11,
    comum: CollectionRun | None = None,
    coletas: dict[int, CollectionRun] | None = None,
) -> list[Price]:
    """`quantidade` pregoes, um a cada `passo` dias de calendario a partir de `inicio`.

    `coletas` troca a coleta (`run`) de pregoes escolhidos pelo indice; os outros ficam com
    `comum`, ou com uma coleta criada aqui.
    """
    comum = comum or CollectionRun.objects.create(
        source="teste", started_at=timezone.now()
    )
    rng = np.random.default_rng(semente)
    nivel = 100.0
    linhas = []
    for i, retorno in enumerate(rng.normal(0, 0.015, quantidade)):
        if i:
            nivel *= math.exp(float(retorno))
        valor = Decimal(str(nivel)).quantize(Q6)
        linhas.append(
            Price(
                asset=asset,
                date=inicio + timedelta(days=passo * i),
                open=valor,
                high=valor,
                low=valor,
                close=valor,
                adj_close=valor,
                volume=1000,
                log_return=None,
                run=(coletas or {}).get(i, comum),
                updated_at=timezone.now(),
            )
        )
    return Price.objects.bulk_create(linhas)


def periodo_de_teste(config: ExperimentConfig, provider: Any) -> pd.Series:
    returns = fetch_returns(provider, config.ticker, config.start, config.end)
    return returns.iloc[config.train_window_days :]


def sintetico(
    config: ExperimentConfig, teste: pd.Series, model_name: str, alpha: float
) -> ModelRunResult:
    """Um `ModelRunResult` montado: o VaR constante e os backtests do motor sobre ele."""
    nivel = 0.02 if alpha == 0.05 else 0.03
    var = pd.Series(nivel, index=teste.index)
    alinhado = teste.reindex(var.index).dropna()
    var_alinhado = var.reindex(alinhado.index)
    return ModelRunResult(
        model_name=model_name,
        alpha=alpha,
        backtests=[
            get_backtest(nome)().run(alinhado, var_alinhado, alpha)
            for nome in config.backtest_names
        ],
        estimate=VaREstimate(
            var_series=var, alpha=alpha, horizon=1, model_name=model_name
        ),
    )


Ajuste = Callable[[list[ModelRunResult]], None]


@dataclass
class Motor:
    """O que o motor de troca recebeu: uma configuracao por chamada."""

    chamadas: list[ExperimentConfig] = field(default_factory=list)


def motor_parcial(
    monkeypatch: pytest.MonkeyPatch,
    reais: frozenset[str] = frozenset(),
    *,
    ajuste: Ajuste | None = None,
) -> Motor:
    """Substitui `apps.risk.compute.run_experiment`: real so para `reais`, sintetico no resto.

    `ajuste` recebe a lista final de resultados, na ordem do pedido, e pode muda-la no lugar
    (forcar um erro, desalinhar uma soma).
    """
    motor = Motor()
    original = runner.run_experiment

    def troca(config: ExperimentConfig, provider: Any) -> ExperimentResult:
        motor.chamadas.append(config)
        escolhidos = [m for m in config.model_names if m in reais]
        reais_por_chave: dict[tuple[str, float], ModelRunResult] = {}
        if escolhidos:
            parcial = original(replace(config, model_names=escolhidos), provider)
            reais_por_chave = {(r.model_name, r.alpha): r for r in parcial.runs}
        teste = periodo_de_teste(config, provider)
        runs = [
            reais_por_chave[(m, a)] if m in reais else sintetico(config, teste, m, a)
            for m in config.model_names
            for a in config.alphas
        ]
        if ajuste is not None:
            ajuste(runs)
        return ExperimentResult(config=config, runs=runs)

    monkeypatch.setattr("apps.risk.compute.run_experiment", troca)
    return motor


def agora_fixo(*instantes: datetime) -> Callable[[], datetime]:
    """Um `now()` que devolve os instantes na ordem, repetindo o ultimo."""
    restantes = list(instantes)

    def agora() -> datetime:
        return restantes.pop(0) if len(restantes) > 1 else restantes[0]

    return agora
