"""CLI do Ruvor. Reusa engine.experiments.runner — a mesma logica de negocio que
qualquer outro consumidor do motor usa — entao rodar um experimento em batch (ex: para
walk-forward validation) nao depende de nenhuma camada de apresentacao.
"""

from __future__ import annotations

import click


@click.group()
def main() -> None:
    """Ruvor — modelagem e backtesting de VaR com metodos tradicionais, GARCH e ML."""


@main.command()
@click.option("--ticker", required=True, help="Ex: PETR4.SA, VALE3.SA, ^BVSP")
@click.option("--start", required=True, help="YYYY-MM-DD")
@click.option("--end", required=True, help="YYYY-MM-DD")
@click.option(
    "--model",
    "models",
    multiple=True,
    required=True,
    help="Repetir para varios modelos",
)
@click.option(
    "--backtest",
    "backtests",
    multiple=True,
    required=True,
    help="Repetir para varios testes",
)
@click.option(
    "--alpha",
    "alphas",
    multiple=True,
    type=float,
    default=(0.05, 0.01),
    help="Repetir para varios niveis de confianca (default: 0.05 e 0.01 simultaneos)",
)
@click.option(
    "--train-window",
    "train_window_days",
    default=252,
    type=int,
    help="Dias uteis usados para treino, a partir do inicio do periodo (default: 252, 1 ano)",
)
def run(
    ticker: str,
    start: str,
    end: str,
    models: tuple[str, ...],
    backtests: tuple[str, ...],
    alphas: tuple[float, ...],
    train_window_days: int,
) -> None:
    """Roda um experimento headless e imprime a tabela de ranking."""
    from engine.backtesting import load_all_backtest_modules
    from engine.data.providers.yfinance_provider import YFinanceProvider
    from engine.experiments.runner import ExperimentConfig, run_experiment
    from engine.models import load_all_model_modules

    load_all_model_modules()
    load_all_backtest_modules()

    config = ExperimentConfig(
        ticker=ticker,
        start=start,
        end=end,
        model_names=list(models),
        backtest_names=list(backtests),
        alphas=list(alphas),
        train_window_days=train_window_days,
    )
    result = run_experiment(config, provider=YFinanceProvider())
    click.echo(result.ranking_table().to_string(index=False))


if __name__ == "__main__":
    main()
