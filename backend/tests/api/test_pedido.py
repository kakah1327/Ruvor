"""V-16, a metade do `POST` do V-17 e o V-18: o pedido de calculo sob demanda (RF-14 a RF-19).

- **V-16**: cada linha da tabela do RF-14, com o codigo e o corpo. Todo 202 tem o corpo do
  `/risk` -- o teste o compara com o `GET` feito logo depois, que nao escreve no banco --; o
  409 traz o `/risk` em `details`; o 429, `{"max": N}`. Uma `running` mais velha que o prazo
  **nao** impede o pedido novo. Os erros rodam com `DEBUG` ligado e desligado (`debug`).
- **V-17**, a metade do `POST`: o pedido aberto vencido e gravado `expired` e outro abre. E o
  caso que pega o `ApiError` levantado **dentro** do `atomic`: com um pedido vencido do ativo
  A, o `POST` que termina em 409 (B coberto) e o que termina em 429 deixam o pedido de A
  `expired` **no banco** -- levantado de dentro, o `atomic` desfaria o `expire_stale`.
- **V-18**: o `send_task` substituido por duplo. O nome registrado e `args=[id]`, e nada antes
  de o `on_commit` rodar (`django_capture_on_commit_callbacks`); o broker recusando grava o
  pedido `failed` (teste `db`); a resposta 202 com ele em `request` so se observa num teste
  `transaction=True` -- so ali o `on_commit` roda ao fim do `atomic` da view, antes do
  `risk_body`; num teste `db`, a captura roda os callbacks depois de o corpo montado. E todo
  nome que `apps/api/` passa a `send_task`, lido do codigo por `ast`, esta no registro do
  `worker`, conferido em subprocesso (molde de `tests/test_celery_registro.py`).

Nenhum teste fala com o Redis: a fixture `fila` troca o `send_task` da aplicacao Celery em
todos eles.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client
from django.utils import timezone
from pytest_django import Settings

import apps.api
from apps.api.models import ComputeRequest
from apps.api.ondemand import (
    OPEN_STATUSES,
    REASON_BROKER_REFUSED,
    enqueue_chain,
    expired_reason,
)
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk.models import RiskRun
from config.celery import app
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

Status = ComputeRequest.Status

SAO_PAULO = ZoneInfo("America/Sao_Paulo")
TAREFA = "apps.assets.tasks.calcular_sob_demanda"

# dentro do prazo de 30 min, e fora dele com folga
DENTRO = timedelta(minutes=5)
FORA = timedelta(minutes=45)

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_RAIZ_API = Path(apps.api.__file__).parent


@pytest.fixture(autouse=True)
def prazo(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)
    settings.RUVOR_ON_DEMAND_MAX = 3


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


# --- os dados ------------------------------------------------------------------------------


def _ativo(
    ticker: str, status: str = Asset.Status.ACTIVE, com_preco: bool = False
) -> Asset:
    agora = timezone.now()
    ativo = Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
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


def _execucao(asset: Asset, status: str, calculated_at: datetime) -> RiskRun:
    coleta = CollectionRun.objects.create(
        source="yahoo_chart", started_at=calculated_at - timedelta(minutes=10)
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
        requested_models=["historical"],
        full_recompute=False,
    )


def _pedido(asset: Asset, status: str, requested_at: datetime) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset, status=status, requested_at=requested_at
    )


def _iso(instante: datetime) -> str:
    return instante.astimezone(SAO_PAULO).isoformat()


def _post(client: Client, ticker: str) -> _MonkeyPatchedWSGIResponse:
    resposta: _MonkeyPatchedWSGIResponse = client.post(f"/api/v1/assets/{ticker}/risk")
    assert resposta["Content-Type"] == "application/json"
    return resposta


def _aceito(client: Client, ticker: str) -> dict[str, Any]:
    """O `POST` que responde 202: o corpo e o do `/risk`, igual ao `GET` feito logo depois."""
    resposta = _post(client, ticker)
    assert resposta.status_code == 202, resposta.content
    corpo: dict[str, Any] = resposta.json()
    leitura = client.get(f"/api/v1/assets/{ticker}/risk")
    assert leitura.status_code == 200, leitura.content
    assert corpo == leitura.json()
    return corpo


def _erro(
    resposta: _MonkeyPatchedWSGIResponse, status: int, code: str
) -> dict[str, Any]:
    assert resposta.status_code == status, resposta.content
    corpo: dict[str, Any] = resposta.json()
    assert set(corpo) == {"error"}
    assert set(corpo["error"]) == {"code", "message", "details"}
    assert corpo["error"]["code"] == code
    erro: dict[str, Any] = corpo["error"]
    return erro


def _abertos() -> list[tuple[str, str]]:
    return sorted(
        ComputeRequest.objects.filter(status__in=OPEN_STATUSES).values_list(
            "asset__ticker", "status"
        )
    )


# --- V-16: as linhas do RF-14 --------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("ticker", ["zzzz9", "ZZZZ9"])
def test_ticker_fora_do_catalogo_e_asset_not_found(
    client: Client, debug: bool, ticker: str
) -> None:
    erro = _erro(_post(client, ticker), 404, "asset_not_found")

    assert erro == {
        "code": "asset_not_found",
        "message": "Ativo ZZZZ9 não existe.",
        "details": {"ticker": "ZZZZ9"},
    }
    assert ComputeRequest.objects.count() == 0


@pytest.mark.django_db
def test_ativo_inativo_e_asset_inactive(client: Client, debug: bool) -> None:
    _ativo("VELH3", status=Asset.Status.INACTIVE)

    erro = _erro(_post(client, "velh3"), 422, "asset_inactive")

    assert erro["details"] == {"ticker": "VELH3"}
    assert erro["message"]
    assert ComputeRequest.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("status", [Status.QUEUED, Status.RUNNING])
def test_pedido_aberto_do_ativo_e_202_com_o_mesmo_pedido(
    client: Client, fila: list[Any], status: str
) -> None:
    aberto = _pedido(_ativo("NOVO3"), status, timezone.now() - DENTRO)

    corpo = _aceito(client, "novo3")

    assert corpo["request"]["id"] == aberto.pk
    assert corpo["request"]["status"] == status
    assert ComputeRequest.objects.count() == 1
    assert fila == []


@pytest.mark.django_db
def test_running_recente_sem_fechada_e_202_sem_pedido_novo(
    client: Client, fila: list[Any]
) -> None:
    ativo = _ativo("NOVO3", com_preco=True)
    running = _execucao(ativo, RiskRun.Status.RUNNING, timezone.now() - DENTRO)

    corpo = _aceito(client, "NOVO3")

    assert corpo["in_progress"]["id"] == running.pk
    assert corpo["request"] is None
    assert ComputeRequest.objects.count() == 0
    assert fila == []


@pytest.mark.django_db
def test_running_recente_mais_nova_que_a_fechada_e_202_sem_pedido_novo(
    client: Client, fila: list[Any]
) -> None:
    ativo = _ativo("ITUB4", com_preco=True)
    fechada = _execucao(ativo, RiskRun.Status.OK, timezone.now() - timedelta(days=1))
    running = _execucao(ativo, RiskRun.Status.RUNNING, timezone.now() - DENTRO)

    corpo = _aceito(client, "ITUB4")

    assert corpo["latest"]["id"] == fechada.pk
    assert corpo["in_progress"]["id"] == running.pk
    assert corpo["request"] is None
    assert ComputeRequest.objects.count() == 0
    assert fila == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status", [RiskRun.Status.OK, RiskRun.Status.PARTIAL, RiskRun.Status.FAILED]
)
def test_ativo_com_execucao_fechada_e_409_com_o_risk_em_details(
    client: Client, debug: bool, status: str
) -> None:
    ativo = _ativo("ITUB4", com_preco=True)
    fechada = _execucao(ativo, status, timezone.now() - timedelta(days=1))

    erro = _erro(_post(client, "itub4"), 409, "asset_already_covered")

    leitura = client.get("/api/v1/assets/ITUB4/risk").json()
    assert erro["details"] == leitura
    assert erro["details"]["latest"]["id"] == fechada.pk
    assert erro["message"]
    assert ComputeRequest.objects.count() == 0


@pytest.mark.django_db
def test_running_mais_velha_que_a_fechada_nao_impede_o_409(
    client: Client, debug: bool
) -> None:
    ativo = _ativo("ITUB4", com_preco=True)
    _execucao(ativo, RiskRun.Status.RUNNING, timezone.now() - timedelta(minutes=20))
    _execucao(ativo, RiskRun.Status.OK, timezone.now() - DENTRO)

    _erro(_post(client, "ITUB4"), 409, "asset_already_covered")

    assert ComputeRequest.objects.count() == 0


@pytest.mark.django_db
def test_teto_de_abertos_e_429_com_o_max(
    client: Client, debug: bool, settings: Settings
) -> None:
    settings.RUVOR_ON_DEMAND_MAX = 2
    _pedido(_ativo("AAAA3"), Status.QUEUED, timezone.now() - DENTRO)
    _pedido(_ativo("BBBB3"), Status.RUNNING, timezone.now() - DENTRO)
    _ativo("NOVO3")

    erro = _erro(_post(client, "NOVO3"), 429, "on_demand_queue_full")

    assert erro["details"] == {"max": 2}
    assert erro["message"]
    assert _abertos() == [("AAAA3", Status.QUEUED), ("BBBB3", Status.RUNNING)]


@pytest.mark.django_db
def test_pedido_fechado_nao_conta_para_o_teto(
    client: Client, settings: Settings
) -> None:
    settings.RUVOR_ON_DEMAND_MAX = 1
    agora = timezone.now()
    for ticker, status in [("AAAA3", Status.DONE), ("BBBB3", Status.FAILED)]:
        _pedido(_ativo(ticker), status, agora - DENTRO)
    _ativo("NOVO3")

    corpo = _aceito(client, "NOVO3")

    assert corpo["request"]["status"] == Status.QUEUED
    assert _abertos() == [("NOVO3", Status.QUEUED)]


@pytest.mark.django_db
def test_nunca_calculado_e_202_com_o_pedido_novo_queued(
    client: Client, fila: list[Any]
) -> None:
    _ativo("NOVO3", com_preco=True)  # com preco e sem risco ainda e "nunca calculado"
    antes = timezone.now()

    corpo = _aceito(client, "novo3")

    depois = timezone.now()
    novo = ComputeRequest.objects.get()
    assert (novo.asset.ticker, novo.status) == ("NOVO3", Status.QUEUED)
    assert antes <= novo.requested_at <= depois
    assert corpo == {
        "ticker": "NOVO3",
        "covered": True,
        "latest": None,
        "in_progress": None,
        "request": {
            "id": novo.pk,
            "status": "queued",
            "requested_at": _iso(novo.requested_at),
            "finished_at": None,
            "reason": "",
            "error": "",
            "risk_run_id": None,
        },
    }
    assert fila == []  # o `on_commit` nao roda num teste `db` sem captura


@pytest.mark.django_db
def test_running_mais_velha_que_o_prazo_nao_impede_o_pedido_novo(
    client: Client,
) -> None:
    ativo = _ativo("NOVO3", com_preco=True)
    _execucao(ativo, RiskRun.Status.RUNNING, timezone.now() - FORA)

    corpo = _aceito(client, "NOVO3")

    assert corpo["in_progress"] is None
    assert corpo["latest"] is None
    assert corpo["request"]["status"] == Status.QUEUED
    assert _abertos() == [("NOVO3", Status.QUEUED)]


# --- V-17: o `POST` grava os vencidos -----------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("status", [Status.QUEUED, Status.RUNNING])
def test_post_grava_o_pedido_vencido_expired_e_abre_outro(
    client: Client, status: str
) -> None:
    vencido = _pedido(_ativo("NOVO3"), status, timezone.now() - FORA)

    corpo = _aceito(client, "NOVO3")

    gravado = ComputeRequest.objects.get(pk=vencido.pk)
    assert gravado.status == Status.EXPIRED
    assert gravado.reason == expired_reason() == "expirado (30 min)"
    assert gravado.finished_at is not None
    novo = ComputeRequest.objects.get(status=Status.QUEUED)
    assert novo.pk != vencido.pk
    assert corpo["request"]["id"] == novo.pk


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("desfecho", "status", "code"),
    [
        ("coberto", 409, "asset_already_covered"),
        ("teto", 429, "on_demand_queue_full"),
    ],
)
def test_vencido_de_outro_ativo_fica_expired_mesmo_com_409_ou_429(
    client: Client,
    debug: bool,
    settings: Settings,
    desfecho: str,
    status: int,
    code: str,
) -> None:
    """O `ApiError` levantado de dentro do `atomic` desfaria o `expire_stale`: o pedido
    vencido do ativo A continuaria aberto no banco."""
    agora = timezone.now()
    vencido = _pedido(_ativo("AAAA3"), Status.QUEUED, agora - FORA)
    if desfecho == "coberto":
        alvo = _ativo("BBBB3", com_preco=True)
        _execucao(alvo, RiskRun.Status.OK, agora - timedelta(days=1))
    else:
        settings.RUVOR_ON_DEMAND_MAX = 1
        _pedido(_ativo("CCCC3"), Status.RUNNING, agora - DENTRO)
        _ativo("BBBB3")

    _erro(_post(client, "BBBB3"), status, code)

    gravado = ComputeRequest.objects.get(pk=vencido.pk)
    assert (gravado.status, gravado.reason) == (Status.EXPIRED, "expirado (30 min)")


# --- V-18: o enfileiramento pelo nome -----------------------------------------------------


@pytest.mark.django_db
def test_send_task_pelo_nome_com_o_id_so_depois_do_commit(
    client: Client,
    fila: list[tuple[str, dict[str, Any]]],
    django_capture_on_commit_callbacks: Any,
) -> None:
    _ativo("NOVO3")

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        _post(client, "NOVO3")
        assert fila == []  # nada antes do commit

    assert len(callbacks) == 1
    assert fila == []
    callbacks[0]()
    novo = ComputeRequest.objects.get()
    assert fila == [(TAREFA, {"args": [novo.pk]})]


@pytest.mark.django_db
def test_broker_recusando_grava_o_pedido_failed_com_o_erro(
    client: Client, broker_recusa: None, django_capture_on_commit_callbacks: Any
) -> None:
    _ativo("NOVO3")

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        resposta = _post(client, "NOVO3")

    assert resposta.status_code == 202, resposta.content
    assert len(callbacks) == 1
    gravado = ComputeRequest.objects.get()
    assert gravado.status == Status.FAILED
    assert gravado.reason == REASON_BROKER_REFUSED == "o broker recusou o pedido"
    assert gravado.error == "redis fora do ar"
    assert gravado.finished_at is not None


@pytest.mark.django_db
def test_broker_recusando_pedido_ja_vencido_grava_expired(broker_recusa: None) -> None:
    vencido = _pedido(_ativo("NOVO3"), Status.QUEUED, timezone.now() - FORA)

    enqueue_chain(vencido.pk)

    gravado = ComputeRequest.objects.get(pk=vencido.pk)
    assert (gravado.status, gravado.reason) == (Status.EXPIRED, "expirado (30 min)")


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_broker_recusando_a_resposta_202_traz_o_pedido_failed(
    client: Client, broker_recusa: None
) -> None:
    """So com commit de verdade o `on_commit` roda ao fim do `atomic` da view, antes de ela
    montar o corpo."""
    _ativo("NOVO3")

    resposta = _post(client, "NOVO3")

    assert resposta.status_code == 202, resposta.content
    pedido = resposta.json()["request"]
    novo = ComputeRequest.objects.get()
    assert pedido["id"] == novo.pk
    assert pedido["status"] == "failed"
    assert pedido["reason"] == "o broker recusou o pedido"
    assert pedido["error"] == "redis fora do ar"
    assert pedido["finished_at"] is not None
    assert novo.status == Status.FAILED


# --- V-18: os nomes que a API usa estao no registro do `worker` ---------------------------

_REGISTRO = """
import django

django.setup()

import config

config.celery_app.loader.import_default_modules()
for name in sorted(config.celery_app.tasks):
    print(name)
"""


def _nomes_do_send_task() -> set[str]:
    """Todo nome passado a `send_task` em `apps/api/`, lido do codigo. Um nome que nao seja
    texto literal reprova: nao daria para confere-lo."""
    nomes: set[str] = set()
    for arquivo in sorted(_RAIZ_API.rglob("*.py")):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"), str(arquivo))
        for no in ast.walk(arvore):
            if (
                isinstance(no, ast.Call)
                and isinstance(no.func, ast.Attribute)
                and no.func.attr == "send_task"
            ):
                primeiro = no.args[0] if no.args else None
                assert isinstance(primeiro, ast.Constant), (arquivo, no.lineno)
                assert isinstance(primeiro.value, str), (arquivo, no.lineno)
                nomes.add(primeiro.value)
    return nomes


def test_todo_nome_que_a_api_passa_a_send_task_esta_no_registro_do_worker() -> None:
    nomes = _nomes_do_send_task()
    assert nomes, "nenhum send_task achado em apps/api/: a leitura nao confere nada"

    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings_test"}
    completed = subprocess.run(
        [sys.executable, "-c", _REGISTRO],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    registrados = set(completed.stdout.split())
    assert nomes <= registrados, completed.stdout
