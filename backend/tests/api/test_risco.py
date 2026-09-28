"""V-13 e metade do V-17: o `/risk` nos estados (RF-13, RF-18).

O corpo e lista fechada: o teste confere o **conjunto** de chaves por igualdade, nos objetos
aninhados tambem (V-11). Os instantes sao relativos a `timezone.now()`: dentro do prazo e
alguns minutos atras, fora do prazo e bem mais que os 30 minutos — a margem cobre o
intervalo entre montar os dados e o `GET`, que le o relogio de novo.

O `GET` nao escreve no banco: o pedido gravado aberto e vencido pelo relogio sai `expired`
no corpo e continua aberto na linha (RF-18). A outra metade do V-17 — o `POST` que o grava
`expired` — e da T12.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client
from django.utils import timezone
from pytest_django import Settings

from apps.api.models import ComputeRequest
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk.models import RiskResult, RiskRun

if TYPE_CHECKING:
    # so existe nos stubs: e o tipo que o cliente de teste devolve
    from django.test.client import _MonkeyPatchedWSGIResponse

pytestmark = pytest.mark.django_db

SAO_PAULO = ZoneInfo("America/Sao_Paulo")

# dentro do prazo de 30 min, e fora dele com folga
DENTRO = timedelta(minutes=5)
FORA = timedelta(minutes=45)

CHAVES_RISCO = {"ticker", "covered", "latest", "in_progress", "request"}
CHAVES_LATEST = {
    "id",
    "calculated_at",
    "finished_at",
    "status",
    "engine_version",
    "seed",
    "train_window_days",
    "as_of_date",
    "first_price_date",
    "price_count",
    "train_count",
    "test_count",
    "price_run",
    "requested_models",
    "full_recompute",
    "results",
}
CHAVES_COLETA = {"id", "source", "started_at", "finished_at"}
CHAVES_RESULTADO = {
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
    "basel_zone",
    "adequate",
    "error",
    "reused_snapshots",
    "trained_snapshots",
}
CHAVES_EM_ANDAMENTO = {
    "id",
    "calculated_at",
    "requested_models",
    "results_written",
    "results_expected",
}
CHAVES_PEDIDO = {
    "id",
    "status",
    "requested_at",
    "finished_at",
    "reason",
    "error",
    "risk_run_id",
}

Status = ComputeRequest.Status


@pytest.fixture(autouse=True)
def prazo(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)


@pytest.fixture
def agora() -> datetime:
    return timezone.now()


def _iso(instante: datetime) -> str:
    """O instante como a API o devolve: no fuso de `TIME_ZONE`, com deslocamento."""
    return instante.astimezone(SAO_PAULO).isoformat()


def _risco(client: Client, ticker: str = "ITUB4") -> dict[str, Any]:
    resposta: _MonkeyPatchedWSGIResponse = client.get(f"/api/v1/assets/{ticker}/risk")
    assert resposta.status_code == 200, resposta.content
    assert resposta["Content-Type"] == "application/json"
    corpo: dict[str, Any] = resposta.json()
    assert set(corpo) == CHAVES_RISCO
    if corpo["latest"] is not None:
        assert set(corpo["latest"]) == CHAVES_LATEST
        assert set(corpo["latest"]["price_run"]) == CHAVES_COLETA
        assert all(set(r) == CHAVES_RESULTADO for r in corpo["latest"]["results"])
    if corpo["in_progress"] is not None:
        assert set(corpo["in_progress"]) == CHAVES_EM_ANDAMENTO
    if corpo["request"] is not None:
        assert set(corpo["request"]) == CHAVES_PEDIDO
    return corpo


def _ativo(ticker: str, agora: datetime, com_preco: bool = True) -> Asset:
    ativo = Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )
    if com_preco:
        Price.objects.create(
            asset=ativo,
            date=date(2026, 9, 25),
            open=Decimal("30"),
            high=Decimal("31"),
            low=Decimal("29"),
            close=Decimal("30.5"),
            adj_close=Decimal("30.25"),
            volume=1000,
            log_return=None,
            run=CollectionRun.objects.create(source="teste", started_at=agora),
            updated_at=agora,
        )
    return ativo


def _execucao(
    asset: Asset,
    status: str,
    calculated_at: datetime,
    requested_models: list[str] | None = None,
) -> RiskRun:
    coleta = CollectionRun.objects.create(
        source="yahoo_chart",
        started_at=calculated_at - timedelta(minutes=10),
        finished_at=calculated_at - timedelta(minutes=9),
        status=CollectionRun.Status.OK,
    )
    return RiskRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=None
        if status == RiskRun.Status.RUNNING
        else calculated_at + timedelta(minutes=2),
        engine_version="0.3.0",
        seed=42,
        train_window_days=252,
        as_of_date=date(2026, 9, 25),
        first_price_date=date(2016, 9, 26),
        price_count=2480,
        train_count=252,
        test_count=2227,
        price_run=coleta,
        requested_by=None,
        status=status,
        requested_models=requested_models or ["historical", "parametric"],
        full_recompute=False,
    )


def _resultado(run: RiskRun, model_name: str, alpha: str, erro: str = "") -> RiskResult:
    if erro:
        return RiskResult.objects.create(
            run=run,
            model_name=model_name,
            model_category="parametric",
            alpha=Decimal(alpha),
            hyperparameters={},
            error=erro,
        )
    return RiskResult.objects.create(
        run=run,
        model_name=model_name,
        model_category="historical" if model_name == "historical" else "parametric",
        alpha=Decimal(alpha),
        hyperparameters={"window": 252},
        var_latest=Decimal("0.0234"),
        var_mean=Decimal("0.0212"),
        violations=110,
        expected_violations=Decimal("111.35"),
        kupiec_passed=True,
        kupiec_p_value=Decimal("0.8912"),
        christoffersen_passed=False,
        christoffersen_p_value=Decimal("0.0123"),
        dq_passed=True,
        dq_p_value=Decimal("0.4567"),
        basel_zone="green",
        adequate=False,
        reused_snapshots=None,
        trained_snapshots=None,
    )


def _pedido(
    asset: Asset,
    status: str,
    requested_at: datetime,
    *,
    finished_at: datetime | None = None,
    reason: str = "",
    error: str = "",
    risk_run: RiskRun | None = None,
) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset,
        status=status,
        requested_at=requested_at,
        finished_at=finished_at,
        reason=reason,
        error=error,
        risk_run=risk_run,
    )


# --- nunca calculado ---------------------------------------------------------------------


def test_nunca_calculado_tem_tudo_nulo_e_covered_pelo_preco(
    client: Client, agora: datetime
) -> None:
    _ativo("ITUB4", agora)
    _ativo("SEMP3", agora, com_preco=False)

    assert _risco(client, "itub4") == {
        "ticker": "ITUB4",
        "covered": True,
        "latest": None,
        "in_progress": None,
        "request": None,
    }
    assert _risco(client, "SEMP3") == {
        "ticker": "SEMP3",
        "covered": False,
        "latest": None,
        "in_progress": None,
        "request": None,
    }


@pytest.mark.parametrize("ticker", ["zzzz9", "ZZZZ9"])
def test_ticker_ausente_e_asset_not_found(
    client: Client, debug: bool, ticker: str
) -> None:
    resposta = client.get(f"/api/v1/assets/{ticker}/risk")

    assert resposta.status_code == 404, resposta.content
    assert resposta["Content-Type"] == "application/json"
    assert resposta.json() == {
        "error": {
            "code": "asset_not_found",
            "message": "Ativo ZZZZ9 não existe.",
            "details": {"ticker": "ZZZZ9"},
        }
    }


# --- as execucoes ------------------------------------------------------------------------


def test_so_running_recente_aparece_em_in_progress(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora)
    running = _execucao(
        ativo,
        RiskRun.Status.RUNNING,
        agora - DENTRO,
        requested_models=["historical", "parametric", "ewma"],
    )
    _resultado(running, "historical", "0.0500")
    _resultado(running, "historical", "0.0100")

    corpo = _risco(client)

    assert corpo == {
        "ticker": "ITUB4",
        "covered": True,
        "latest": None,
        "in_progress": {
            "id": running.pk,
            "calculated_at": _iso(running.calculated_at),
            "requested_models": ["historical", "parametric", "ewma"],
            "results_written": 2,
            # len(requested_models) x len(ALPHAS)
            "results_expected": 6,
        },
        "request": None,
    }


def test_ok_traz_o_manifesto_e_os_resultados_em_ordem(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora)
    run = _execucao(ativo, RiskRun.Status.OK, agora - timedelta(hours=3))
    # fora de ordem de proposito: a rota entrega por model_name, depois alpha decrescente
    _resultado(run, "parametric", "0.0100")
    _resultado(run, "historical", "0.0100")
    _resultado(run, "parametric", "0.0500")
    _resultado(run, "historical", "0.0500")
    # a execucao fechada mais velha nao e o latest
    _execucao(ativo, RiskRun.Status.OK, agora - timedelta(days=1))
    # execucao de outro ativo nao vaza
    _execucao(_ativo("PETR4", agora), RiskRun.Status.OK, agora - timedelta(hours=1))

    corpo = _risco(client)

    assert corpo["in_progress"] is None
    assert corpo["request"] is None
    latest = corpo["latest"]
    coleta = run.price_run
    assert {k: v for k, v in latest.items() if k != "results"} == {
        "id": run.pk,
        "calculated_at": _iso(run.calculated_at),
        "finished_at": _iso(run.finished_at),  # type: ignore[arg-type]
        "status": "ok",
        "engine_version": "0.3.0",
        "seed": 42,
        "train_window_days": 252,
        "as_of_date": "2026-09-25",
        "first_price_date": "2016-09-26",
        "price_count": 2480,
        "train_count": 252,
        "test_count": 2227,
        # a coleta de preco que a execucao usou, e a data dela (D-15)
        "price_run": {
            "id": coleta.pk,
            "source": "yahoo_chart",
            "started_at": _iso(coleta.started_at),
            "finished_at": _iso(coleta.finished_at),  # type: ignore[arg-type]
        },
        "requested_models": ["historical", "parametric"],
        "full_recompute": False,
    }
    assert [(r["model_name"], r["alpha"]) for r in latest["results"]] == [
        ("historical", "0.0500"),
        ("historical", "0.0100"),
        ("parametric", "0.0500"),
        ("parametric", "0.0100"),
    ]
    # decimal como string, com as casas da coluna
    assert latest["results"][0] == {
        "model_name": "historical",
        "model_category": "historical",
        "alpha": "0.0500",
        "hyperparameters": {"window": 252},
        "var_latest": "0.0234000000",
        "var_mean": "0.0212000000",
        "violations": 110,
        "expected_violations": "111.350000",
        "kupiec_passed": True,
        "kupiec_p_value": "0.8912000000",
        "christoffersen_passed": False,
        "christoffersen_p_value": "0.0123000000",
        "dq_passed": True,
        "dq_p_value": "0.4567000000",
        "basel_zone": "green",
        "adequate": False,
        "error": "",
        "reused_snapshots": None,
        "trained_snapshots": None,
    }


def test_partial_traz_o_modelo_falho_com_o_erro(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora)
    run = _execucao(ativo, RiskRun.Status.PARTIAL, agora - timedelta(hours=3))
    _resultado(run, "historical", "0.0500")
    _resultado(run, "historical", "0.0100")
    _resultado(run, "parametric", "0.0500", erro="ValueError: serie constante")
    _resultado(run, "parametric", "0.0100", erro="ValueError: serie constante")

    latest = _risco(client)["latest"]

    assert latest["id"] == run.pk
    assert latest["status"] == "partial"
    assert len(latest["results"]) == 4
    falho = latest["results"][2]
    assert falho == {
        "model_name": "parametric",
        "model_category": "parametric",
        "alpha": "0.0500",
        "hyperparameters": {},
        "var_latest": None,
        "var_mean": None,
        "violations": None,
        "expected_violations": None,
        "kupiec_passed": None,
        "kupiec_p_value": None,
        "christoffersen_passed": None,
        "christoffersen_p_value": None,
        "dq_passed": None,
        "dq_p_value": None,
        "basel_zone": None,
        "adequate": None,
        "error": "ValueError: serie constante",
        "reused_snapshots": None,
        "trained_snapshots": None,
    }
    assert latest["results"][0]["error"] == ""


def test_failed_e_o_latest_sem_esconder_a_falha(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora)
    # a ok mais velha nao encobre a failed mais nova
    _execucao(ativo, RiskRun.Status.OK, agora - timedelta(days=1))
    run = _execucao(ativo, RiskRun.Status.FAILED, agora - timedelta(hours=3))
    _resultado(run, "historical", "0.0500", erro="RuntimeError: sem dados")

    corpo = _risco(client)

    assert corpo["latest"]["id"] == run.pk
    assert corpo["latest"]["status"] == "failed"
    assert [r["error"] for r in corpo["latest"]["results"]] == [
        "RuntimeError: sem dados"
    ]
    assert corpo["in_progress"] is None


def test_fechado_mais_running_novo_mostra_os_dois(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora)
    fechado = _execucao(ativo, RiskRun.Status.OK, agora - timedelta(hours=3))
    running = _execucao(ativo, RiskRun.Status.RUNNING, agora - DENTRO)

    corpo = _risco(client)

    assert corpo["latest"]["id"] == fechado.pk
    assert corpo["in_progress"] == {
        "id": running.pk,
        "calculated_at": _iso(running.calculated_at),
        "requested_models": ["historical", "parametric"],
        "results_written": 0,
        "results_expected": 4,
    }


def test_running_mais_velho_que_o_latest_nao_aparece(
    client: Client, agora: datetime
) -> None:
    # dentro do prazo: so o "mais nova que o latest" o tira
    ativo = _ativo("ITUB4", agora)
    _execucao(ativo, RiskRun.Status.RUNNING, agora - timedelta(minutes=20))
    fechado = _execucao(ativo, RiskRun.Status.OK, agora - timedelta(minutes=10))

    corpo = _risco(client)

    assert corpo["latest"]["id"] == fechado.pk
    assert corpo["in_progress"] is None


def test_running_mais_novo_que_o_latest_mas_fora_do_prazo_nao_aparece(
    client: Client, agora: datetime
) -> None:
    # mais nova que o latest: so o prazo a tira -- e execucao presa
    ativo = _ativo("ITUB4", agora)
    fechado = _execucao(ativo, RiskRun.Status.OK, agora - timedelta(hours=3))
    _execucao(ativo, RiskRun.Status.RUNNING, agora - FORA)

    corpo = _risco(client)

    assert corpo["latest"]["id"] == fechado.pk
    assert corpo["in_progress"] is None


def test_running_fora_do_prazo_sem_latest_nao_aparece(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora)
    _execucao(ativo, RiskRun.Status.RUNNING, agora - FORA)

    corpo = _risco(client)

    assert corpo["latest"] is None
    assert corpo["in_progress"] is None


# --- o pedido ----------------------------------------------------------------------------


def test_pedido_aberto_sem_risk_run(client: Client, agora: datetime) -> None:
    ativo = _ativo("ITUB4", agora, com_preco=False)
    pedido = _pedido(ativo, Status.QUEUED, agora - DENTRO)

    corpo = _risco(client)

    assert corpo == {
        "ticker": "ITUB4",
        "covered": False,
        "latest": None,
        "in_progress": None,
        "request": {
            "id": pedido.pk,
            "status": "queued",
            "requested_at": _iso(pedido.requested_at),
            "finished_at": None,
            "reason": "",
            "error": "",
            "risk_run_id": None,
        },
    }


def test_pedido_failed_aparece_com_o_motivo_e_o_erro(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora, com_preco=False)
    # o ultimo pedido, nao o primeiro
    _pedido(
        ativo,
        Status.DONE,
        agora - timedelta(days=2),
        finished_at=agora - timedelta(days=2),
        reason="calculado",
    )
    pedido = _pedido(
        ativo,
        Status.FAILED,
        agora - timedelta(hours=2),
        finished_at=agora - timedelta(hours=2) + timedelta(seconds=30),
        reason="falhou na coleta",
        error="HTTPError: 500",
    )

    assert _risco(client)["request"] == {
        "id": pedido.pk,
        "status": "failed",
        "requested_at": _iso(pedido.requested_at),
        "finished_at": _iso(pedido.finished_at),  # type: ignore[arg-type]
        "reason": "falhou na coleta",
        "error": "HTTPError: 500",
        "risk_run_id": None,
    }


def test_pedido_done_por_serie_curta_aparece_com_o_motivo(
    client: Client, agora: datetime
) -> None:
    ativo = _ativo("ITUB4", agora)
    pedido = _pedido(
        ativo,
        Status.DONE,
        agora - timedelta(hours=1),
        finished_at=agora - timedelta(minutes=59),
        reason="serie curta (120 pregoes, minimo 503)",
    )

    corpo = _risco(client)

    assert corpo["covered"] is True
    assert corpo["latest"] is None
    assert corpo["request"] == {
        "id": pedido.pk,
        "status": "done",
        "requested_at": _iso(pedido.requested_at),
        "finished_at": _iso(pedido.finished_at),  # type: ignore[arg-type]
        "reason": "serie curta (120 pregoes, minimo 503)",
        "error": "",
        "risk_run_id": None,
    }


def test_pedido_ligado_traz_o_id_da_execucao(client: Client, agora: datetime) -> None:
    ativo = _ativo("ITUB4", agora)
    running = _execucao(ativo, RiskRun.Status.RUNNING, agora - DENTRO)
    pedido = _pedido(
        ativo, Status.RUNNING, agora - DENTRO - timedelta(minutes=1), risk_run=running
    )

    corpo = _risco(client)

    assert corpo["request"]["id"] == pedido.pk
    assert corpo["request"]["status"] == "running"
    assert corpo["request"]["risk_run_id"] == running.pk
    assert corpo["in_progress"]["id"] == running.pk


@pytest.mark.parametrize("gravado", [Status.QUEUED, Status.RUNNING])
def test_pedido_vencido_sai_expired_e_continua_aberto_no_banco(
    client: Client, agora: datetime, gravado: str
) -> None:
    ativo = _ativo("ITUB4", agora, com_preco=False)
    pedido = _pedido(ativo, gravado, agora - FORA)

    corpo = _risco(client)

    assert corpo["request"] == {
        "id": pedido.pk,
        "status": "expired",
        "requested_at": _iso(pedido.requested_at),
        "finished_at": None,
        "reason": "expirado (30 min)",
        "error": "",
        "risk_run_id": None,
    }
    # o GET nao escreve (RF-18): a linha continua como estava
    linha = ComputeRequest.objects.get(pk=pedido.pk)
    assert linha.status == gravado
    assert linha.finished_at is None
    assert linha.reason == ""
