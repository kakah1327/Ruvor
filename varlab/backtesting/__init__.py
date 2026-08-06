# Etapa 4: testes de backtesting (Kupiec, Christoffersen, DQ, zonas de Basileia).
# Cada arquivo neste pacote define uma classe BacktestTest e se registra com @register_backtest.
from varlab.backtesting.registry import _load_all_backtest_modules, get_backtest, list_backtests

__all__ = ["get_backtest", "list_backtests", "load_all_backtest_modules"]


def load_all_backtest_modules() -> None:
    _load_all_backtest_modules()
