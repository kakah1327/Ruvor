"""M2.2a, T6: a conversao da carteira e a do ativo (RF-23; V-23).

Os mesmos `ModelRunResult`, construidos a mao com `BacktestResult`, passam por `compute.row` e por
`apps.risk.compute._row(RiskRun(), ..., None)`, e as linhas sao comparadas campo a campo, menos
`run`, `id` e as duas colunas de retrato. Se a `marco1` mudar `_row`, este teste reprova na PR dela.
"""

from __future__ import annotations

import pandas as pd
import pytest
from engine.backtesting.base import BacktestResult
from engine.experiments.runner import ModelRunResult
from engine.models import load_all_model_modules
from engine.models.base import VaREstimate

from apps.portfolios.compute import failed_rows, row
from apps.portfolios.models import PortfolioRiskResult, PortfolioRiskRun
from apps.risk.compute import _row
from apps.risk.models import RiskRun


@pytest.fixture(autouse=True, scope="module")
def registry() -> None:
    load_all_model_modules()


def _bt(nome: str, passou: bool, p: float, **details: object) -> BacktestResult:
    return BacktestResult(
        test_name=nome, statistic=1.5, p_value=p, passed=passou, details=dict(details)
    )


def _resultado(
    *,
    kupiec: bool | None = True,
    christoffersen: bool | None = True,
    dq: bool | None = True,
    error: str | None = None,
    alpha: float = 0.05,
) -> ModelRunResult:
    backtests = []
    if kupiec is not None:
        backtests.append(
            _bt("kupiec", kupiec, 0.4123456789123, violations=14, expected=13.35)
        )
    if christoffersen is not None:
        backtests.append(_bt("christoffersen", christoffersen, 0.0312345678912))
    if dq is not None:
        backtests.append(_bt("dq", dq, 0.7777777777777))
    backtests.append(_bt("basileia", True, 0.5, zone="yellow"))
    return ModelRunResult(
        model_name="historical",
        alpha=alpha,
        backtests=backtests,
        error=error,
        estimate=VaREstimate(
            var_series=pd.Series([0.021, 0.0283415120123, 0.0199999999999]),
            alpha=alpha,
            horizon=1,
            model_name="historical",
        ),
    )


CASOS = {
    "com_erro": _resultado(error="RuntimeError: falhou"),
    "os_dois_aprovados": _resultado(),
    "kupiec_aprovado_christoffersen_reprovado": _resultado(christoffersen=False),
    "kupiec_reprovado_christoffersen_aprovado": _resultado(kupiec=False),
    "sem_o_dq": _resultado(dq=None),
    "nivel_99": _resultado(alpha=0.01),
}

CAMPOS = [
    f.name
    for f in PortfolioRiskResult._meta.concrete_fields
    if f.name not in {"id", "run"}
]


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_v23_a_carteira_converte_como_o_ativo(caso: str) -> None:
    resultado = CASOS[caso]
    da_carteira = row(PortfolioRiskRun(), resultado)
    do_ativo = _row(RiskRun(), resultado, None)
    assert len(CAMPOS) == 17  # contra a comparacao inerte
    for campo in CAMPOS:
        assert getattr(da_carteira, campo) == getattr(do_ativo, campo), campo


def test_v23_o_terceiro_caso_reprova_o_veredito() -> None:
    linha = row(PortfolioRiskRun(), CASOS["kupiec_aprovado_christoffersen_reprovado"])
    assert (linha.kupiec_passed, linha.christoffersen_passed, linha.adequate) == (
        True,
        False,
        False,
    )


def test_v23_com_erro_os_numeros_sao_nulos() -> None:
    linha = row(PortfolioRiskRun(), CASOS["com_erro"])
    assert linha.error == "RuntimeError: falhou"
    assert (linha.var_latest, linha.violations, linha.adequate) == (None, None, None)


def test_failed_rows_e_o_par_dos_dois_niveis() -> None:
    par = failed_rows(PortfolioRiskRun(), "historical", "serie mudou")
    assert [(r.model_name, str(r.alpha), r.error) for r in par] == [
        ("historical", "0.0500", "serie mudou"),
        ("historical", "0.0100", "serie mudou"),
    ]
    assert all(r.var_latest is None and r.adequate is None for r in par)
