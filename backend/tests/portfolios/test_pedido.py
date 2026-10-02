"""M2.2a, T5: pedir o risco da carteira (RF-13; V-11, V-13, e V-07, V-09, V-19, V-20 pela rota de
risco).

O `send_task` e sempre o duplo `fila`, que anota o nome e os argumentos e nao fala com o Redis. Os
servicos sao chamados **sem contexto posto**; o `on_commit` so roda pelo
`captureOnCommitCallbacks`, e a fila vazia antes dele prova que o pedido sai depois do commit.

As series sao as de `dados.serie_longa`: 520 pregoes em dias uteis, acima do minimo de 503.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client
from django.utils import timezone
from pytest_django import DjangoCaptureOnCommitCallbacks, Settings

from apps.accounts.models import User
from apps.accounts.tenancy import organization_scope
from apps.assets.models import Asset, CollectionRun, Price
from apps.portfolios import config as portfolio_config
from apps.portfolios.errors import PortfolioError
from apps.portfolios.models import (
    Portfolio,
    PortfolioRiskResult,
    PortfolioRiskRun,
    PortfolioVersion,
)
from apps.portfolios.series import build
from apps.portfolios.services import replace_holdings, request_risk
from apps.risk import config as risk_config
from apps.risk.models import RiskRun
from config.celery import app
from tests.accounts.conftest import organizacao, usuario
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)
from tests.portfolios.dados import (
    Pessoas,
    acao,
    carteira,
    chave,
    erro,
    org_e_pessoas,
    serie_longa,
    sessao,
)

Status = RiskRun.Status
TAREFA = "apps.portfolios.tasks.abrir_risco_carteira"
PESOS = {"PETR4": "60.00", "VALE3": "40.00"}
VENCIDA = timedelta(minutes=61)
NAO_ACHOU = {
    "error": {
        "code": "portfolio_not_found",
        "message": "Carteira não encontrada.",
        "details": {},
    }
}


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict[str, Any]]]:
    """O duplo do `send_task`: anota o nome e os argumentos, nao fala com o Redis."""
    chamadas: list[tuple[str, dict[str, Any]]] = []

    def send_task(name: str, **kwargs: Any) -> None:
        chamadas.append((name, kwargs))

    monkeypatch.setattr(app, "send_task", send_task)
    return chamadas


@pytest.fixture
def broker_recusa(monkeypatch: pytest.MonkeyPatch) -> None:
    def send_task(name: str, **kwargs: Any) -> None:
        raise ConnectionRefusedError("redis fora do ar")

    monkeypatch.setattr(app, "send_task", send_task)


@pytest.fixture
def pessoas() -> Pessoas:
    serie_longa("PETR4")
    serie_longa("VALE3")
    serie_longa("ITUB4")
    return org_e_pessoas()


def _versao(portfolio: Portfolio) -> PortfolioVersion:
    return PortfolioVersion.unscoped.filter(portfolio=portfolio).order_by("-number")[0]


def _execucao_da_serie(
    portfolio: Portfolio, pessoa: User, status: str, calculated_at: datetime
) -> PortfolioRiskRun:
    """Uma execucao com o manifesto da serie de agora: o mesmo `as_of_date` e o mesmo hash."""
    versao = _versao(portfolio)
    with organization_scope(portfolio.organization_id):
        serie = build(versao)
        assert serie.price_run_id is not None
        return PortfolioRiskRun.objects.create(
            version=versao,
            requested_by=pessoa,
            calculated_at=calculated_at,
            finished_at=None if status == Status.RUNNING else calculated_at,
            status=status,
            engine_version="0.3.0",
            seed=42,
            train_window_days=252,
            first_date=serie.dates[0],
            as_of_date=serie.dates[-1],
            session_count=len(serie.dates),
            train_count=252,
            test_count=len(serie.dates) - 253,
            requested_models=list(portfolio_config.PORTFOLIO_MODELS),
            price_run_id=serie.price_run_id,
            series_sha256=serie.sha256,
        )


def _pede(pessoa: User, portfolio: Portfolio, now: datetime | None = None) -> None:
    request_risk(pessoa, str(portfolio.public_id), now or timezone.now())


def _execucoes(portfolio: Portfolio) -> list[PortfolioRiskRun]:
    return list(
        PortfolioRiskRun.unscoped.filter(version__portfolio=portfolio).order_by("pk")
    )


# --- V-11: as saidas do pedido ----------------------------------------------------------


@pytest.mark.django_db
def test_v11_serie_curta_e_insufficient_history_em_ordem_de_ticker(
    pessoas: Pessoas, fila: list[Any]
) -> None:
    acao(
        "ZZZZ3", [(date(2024, 1, 2), Decimal("10")), (date(2024, 1, 3), Decimal("11"))]
    )
    acao("AAAA3", [])
    portfolio = carteira(pessoas.admin, {"ZZZZ3": "50", "PETR4": "30", "AAAA3": "20"})

    with pytest.raises(PortfolioError) as falha:
        _pede(pessoas.admin, portfolio)

    assert falha.value.code == "insufficient_history"
    assert falha.value.message == "A carteira tem 0 pregões em comum; o mínimo é 503."
    assert falha.value.details == {
        "sessions": 0,
        "minimum": risk_config.MIN_SESSIONS,
        "assets": [
            {"ticker": "AAAA3", "first_date": None, "sessions": 0},
            {"ticker": "PETR4", "first_date": "2024-01-02", "sessions": 520},
            {"ticker": "ZZZZ3", "first_date": "2024-01-02", "sessions": 2},
        ],
    }
    assert _execucoes(portfolio) == []
    assert fila == []


@pytest.mark.django_db
def test_v11_running_nao_vencida_da_versao_devolve_sem_execucao_nova(
    pessoas: Pessoas,
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    existente = _execucao_da_serie(
        portfolio, pessoas.admin, Status.RUNNING, timezone.now() - timedelta(minutes=5)
    )
    with django_capture_on_commit_callbacks(execute=True):
        _pede(pessoas.member, portfolio)
    assert _execucoes(portfolio) == [existente]
    assert fila == []


@pytest.mark.django_db
@pytest.mark.parametrize("status", [Status.OK, Status.PARTIAL])
def test_v11_fechada_igual_e_portfolio_risk_up_to_date(
    pessoas: Pessoas, status: str, fila: list[Any]
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    fechada = _execucao_da_serie(
        portfolio, pessoas.admin, status, timezone.now() - timedelta(hours=2)
    )
    with pytest.raises(PortfolioError) as falha:
        _pede(pessoas.admin, portfolio)
    assert (falha.value.code, falha.value.details) == (
        "portfolio_risk_up_to_date",
        {"run_id": fechada.pk},
    )
    assert falha.value.message == (
        "O risco desta composição já está calculado com os preços atuais."
    )
    assert _execucoes(portfolio) == [fechada]
    assert fila == []


@pytest.mark.django_db
def test_v11_fechada_failed_nao_segura(
    pessoas: Pessoas,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    _execucao_da_serie(
        portfolio, pessoas.admin, Status.FAILED, timezone.now() - timedelta(hours=2)
    )
    with django_capture_on_commit_callbacks(execute=True):
        _pede(pessoas.admin, portfolio)
    assert [r.status for r in _execucoes(portfolio)] == [Status.FAILED, Status.RUNNING]


@pytest.mark.django_db
def test_v11_um_pregao_novo_em_todas_pede_de_novo(
    pessoas: Pessoas,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    _execucao_da_serie(
        portfolio, pessoas.admin, Status.OK, timezone.now() - timedelta(hours=2)
    )
    ultimo = Price.objects.filter(asset__ticker="PETR4").order_by("-date")[0]
    coleta = CollectionRun.objects.create(
        source="yahoo_chart", started_at=timezone.now()
    )
    for ticker in PESOS:
        Price.objects.create(
            asset=Asset.objects.get(ticker=ticker),
            date=ultimo.date + timedelta(days=3),
            open=Decimal("30"),
            high=Decimal("30"),
            low=Decimal("30"),
            close=Decimal("30"),
            adj_close=Decimal("30"),
            volume=1,
            log_return=None,
            run=coleta,
            updated_at=timezone.now(),
        )
    with django_capture_on_commit_callbacks(execute=True):
        _pede(pessoas.admin, portfolio)
    nova = _execucoes(portfolio)[-1]
    assert (nova.status, nova.as_of_date, nova.price_run_id) == (
        Status.RUNNING,
        ultimo.date + timedelta(days=3),
        coleta.pk,
    )


@pytest.mark.django_db
def test_v11_outra_carteira_da_organizacao_calculando_e_compute_busy(
    pessoas: Pessoas, fila: list[Any]
) -> None:
    calculando = carteira(pessoas.member, {"ITUB4": "50", "VALE3": "50"})
    _execucao_da_serie(
        calculando,
        pessoas.member,
        Status.RUNNING,
        timezone.now() - timedelta(minutes=5),
    )
    portfolio = carteira(pessoas.admin, PESOS)
    with pytest.raises(PortfolioError) as falha:
        _pede(pessoas.admin, portfolio)
    assert (falha.value.code, falha.value.details) == ("portfolio_compute_busy", {})
    assert falha.value.message == (
        "A organização já tem um cálculo de carteira em andamento."
    )
    assert _execucoes(portfolio) == []


def _de_outra_organizacao(slug: str) -> Portfolio:
    pessoa = usuario(organizacao(slug), f"admin@{slug}.test", role="admin")
    return carteira(pessoa, PESOS)


@pytest.mark.django_db
def test_v11_o_teto_global_e_portfolio_queue_full(
    pessoas: Pessoas, settings: Settings, fila: list[Any]
) -> None:
    settings.RUVOR_PORTFOLIO_COMPUTE_MAX = 2
    for slug in ("org-b", "org-c"):
        outra = _de_outra_organizacao(slug)
        _execucao_da_serie(
            outra,
            outra.created_by,
            Status.RUNNING,
            timezone.now() - timedelta(minutes=5),
        )
    portfolio = carteira(pessoas.admin, PESOS)
    with pytest.raises(PortfolioError) as falha:
        _pede(pessoas.admin, portfolio)
    assert (falha.value.code, falha.value.details) == ("portfolio_queue_full", {})
    assert falha.value.message == (
        "Muitos cálculos de carteira em andamento; tente mais tarde."
    )
    assert _execucoes(portfolio) == []


# --- V-11: a vencida nao conta, um teste por item ---------------------------------------


@pytest.mark.django_db
def test_v11_vencida_na_mesma_versao_nao_segura(
    pessoas: Pessoas,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    vencida = _execucao_da_serie(
        portfolio, pessoas.admin, Status.RUNNING, timezone.now() - VENCIDA
    )
    with django_capture_on_commit_callbacks(execute=True):
        _pede(pessoas.admin, portfolio)
    assert len(_execucoes(portfolio)) == 2
    assert _execucoes(portfolio)[0] == vencida


@pytest.mark.django_db
def test_v11_vencida_em_outra_carteira_da_organizacao_nao_segura(
    pessoas: Pessoas,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    outra = carteira(pessoas.member, {"ITUB4": "50", "VALE3": "50"})
    _execucao_da_serie(outra, pessoas.member, Status.RUNNING, timezone.now() - VENCIDA)
    portfolio = carteira(pessoas.admin, PESOS)
    with django_capture_on_commit_callbacks(execute=True):
        _pede(pessoas.admin, portfolio)
    assert len(_execucoes(portfolio)) == 1


@pytest.mark.django_db
def test_v11_vencida_de_outra_organizacao_nao_conta_no_teto(
    pessoas: Pessoas,
    settings: Settings,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    settings.RUVOR_PORTFOLIO_COMPUTE_MAX = 1
    outra = _de_outra_organizacao("org-b")
    _execucao_da_serie(
        outra, outra.created_by, Status.RUNNING, timezone.now() - VENCIDA
    )
    portfolio = carteira(pessoas.admin, PESOS)
    with django_capture_on_commit_callbacks(execute=True):
        _pede(pessoas.admin, portfolio)
    assert len(_execucoes(portfolio)) == 1


# --- V-11: o manifesto e a fila depois do commit ----------------------------------------


@pytest.mark.django_db
def test_v11_o_manifesto_e_o_da_serie_e_a_fila_so_depois_do_commit(
    pessoas: Pessoas,
    fila: list[tuple[str, dict[str, Any]]],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    agora = timezone.now()

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        _pede(pessoas.member, portfolio, agora)

    run = PortfolioRiskRun.unscoped.get(version__portfolio=portfolio)
    with organization_scope(portfolio.organization_id):
        serie = build(_versao(portfolio))
    assert run.version_id == _versao(portfolio).pk
    assert run.requested_by_id == pessoas.member.pk
    assert run.calculated_at == agora
    assert run.finished_at is None
    assert run.status == Status.RUNNING
    assert run.engine_version == ""
    assert run.seed == risk_config.DEFAULT_SEED
    assert run.train_window_days == risk_config.TRAIN_WINDOW_DAYS
    assert run.first_date == serie.dates[0]
    assert run.as_of_date == serie.dates[-1]
    assert run.session_count == len(serie.dates) == 520
    assert run.train_count == risk_config.TRAIN_WINDOW_DAYS
    assert run.test_count == 520 - 1 - risk_config.TRAIN_WINDOW_DAYS
    assert run.requested_models == list(portfolio_config.PORTFOLIO_MODELS)
    assert run.price_run_id == serie.price_run_id
    assert run.series_sha256 == serie.sha256

    assert fila == []  # so depois do commit
    assert len(callbacks) == 1
    callbacks[0]()
    assert fila == [(TAREFA, {"args": [run.pk, pessoas.acme.pk]})]


# --- V-13: o corretor que recusa --------------------------------------------------------


@pytest.mark.django_db
def test_v13_corretor_recusando_fecha_a_execucao_failed(
    pessoas: Pessoas,
    broker_recusa: None,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    with django_capture_on_commit_callbacks(execute=True):
        _pede(
            pessoas.admin, portfolio
        )  # sem contexto: o callback abre o escopo sozinho
    run = PortfolioRiskRun.unscoped.get(version__portfolio=portfolio)
    assert run.status == Status.FAILED
    assert run.finished_at is not None
    assert not PortfolioRiskResult.unscoped.filter(run=run).exists()


@pytest.mark.django_db
def test_v13_execucao_ja_fechada_antes_do_callback_nao_e_escrita(
    pessoas: Pessoas,
    broker_recusa: None,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        _pede(pessoas.admin, portfolio)
    run = PortfolioRiskRun.unscoped.get(version__portfolio=portfolio)
    fim = timezone.now()
    PortfolioRiskRun.unscoped.filter(pk=run.pk).update(
        status=Status.OK, finished_at=fim
    )
    callbacks[0]()
    run.refresh_from_db()
    assert (run.status, run.finished_at) == (Status.OK, fim)


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_v13_pela_rota_o_202_ja_traz_a_execucao_failed(broker_recusa: None) -> None:
    """So com commit de verdade o `on_commit` roda ao fim do `atomic`, antes de a view montar o
    corpo."""
    serie_longa("PETR4")
    serie_longa("VALE3")
    pessoas = org_e_pessoas()
    portfolio = carteira(pessoas.admin, PESOS)
    cliente = sessao(pessoas.admin)
    url = f"/api/v1/portfolios/{portfolio.public_id}/risk"

    resposta = cliente.post(url)

    assert resposta.status_code == 202, resposta.content
    corpo = resposta.json()["portfolio_risk"]
    assert corpo["in_progress"] is None
    assert corpo["latest"]["status"] == "failed"
    assert corpo["latest"]["finished_at"] is not None
    assert corpo["latest"]["results"] == []
    assert cliente.get(url).json() == resposta.json()


# --- a rota de risco: V-07, V-09, V-19, V-20 --------------------------------------------


def _url(portfolio_id: object) -> str:
    return f"/api/v1/portfolios/{portfolio_id}/risk"


@pytest.mark.django_db
def test_rota_post_202_e_get_200(pessoas: Pessoas, debug: bool) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    cliente = sessao(pessoas.member)
    resposta = cliente.post(_url(portfolio.public_id))
    assert resposta.status_code == 202, resposta.content
    corpo = resposta.json()["portfolio_risk"]
    assert corpo["latest"] is None
    assert corpo["in_progress"]["results_written"] == 0
    assert corpo["in_progress"]["results_expected"] == 18
    assert cliente.get(_url(portfolio.public_id)).status_code == 200


@pytest.mark.django_db
def test_rota_insufficient_history_409(pessoas: Pessoas, debug: bool) -> None:
    acao("AAAA3", [])
    portfolio = carteira(pessoas.admin, {"AAAA3": "50", "PETR4": "50"})
    corpo = erro(
        sessao(pessoas.admin).post(_url(portfolio.public_id)),
        409,
        "insufficient_history",
    )
    assert corpo["error"]["details"]["sessions"] == 0


@pytest.mark.django_db
def test_v09_o_mesmo_404_na_rota_de_risco(pessoas: Pessoas, debug: bool) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    ids = [
        (pessoas.de_fora, str(portfolio.public_id)),
        (pessoas.admin, "00000000-0000-4000-8000-000000000000"),
        (pessoas.admin, "abc"),
        (pessoas.admin, str(portfolio.public_id).upper()),
    ]
    for quem, pid in ids:
        cliente = sessao(quem)
        assert erro(cliente.get(_url(pid)), 404, "portfolio_not_found") == NAO_ACHOU
        assert erro(cliente.post(_url(pid)), 404, "portfolio_not_found") == NAO_ACHOU
    assert _execucoes(portfolio) == []


@pytest.mark.django_db
def test_v09_member_e_admin_pedem_e_leem_um_do_outro(pessoas: Pessoas) -> None:
    da_admin = carteira(pessoas.admin, PESOS)
    do_member = carteira(pessoas.member, {"ITUB4": "50", "VALE3": "50"})
    for quem, portfolio in ((pessoas.member, da_admin), (pessoas.admin, do_member)):
        cliente = sessao(quem)
        # a organizacao calcula uma carteira por vez: a do passo anterior fecha antes
        PortfolioRiskRun.unscoped.filter(status=Status.RUNNING).update(
            status=Status.FAILED, finished_at=timezone.now()
        )
        assert cliente.post(_url(portfolio.public_id)).status_code == 202
        assert cliente.get(_url(portfolio.public_id)).status_code == 200


@pytest.mark.django_db
def test_v07_depois_do_delete_a_rota_de_risco_e_404(
    pessoas: Pessoas, debug: bool
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    cliente = sessao(pessoas.admin)
    assert (
        cliente.delete(f"/api/v1/portfolios/{portfolio.public_id}").status_code == 204
    )
    erro(cliente.get(_url(portfolio.public_id)), 404, "portfolio_not_found")
    erro(cliente.post(_url(portfolio.public_id)), 404, "portfolio_not_found")


@pytest.mark.django_db
def test_v19_a_chave_le_o_risco_e_nao_pede(pessoas: Pessoas, debug: bool) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    cliente = chave(pessoas.member)
    assert cliente.get(_url(portfolio.public_id)).status_code == 200
    erro(cliente.post(_url(portfolio.public_id)), 403, "api_key_not_allowed")
    assert _execucoes(portfolio) == []


@pytest.mark.django_db
def test_v19_anonimo_recebe_401(pessoas: Pessoas, debug: bool, client: Client) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    chamadas: tuple[Callable[[], Any], ...] = (
        lambda: client.get(_url(portfolio.public_id)),
        lambda: client.post(_url(portfolio.public_id)),
    )
    for chamada in chamadas:
        erro(chamada(), 401, "not_authenticated")


@pytest.mark.django_db
def test_v20_pedir_exige_csrf(pessoas: Pessoas, debug: bool) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    cliente = sessao(pessoas.admin, csrf=True)
    assert cliente.post(_url(portfolio.public_id)).status_code == 403
    assert _execucoes(portfolio) == []
    assert cliente.get("/api/v1/auth/csrf").status_code == 204
    token = cliente.cookies["csrftoken"].value
    resposta = cliente.post(_url(portfolio.public_id), HTTP_X_CSRFTOKEN=token)
    assert resposta.status_code == 202, resposta.content


@pytest.mark.django_db
def test_trocar_a_composicao_tira_o_latest_e_deixa_pedir(
    pessoas: Pessoas,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    portfolio = carteira(pessoas.admin, PESOS)
    antiga = _execucao_da_serie(
        portfolio, pessoas.admin, Status.OK, timezone.now() - timedelta(hours=2)
    )
    replace_holdings(
        pessoas.admin,
        str(portfolio.public_id),
        [
            {"ticker": "PETR4", "weight": Decimal("50")},
            {"ticker": "ITUB4", "weight": Decimal("50")},
        ],
    )
    with django_capture_on_commit_callbacks(execute=True):
        _pede(pessoas.admin, portfolio)
    execucoes = _execucoes(portfolio)
    assert execucoes[0] == antiga
    assert execucoes[1].version.number == 2
