"""Orquestrador: liga data -> models -> backtesting. Usado pela web (Etapa 5) e pelo
CLI/notebooks, sem nenhuma dependencia do Flask — a interface e so mais um consumidor
desta camada (Etapa 6: experimento comparativo).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from engine import seeding
from engine.backtesting import get_backtest
from engine.backtesting.base import BacktestResult
from engine.data.preprocessing import fetch_returns
from engine.models import get_model
from engine.models.base import VaREstimate
from engine.snapshots import Snapshot


@dataclass
class ExperimentConfig:
    ticker: str
    start: str
    end: str
    model_names: list[str]
    backtest_names: list[str]
    alphas: list[float] = field(default_factory=lambda: [0.05, 0.01])
    horizon: int = 1
    train_window_days: int = 252
    #: semente da execucao; o runner a CONFIGURA, e `_fit_for_alpha` a aplica (RF-01)
    seed: int = seeding.DEFAULT_SEED
    #: retratos a restaurar, por (modelo, alpha), antes de `estimate_var` (M1.5b, RF-06)
    snapshots: dict[tuple[str, float], list[Snapshot]] = field(default_factory=dict)


@dataclass
class ModelRunResult:
    model_name: str
    alpha: float
    backtests: list[BacktestResult] = field(default_factory=list)
    error: str | None = None
    #: a estimativa que produziu os backtests; sem ela o VaR nao sai daqui (RF-04)
    estimate: VaREstimate | None = None
    #: os retratos que o modelo expos, restaurados e treinados -- preenchido TAMBEM com
    #: `error`: os pontos anteriores a falha continuam valendo (M1.5b, RF-02)
    snapshots: list[Snapshot] = field(default_factory=list)


@dataclass
class ExperimentResult:
    config: ExperimentConfig
    runs: list[ModelRunResult]

    def ranking_table(self) -> pd.DataFrame:
        """Tabela comparativa: 1 linha por (modelo, alpha), 1 coluna por teste de backtesting."""
        rows = []
        for run in self.runs:
            row = {"model": run.model_name, "alpha": run.alpha, "error": run.error}
            for bt in run.backtests:
                row[f"{bt.test_name}_passed"] = bt.passed
                row[f"{bt.test_name}_p_value"] = bt.p_value
            rows.append(row)
        return pd.DataFrame(rows)


def run_experiment(config: ExperimentConfig, provider) -> ExperimentResult:
    """Executa todos os modelos sobre um ativo, em cada nivel de confianca de `config.alphas`
    (95% e 99% simultaneamente por padrao, para comparacao regulatoria) e roda os testes de
    backtesting configurados sobre cada estimativa.

    Falhas (ex: dados insuficientes) nao derrubam o experimento inteiro — o erro fica
    registrado no ModelRunResult daquele (modelo, alpha) especifico e os demais continuam.

    A semente e CONFIGURADA aqui, uma vez por experimento, e aplicada no inicio de cada
    treino por `_fit_for_alpha` — o `fit()` dos neurais e preguicoso, entao semear aqui
    semearia antes de o treino existir (RF-01).
    """
    seeding.configure(config.seed)

    returns = fetch_returns(provider, config.ticker, config.start, config.end)
    if len(returns) <= config.train_window_days:
        raise ValueError(
            f"Periodo tem {len(returns)} dias uteis, insuficiente para a janela de "
            f"treino de {config.train_window_days} dias (nao sobraria dado de teste)"
        )
    train_returns = returns.iloc[: config.train_window_days]
    test_returns = returns.iloc[config.train_window_days :]

    runs: list[ModelRunResult] = []
    for model_name in config.model_names:
        try:
            model = get_model(model_name)().fit(train_returns)
        except Exception as exc:  # isola falha de 1 modelo do restante
            runs.extend(
                ModelRunResult(model_name=model_name, alpha=a, error=str(exc))
                for a in config.alphas
            )
            continue

        for alpha in config.alphas:
            try:
                if hasattr(model, "restore"):
                    model.restore(alpha, config.snapshots.get((model_name, alpha), []))
                estimate = model.estimate_var(
                    test_returns, alpha=alpha, horizon=config.horizon
                )
                snaps = model.snapshots(alpha) if hasattr(model, "snapshots") else []

                aligned_returns = test_returns.reindex(
                    estimate.var_series.index
                ).dropna()
                var_series = estimate.var_series.reindex(aligned_returns.index)

                backtests = [
                    get_backtest(bt_name)().run(aligned_returns, var_series, alpha)
                    for bt_name in config.backtest_names
                ]
                runs.append(
                    ModelRunResult(
                        model_name=model_name,
                        alpha=alpha,
                        backtests=backtests,
                        estimate=estimate,
                        snapshots=snaps,
                    )
                )
            except Exception as exc:  # isola falha de 1 (modelo, alpha) do restante
                try:
                    snaps = (
                        model.snapshots(alpha) if hasattr(model, "snapshots") else []
                    )
                except Exception:  # a leitura dos parciais nunca derruba o experimento
                    snaps = []
                runs.append(
                    ModelRunResult(
                        model_name=model_name,
                        alpha=alpha,
                        error=str(exc),
                        snapshots=snaps,
                    )
                )

    return ExperimentResult(config=config, runs=runs)
