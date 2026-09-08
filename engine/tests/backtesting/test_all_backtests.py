"""1 teste parametrizado cobre TODO teste de backtesting registrado — novo teste
adicionado em engine/backtesting/*.py passa a ser validado aqui automaticamente.
"""

import pytest

from engine.backtesting import get_backtest, list_backtests, load_all_backtest_modules

load_all_backtest_modules()


def test_registry_loads_without_error():
    assert isinstance(list_backtests(), list)


@pytest.fixture
def constant_var_series(synthetic_returns):
    # VaR constante no quantil 5% amostral — suficiente para exercitar a interface
    # de qualquer BacktestTest sem depender de um modelo de VaR real.
    alpha = 0.05
    threshold = -synthetic_returns.quantile(alpha)
    return synthetic_returns.apply(lambda _: threshold)


@pytest.mark.parametrize("backtest_name", list_backtests())
def test_backtest_run(backtest_name, synthetic_returns, constant_var_series):
    backtest_cls = get_backtest(backtest_name)
    result = backtest_cls().run(synthetic_returns, constant_var_series, alpha=0.05)

    assert result.test_name == backtest_name
    assert isinstance(result.passed, bool)
    assert isinstance(result.details, dict)
