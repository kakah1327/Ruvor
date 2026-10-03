"""M2.2a, T6: as tarefas do risco da carteira (RF-14; V-14, V-15, V-16 sem concorrencia).

As funcoes com sublinhado sao chamadas direto, **sem contexto posto pelo teste**: cada tarefa abre
o `organization_scope` do `organization_id` que recebe. O `_enqueue` e sempre o duplo, que guarda
o `chord` e nao fala com o Redis. O motor e o de verdade, com o `historical` -- o rapido -- sobre
as series de `dados.serie_longa` (520 pregoes).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from decimal import Decimal
from importlib.metadata import version
from typing import Any

import pytest
from celery import chord
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import run_experiment
from engine.models import get_model, list_models, load_all_model_modules
from engine.models.base import ModelCategory

from apps.assets.models import Price
from apps.portfolios import config as portfolio_config
from apps.portfolios.models import Portfolio, PortfolioRiskResult, PortfolioRiskRun
from apps.portfolios.tasks import (
    _abrir_risco_carteira,
    _calcular_modelo_carteira,
    _fechar_risco_carteira,
)
from apps.risk.compute import ModelsMissing
from apps.risk.models import RiskRun
from tests.portfolios.dados import (
    Pessoas,
    carteira,
    execucao_da_serie,
    org_e_pessoas,
    serie_longa,
)

pytestmark = pytest.mark.django_db

Status = RiskRun.Status
PESOS = {"PETR4": "60.00", "VALE3": "40.00"}
RANK = {ModelCategory.TRADITIONAL: 0, ModelCategory.GARCH: 1, ModelCategory.ML: 2}


@pytest.fixture(autouse=True, scope="module")
def registry() -> None:
    load_all_model_modules()
    load_all_backtest_modules()


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """O duplo do `_enqueue`: guarda o que recebeu e nao fala com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.portfolios.tasks._enqueue", recebidos.append)
    return recebidos


@pytest.fixture
def pessoas() -> Pessoas:
    serie_longa("PETR4")
    serie_longa("VALE3")
    return org_e_pessoas()


@pytest.fixture
def portfolio(pessoas: Pessoas) -> Portfolio:
    return carteira(pessoas.admin, PESOS)


def _run(
    portfolio: Portfolio, status: str = Status.RUNNING, **kw: Any
) -> PortfolioRiskRun:
    return execucao_da_serie(portfolio, portfolio.created_by, status, **kw)


def _relida(run: PortfolioRiskRun) -> PortfolioRiskRun:
    return PortfolioRiskRun.unscoped.get(pk=run.pk)


def _resultados(run: PortfolioRiskRun) -> list[PortfolioRiskResult]:
    return list(
        PortfolioRiskResult.unscoped.filter(run=run).order_by("model_name", "-alpha")
    )


# --- V-14: a abertura -------------------------------------------------------------------


def test_v14_a_abertura_escreve_a_versao_e_enfileira_o_chord_por_custo(
    portfolio: Portfolio, fila: list[Any]
) -> None:
    run = _run(portfolio, engine_version="")
    org = portfolio.organization_id

    _abrir_risco_carteira(run.pk, org)

    linha = _relida(run)
    assert linha.engine_version == version("ruvor-engine")
    assert linha.requested_models == list(portfolio_config.PORTFOLIO_MODELS)
    assert linha.status == Status.RUNNING
    assert len(fila) == 1
    grupo = fila[0]
    assert isinstance(grupo, chord)
    por_custo = sorted(
        portfolio_config.PORTFOLIO_MODELS, key=lambda n: RANK[get_model(n).category]
    )
    assert [get_model(n).category for n in por_custo][:3] == [
        ModelCategory.TRADITIONAL
    ] * 3
    assert [(s.task, s.args) for s in grupo.tasks] == [
        ("apps.portfolios.tasks.calcular_modelo_carteira", (run.pk, org, nome))
        for nome in por_custo
    ]
    assert (grupo.body.task, grupo.body.args) == (
        "apps.portfolios.tasks.fechar_risco_carteira",
        (run.pk, org),
    )


def test_v14_registry_incompleto_fecha_failed_no_banco_e_levanta(
    portfolio: Portfolio, fila: list[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    run = _run(portfolio, engine_version="")
    monkeypatch.setattr(
        "apps.portfolios.tasks.list_models",
        lambda: [m for m in list_models() if m != "gru"],
    )
    with pytest.raises(ModelsMissing, match="gru"):
        _abrir_risco_carteira(run.pk, portfolio.organization_id)
    linha = _relida(run)
    assert (linha.status, linha.engine_version) == (Status.FAILED, "")
    assert linha.finished_at is not None
    assert fila == []


def test_v14_execucao_ja_fechada_nao_escreve_nem_enfileira(
    portfolio: Portfolio, fila: list[Any]
) -> None:
    run = _run(portfolio, Status.FAILED, engine_version="")
    _abrir_risco_carteira(run.pk, portfolio.organization_id)
    assert _relida(run).engine_version == ""
    assert fila == []


def test_v14_abertura_reentregue_nao_regrava_nem_enfileira(
    portfolio: Portfolio, fila: list[Any]
) -> None:
    run = _run(portfolio, engine_version="0.0.0-de-antes")
    _abrir_risco_carteira(run.pk, portfolio.organization_id)
    assert _relida(run).engine_version == "0.0.0-de-antes"
    assert fila == []


def test_v14_enqueue_que_levanta_fecha_failed_e_sobe(
    portfolio: Portfolio, monkeypatch: pytest.MonkeyPatch
) -> None:
    def recusa(signature: Any) -> None:
        raise ConnectionRefusedError("redis fora do ar")

    monkeypatch.setattr("apps.portfolios.tasks._enqueue", recusa)
    run = _run(portfolio, engine_version="")
    with pytest.raises(ConnectionRefusedError):
        _abrir_risco_carteira(run.pk, portfolio.organization_id)
    linha = _relida(run)
    assert linha.status == Status.FAILED
    assert linha.finished_at is not None


# --- V-15: a tarefa por modelo ----------------------------------------------------------


def test_v15_calcula_o_historical_e_grava_os_dois(portfolio: Portfolio) -> None:
    run = _run(portfolio)
    _calcular_modelo_carteira(run.pk, portfolio.organization_id, "historical")
    resultados = _resultados(run)
    assert [(r.model_name, str(r.alpha), r.error) for r in resultados] == [
        ("historical", "0.0500", ""),
        ("historical", "0.0100", ""),
    ]
    assert all(r.var_latest is not None and r.var_latest > 0 for r in resultados)
    assert all(r.kupiec_passed is not None for r in resultados)


def test_v15_preco_reescrito_depois_do_pedido_e_serie_mudou(
    portfolio: Portfolio,
) -> None:
    run = _run(portfolio)
    linha = Price.objects.filter(asset__ticker="PETR4").order_by("date")[100]
    Price.objects.filter(pk=linha.pk).update(adj_close=linha.adj_close + Decimal("1"))

    _calcular_modelo_carteira(run.pk, portfolio.organization_id, "historical")

    assert [(r.error, r.var_latest) for r in _resultados(run)] == [
        ("serie mudou", None),
        ("serie mudou", None),
    ]


def _levanta(*args: object, **kwargs: object) -> None:
    raise RuntimeError("o motor quebrou")


def test_v15_excecao_vira_o_par_de_erro_e_nao_levanta(
    portfolio: Portfolio, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("apps.portfolios.tasks.run_experiment", _levanta)
    run = _run(portfolio)
    _calcular_modelo_carteira(run.pk, portfolio.organization_id, "historical")
    assert [r.error for r in _resultados(run)] == [
        "RuntimeError: o motor quebrou",
        "RuntimeError: o motor quebrou",
    ]


def _caminho_bom(monkeypatch: pytest.MonkeyPatch, portfolio: Portfolio) -> None:
    pass


def _caminho_serie_mudou(monkeypatch: pytest.MonkeyPatch, portfolio: Portfolio) -> None:
    linha = Price.objects.filter(asset__ticker="VALE3").order_by("date")[50]
    Price.objects.filter(pk=linha.pk).update(adj_close=linha.adj_close + Decimal("1"))


def _caminho_excecao(monkeypatch: pytest.MonkeyPatch, portfolio: Portfolio) -> None:
    monkeypatch.setattr("apps.portfolios.tasks.run_experiment", _levanta)


@pytest.mark.parametrize(
    "caminho",
    [_caminho_bom, _caminho_serie_mudou, _caminho_excecao],
    ids=["bom", "serie_mudou", "excecao"],
)
def test_v15_execucao_ja_fechada_nao_grava_em_nenhum_caminho(
    portfolio: Portfolio,
    monkeypatch: pytest.MonkeyPatch,
    caminho: Callable[[pytest.MonkeyPatch, Portfolio], None],
) -> None:
    run = _run(portfolio, Status.FAILED)
    caminho(monkeypatch, portfolio)
    _calcular_modelo_carteira(run.pk, portfolio.organization_id, "historical")
    assert _resultados(run) == []


def test_v15_reentregue_com_os_resultados_nao_chama_o_motor(
    portfolio: Portfolio, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = _run(portfolio)
    _calcular_modelo_carteira(run.pk, portfolio.organization_id, "historical")
    chamadas: list[object] = []

    def contando(*args: Any, **kwargs: Any) -> Any:
        chamadas.append(args)
        return run_experiment(*args, **kwargs)

    monkeypatch.setattr("apps.portfolios.tasks.run_experiment", contando)
    _calcular_modelo_carteira(run.pk, portfolio.organization_id, "historical")
    assert chamadas == []
    assert len(_resultados(run)) == 2


def test_v15_execucao_inexistente_so_registra(portfolio: Portfolio) -> None:
    _calcular_modelo_carteira(999_999, portfolio.organization_id, "historical")


# --- V-16: o fecho, sem concorrencia ----------------------------------------------------


def _grava(run: PortfolioRiskRun, quantos: int, com_erro: int) -> None:
    nomes = portfolio_config.PORTFOLIO_MODELS
    linhas = []
    for i in range(quantos):
        nome, alpha = nomes[i // 2], ("0.0500", "0.0100")[i % 2]
        erro = "RuntimeError: x" if i < com_erro else ""
        linhas.append(
            PortfolioRiskResult(
                run=run,
                model_name=nome,
                model_category="traditional",
                alpha=Decimal(alpha),
                hyperparameters={},
                var_latest=None if erro else Decimal("0.02"),
                error=erro,
            )
        )
    PortfolioRiskResult.unscoped.bulk_create(linhas)


@pytest.mark.parametrize(
    ("quantos", "com_erro", "esperado"),
    [
        (18, 0, Status.OK),
        (18, 2, Status.PARTIAL),
        (10, 0, Status.PARTIAL),
        (4, 4, Status.FAILED),
        (0, 0, Status.FAILED),
    ],
)
def test_v16_o_fecho_segue_status_for(
    portfolio: Portfolio, quantos: int, com_erro: int, esperado: str
) -> None:
    run = _run(portfolio)
    _grava(run, quantos, com_erro)
    _fechar_risco_carteira([None], run.pk, portfolio.organization_id)
    linha = _relida(run)
    assert linha.status == esperado
    assert linha.finished_at is not None


def test_v16_execucao_ja_fechada_o_fecho_nao_escreve(portfolio: Portfolio) -> None:
    fim = timezone.now() - timedelta(minutes=3)
    run = _run(portfolio, Status.FAILED, calculated_at=fim)
    _grava(run, 18, 0)
    _fechar_risco_carteira([None], run.pk, portfolio.organization_id)
    linha = _relida(run)
    assert (linha.status, linha.finished_at) == (Status.FAILED, fim)
