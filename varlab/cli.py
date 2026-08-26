"""CLI do VaR Lab. Reusa varlab.experiments.runner — a mesma logica de negocio que a
web usa — entao rodar um experimento em batch (ex: para walk-forward validation) nunca
depende do Flask estar rodando.
"""
from __future__ import annotations

import click


@click.group()
def main() -> None:
    """VaR Lab — modelagem e backtesting de VaR com metodos tradicionais, GARCH e ML."""


@main.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=5000, type=int)
@click.option("--debug/--no-debug", default=True)
def web(host: str, port: int, debug: bool) -> None:
    """Sobe o servidor de desenvolvimento Flask."""
    from varlab.web.app import create_app

    app = create_app()
    app.run(host=host, port=port, debug=debug)


@main.command()
@click.option("--ticker", required=True, help="Ex: PETR4.SA, VALE3.SA, ^BVSP")
@click.option("--start", required=True, help="YYYY-MM-DD")
@click.option("--end", required=True, help="YYYY-MM-DD")
@click.option("--model", "models", multiple=True, required=True, help="Repetir para varios modelos")
@click.option("--backtest", "backtests", multiple=True, required=True, help="Repetir para varios testes")
@click.option("--alpha", "alphas", multiple=True, type=float, default=(0.05, 0.01),
              help="Repetir para varios niveis de confianca (default: 0.05 e 0.01 simultaneos)")
@click.option("--train-window", "train_window_days", default=252, type=int,
              help="Dias uteis usados para treino, a partir do inicio do periodo (default: 252, 1 ano)")
@click.option("--save/--no-save", default=False, help="Persiste o resultado no SQLite local")
def run(ticker: str, start: str, end: str, models: tuple[str, ...], backtests: tuple[str, ...], alphas: tuple[float, ...], train_window_days: int, save: bool) -> None:
    """Roda um experimento headless (sem subir a web) e imprime a tabela de ranking."""
    from varlab.data.providers.yfinance_provider import YFinanceProvider
    from varlab.experiments.runner import ExperimentConfig, run_experiment
    from varlab.models import load_all_model_modules
    from varlab.backtesting import load_all_backtest_modules

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

    if save:
        from varlab.storage.repository import SQLiteExperimentRunRepository

        run_id = SQLiteExperimentRunRepository().save(result)
        click.echo(f"Salvo como run #{run_id}")


if __name__ == "__main__":
    main()
