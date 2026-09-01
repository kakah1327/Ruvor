"""1 teste parametrizado cobre TODO modelo registrado — novo modelo adicionado em
engine/models/{traditional,garch,ml} passa a ser testado aqui automaticamente, sem
escrever nenhum teste novo.
"""
from engine.models import get_model, list_models, load_all_model_modules

load_all_model_modules()


def test_registry_loads_without_error():
    # Garante que o mecanismo de auto-registro funciona mesmo sem nenhum modelo ainda.
    assert isinstance(list_models(), list)


import pytest  # noqa: E402


@pytest.mark.parametrize("model_name", list_models())
def test_model_fit_and_estimate_var(model_name, synthetic_returns):
    split = len(synthetic_returns) // 2
    train, test = synthetic_returns.iloc[:split], synthetic_returns.iloc[split:]

    model_cls = get_model(model_name)
    model = model_cls().fit(train)
    estimate = model.estimate_var(test, alpha=0.05, horizon=1)

    assert isinstance(estimate.model_name, str) and estimate.model_name
    assert estimate.alpha == 0.05
    assert len(estimate.var_series) == len(test)
    assert estimate.var_series.index.equals(test.index)
    assert (estimate.var_series >= 0).all()
