"""M2.2a, T5: ler o risco da carteira (RF-16, RF-17; V-17, V-18).

A execucao fechada tem quatro resultados escritos a mao, com a perda em reais conferida contra
valores tambem escritos a mao (`notional * (1 - e^-var)`, a 2 casas, `ROUND_HALF_UP`):

| var          | 100000.00 | 50000.00 |
|--------------|-----------|----------|
| 0.0200000000 | 1980.13   | 990.07   |
| 0.0283415120 | 2794.37   | 1397.18  |
| 0.0300000000 | 2955.45   | 1477.72  |
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.utils import timezone

from apps.accounts.tenancy import organization_scope
from apps.assets.models import CollectionRun
from apps.portfolios import config as portfolio_config
from apps.portfolios.models import (
    Portfolio,
    PortfolioRiskResult,
    PortfolioRiskRun,
    PortfolioVersion,
)
from apps.risk.models import RiskRun
from tests.portfolios.dados import Pessoas, acao, carteira, org_e_pessoas, sessao

pytestmark = pytest.mark.django_db

Status = RiskRun.Status

RISCO = {"portfolio_id", "version", "notional", "latest", "in_progress"}
RUN = {
    "id",
    "version",
    "status",
    "calculated_at",
    "finished_at",
    "engine_version",
    "seed",
    "train_window_days",
    "first_date",
    "as_of_date",
    "session_count",
    "train_count",
    "test_count",
    "requested_models",
    "series_sha256",
    "price_run_id",
    "requested_by",
    "results",
    "summary",
}
RESULT = {
    "model_name",
    "model_category",
    "alpha",
    "hyperparameters",
    "var_latest",
    "var_mean",
    "violations",
    "expected_violations",
    "kupiec_passed",
    "kupiec_p_value",
    "christoffersen_passed",
    "christoffersen_p_value",
    "dq_passed",
    "dq_p_value",
    "adequate",
    "error",
    "loss_brl",
}
LEVEL = {
    "alpha",
    "computed",
    "var_min",
    "var_max",
    "loss_brl_min",
    "loss_brl_max",
    "not_rejected",
}
PROGRESS = {
    "id",
    "version",
    "calculated_at",
    "requested_models",
    "results_written",
    "results_expected",
}


@pytest.fixture
def pessoas() -> Pessoas:
    acao("PETR4", [])
    acao("VALE3", [])
    acao("ITUB4", [])
    return org_e_pessoas()


def _versao(portfolio: Portfolio) -> PortfolioVersion:
    return PortfolioVersion.unscoped.filter(portfolio=portfolio).order_by("-number")[0]


def _execucao(
    portfolio: Portfolio, status: str, horas_atras: float
) -> PortfolioRiskRun:
    instante = timezone.now() - timedelta(hours=horas_atras)
    coleta = CollectionRun.objects.create(source="yahoo_chart", started_at=instante)
    with organization_scope(portfolio.organization_id):
        return PortfolioRiskRun.objects.create(
            version=_versao(portfolio),
            requested_by=portfolio.created_by,
            calculated_at=instante,
            finished_at=None if status == Status.RUNNING else instante,
            status=status,
            engine_version="0.3.0",
            seed=42,
            train_window_days=252,
            first_date=date(2024, 1, 2),
            as_of_date=date(2026, 1, 2),
            session_count=520,
            train_count=252,
            test_count=267,
            requested_models=list(portfolio_config.PORTFOLIO_MODELS),
            price_run=coleta,
            series_sha256="a" * 64,
        )


def _resultado(
    run: PortfolioRiskRun,
    model_name: str,
    alpha: str,
    var: str | None,
    adequate: bool | None,
) -> None:
    with organization_scope(run.version.portfolio.organization_id):
        PortfolioRiskResult.objects.create(
            run=run,
            model_name=model_name,
            model_category="traditional",
            alpha=Decimal(alpha),
            hyperparameters={"janela": 252},
            var_latest=None if var is None else Decimal(var),
            var_mean=None if var is None else Decimal(var),
            violations=None if var is None else 10,
            expected_violations=None if var is None else Decimal("13.350000"),
            kupiec_passed=adequate,
            kupiec_p_value=None if var is None else Decimal("0.5000000000"),
            christoffersen_passed=adequate,
            christoffersen_p_value=None if var is None else Decimal("0.4000000000"),
            dq_passed=None,
            dq_p_value=None,
            basel_zone=None if var is None else "green",
            adequate=adequate,
            error="" if var is not None else "RuntimeError: de teste",
        )


def _fechada_com_quatro(portfolio: Portfolio) -> PortfolioRiskRun:
    run = _execucao(portfolio, Status.PARTIAL, 2)
    # fora de ordem de proposito: a leitura ordena
    _resultado(run, "parametric", "0.0100", None, None)
    _resultado(run, "historical", "0.0500", "0.0200000000", True)
    _resultado(run, "parametric", "0.0500", "0.0283415120", True)
    _resultado(run, "historical", "0.0100", "0.0300000000", False)
    return run


def _risco(pessoas: Pessoas, portfolio: Portfolio) -> dict[str, Any]:
    resposta = sessao(pessoas.admin).get(
        f"/api/v1/portfolios/{portfolio.public_id}/risk"
    )
    assert resposta.status_code == 200, resposta.content
    corpo = resposta.json()
    assert set(corpo) == {"portfolio_risk"}
    risco: dict[str, Any] = corpo["portfolio_risk"]
    return risco


# --- V-17: o corpo ----------------------------------------------------------------------


def test_v17_as_listas_fechadas_de_chaves(pessoas: Pessoas, debug: bool) -> None:
    portfolio = carteira(
        pessoas.admin, {"PETR4": "60", "VALE3": "40"}, notional="100000.00"
    )
    _fechada_com_quatro(portfolio)
    progresso = _execucao(portfolio, Status.RUNNING, 0.1)
    _resultado(progresso, "historical", "0.0500", "0.0200000000", True)

    risco = _risco(pessoas, portfolio)

    assert set(risco) == RISCO
    assert set(risco["latest"]) == RUN
    for resultado in risco["latest"]["results"]:
        assert set(resultado) == RESULT
    for nivel in risco["latest"]["summary"]:
        assert set(nivel) == LEVEL
    assert set(risco["in_progress"]) == PROGRESS
    assert risco["in_progress"]["results_written"] == 1
    assert risco["in_progress"]["results_expected"] == 18
    assert risco["in_progress"]["id"] == progresso.pk
    assert risco["in_progress"]["version"] == 1


def test_v17_o_manifesto_e_os_resultados_em_ordem(pessoas: Pessoas) -> None:
    portfolio = carteira(
        pessoas.admin, {"PETR4": "60", "VALE3": "40"}, notional="100000.00"
    )
    run = _fechada_com_quatro(portfolio)

    risco = _risco(pessoas, portfolio)
    latest = risco["latest"]

    assert (risco["portfolio_id"], risco["version"], risco["notional"]) == (
        str(portfolio.public_id),
        1,
        "100000.00",
    )
    assert risco["in_progress"] is None
    assert latest["id"] == run.pk
    assert latest["version"] == 1
    assert latest["status"] == "partial"
    assert latest["price_run_id"] == run.price_run_id
    assert latest["series_sha256"] == "a" * 64
    assert latest["first_date"] == "2024-01-02"
    assert latest["as_of_date"] == "2026-01-02"
    assert latest["requested_by"] == {
        "email": "admin@acme.test",
        "name": "Pessoa de Teste",
    }
    assert latest["requested_models"] == list(portfolio_config.PORTFOLIO_MODELS)
    assert [(r["model_name"], r["alpha"]) for r in latest["results"]] == [
        ("historical", "0.0500"),
        ("historical", "0.0100"),
        ("parametric", "0.0500"),
        ("parametric", "0.0100"),
    ]
    historico = latest["results"][0]
    assert historico["var_latest"] == "0.0200000000"
    assert historico["expected_violations"] == "13.350000"
    assert historico["hyperparameters"] == {"janela": 252}
    assert latest["results"][3]["error"] == "RuntimeError: de teste"
    assert latest["results"][3]["var_latest"] is None


def test_v17_o_resumo_escrito_a_mao(pessoas: Pessoas) -> None:
    portfolio = carteira(
        pessoas.admin, {"PETR4": "60", "VALE3": "40"}, notional="100000.00"
    )
    _fechada_com_quatro(portfolio)

    assert _risco(pessoas, portfolio)["latest"]["summary"] == [
        {
            "alpha": "0.0500",
            "computed": ["historical", "parametric"],
            "var_min": "0.0200000000",
            "var_max": "0.0283415120",
            "loss_brl_min": "1980.13",
            "loss_brl_max": "2794.37",
            "not_rejected": ["historical", "parametric"],
        },
        {
            "alpha": "0.0100",
            "computed": ["historical"],
            "var_min": "0.0300000000",
            "var_max": "0.0300000000",
            "loss_brl_min": "2955.45",
            "loss_brl_max": "2955.45",
            "not_rejected": [],
        },
    ]


def test_v17_sem_nenhum_adequate_not_rejected_vazio(pessoas: Pessoas) -> None:
    portfolio = carteira(pessoas.admin, {"PETR4": "60", "VALE3": "40"})
    run = _execucao(portfolio, Status.FAILED, 2)
    _resultado(run, "historical", "0.0500", None, None)
    _resultado(run, "historical", "0.0100", None, None)

    summary = _risco(pessoas, portfolio)["latest"]["summary"]
    assert [n["not_rejected"] for n in summary] == [[], []]
    assert [n["computed"] for n in summary] == [[], []]
    assert summary[0]["var_min"] is None
    assert summary[0]["loss_brl_min"] is None


def test_v17_latest_so_da_versao_corrente(pessoas: Pessoas) -> None:
    portfolio = carteira(pessoas.admin, {"PETR4": "60", "VALE3": "40"})
    antiga = _fechada_com_quatro(portfolio)
    resposta = sessao(pessoas.admin).put(
        f"/api/v1/portfolios/{portfolio.public_id}/holdings",
        {
            "holdings": [
                {"ticker": "ITUB4", "weight": "50"},
                {"ticker": "VALE3", "weight": "50"},
            ]
        },
        format="json",
    )
    assert resposta.status_code == 200, resposta.content

    risco = _risco(pessoas, portfolio)

    assert (risco["version"], risco["latest"], risco["in_progress"]) == (2, None, None)
    assert PortfolioRiskRun.unscoped.filter(pk=antiga.pk).exists()


def test_v17_in_progress_vencida_nao_aparece(pessoas: Pessoas) -> None:
    portfolio = carteira(pessoas.admin, {"PETR4": "60", "VALE3": "40"})
    _execucao(portfolio, Status.RUNNING, 2)  # 120 min: vencida
    assert _risco(pessoas, portfolio)["in_progress"] is None


def test_v17_in_progress_mais_velha_que_o_latest_nao_aparece(pessoas: Pessoas) -> None:
    portfolio = carteira(pessoas.admin, {"PETR4": "60", "VALE3": "40"})
    _execucao(portfolio, Status.RUNNING, 0.5)
    fechada = _execucao(portfolio, Status.OK, 0.2)
    risco = _risco(pessoas, portfolio)
    assert risco["in_progress"] is None
    assert risco["latest"]["id"] == fechada.pk


# --- V-18: a perda em reais -------------------------------------------------------------


def test_v18_a_perda_em_reais_e_a_escrita_a_mao(pessoas: Pessoas) -> None:
    portfolio = carteira(
        pessoas.admin, {"PETR4": "60", "VALE3": "40"}, notional="100000.00"
    )
    _fechada_com_quatro(portfolio)
    resultados = _risco(pessoas, portfolio)["latest"]["results"]
    assert [r["loss_brl"] for r in resultados] == [
        "1980.13",
        "2955.45",
        "2794.37",
        None,
    ]


def test_v18_sem_notional_a_perda_e_nula(pessoas: Pessoas) -> None:
    portfolio = carteira(pessoas.admin, {"PETR4": "60", "VALE3": "40"})
    _fechada_com_quatro(portfolio)
    latest = _risco(pessoas, portfolio)["latest"]
    assert {r["loss_brl"] for r in latest["results"]} == {None}
    assert {n["loss_brl_min"] for n in latest["summary"]} == {None}


def test_v18_mudar_o_notional_muda_a_perda_sem_execucao_nova(pessoas: Pessoas) -> None:
    portfolio = carteira(
        pessoas.admin, {"PETR4": "60", "VALE3": "40"}, notional="100000.00"
    )
    _fechada_com_quatro(portfolio)
    resposta = sessao(pessoas.admin).patch(
        f"/api/v1/portfolios/{portfolio.public_id}",
        {"notional": "50000.00"},
        format="json",
    )
    assert resposta.status_code == 200, resposta.content

    risco = _risco(pessoas, portfolio)

    assert risco["notional"] == "50000.00"
    assert [r["loss_brl"] for r in risco["latest"]["results"]] == [
        "990.07",
        "1477.72",
        "1397.18",
        None,
    ]
    assert PortfolioRiskRun.unscoped.filter(version__portfolio=portfolio).count() == 1
