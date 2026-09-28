"""O dominio do pedido sob demanda: o prazo, os fechos, o indice parcial e a guarda das travas.

- **O prazo (RF-18)**: `effective_status` devolve `expired` para o aberto vencido **sem
  gravar** -- e o do `GET`; `expire_stale` grava.
- **Os fechos (RF-15)**: `close_request` sobre pedido vencido grava `expired`, nao o desfecho
  pedido; `close_linked` fecha **todos** os abertos ligados a execucao, `done` ou `failed`
  pelo `status` dela, e `expired` o vencido.
- **O indice unico parcial (RF-16)**: o segundo pedido aberto do mesmo ativo, inserido direto
  no banco, levanta `IntegrityError` -- metade do V-14 --, e o pedido fechado nao conta.
- **A guarda das travas**: `lock_asset` e `lock_on_demand` fora de `transaction.atomic`
  levantam `RuntimeError`. O teste e `transaction=True`, porque num teste `django_db` comum o
  proprio teste ja esta num `atomic` e a guarda nao dispararia; e casa a mensagem, porque o
  bloqueio do pytest-django tambem levanta `RuntimeError`. Como todo `transaction=True` do
  repositorio, usa `TRANSACIONAL` e `banco_limpo` de `tests/api/migracao.py`: o `flush` do
  Django nao enxerga as tabelas com esquema.
- **A guarda da limpeza**: o ultimo teste do modulo, sem marca de banco -- o pytest-django o
  roda depois dos `transaction=True` --, confere que nenhuma tabela de dominio ficou com
  linha. O teste das travas grava um ativo e um pedido de proposito, para que uma
  `banco_limpo` sem o `TRUNCATE` seja observavel.

O prazo e fixado em 30 min pela fixture `prazo`, para que um `.env` com outro valor nao
mude o que se confere.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from django.db import IntegrityError, connection, transaction
from django.utils import timezone
from pytest_django import Settings
from pytest_django.plugin import DjangoDbBlocker

from apps.api.models import ComputeRequest
from apps.api.ondemand import (
    close_linked,
    close_request,
    effective_status,
    expire_stale,
    lock_asset,
    lock_on_demand,
)
from apps.assets.models import Asset, CollectionRun
from apps.risk.models import RiskRun
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)

AGORA = timezone.now()
VENCIDO = AGORA - timedelta(minutes=31)
RECENTE = AGORA - timedelta(minutes=1)

Status = ComputeRequest.Status


@pytest.fixture(autouse=True)
def prazo(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)


def _ativo(ticker: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


def _pedido(
    asset: Asset,
    status: str,
    requested_at: datetime,
    risk_run: RiskRun | None = None,
) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset, status=status, requested_at=requested_at, risk_run=risk_run
    )


def _execucao(asset: Asset, status: str) -> RiskRun:
    coleta = CollectionRun.objects.create(source="teste", started_at=AGORA)
    return RiskRun.objects.create(
        asset=asset,
        calculated_at=AGORA - timedelta(seconds=10),
        finished_at=AGORA,
        engine_version="0.3.0",
        seed=42,
        train_window_days=252,
        as_of_date=date(2026, 9, 25),
        first_price_date=date(2024, 9, 25),
        price_count=503,
        train_count=252,
        test_count=250,
        price_run=coleta,
        requested_by=None,
        status=status,
        requested_models=["historical"],
        full_recompute=False,
    )


def _gravado(req: ComputeRequest) -> ComputeRequest:
    return ComputeRequest.objects.get(pk=req.pk)


# --- o prazo (RF-18) ----------------------------------------------------------------------


@pytest.mark.django_db
def test_effective_status_do_aberto_vencido_e_expired_sem_gravar() -> None:
    queued = _pedido(_ativo("AAA3"), Status.QUEUED, VENCIDO)
    running = _pedido(_ativo("BBB3"), Status.RUNNING, VENCIDO)
    recente = _pedido(_ativo("CCC3"), Status.RUNNING, RECENTE)

    assert effective_status(queued, AGORA) == "expired"
    assert effective_status(running, AGORA) == "expired"
    assert effective_status(recente, AGORA) == "running"
    assert _gravado(queued).status == Status.QUEUED
    assert _gravado(running).status == Status.RUNNING
    assert _gravado(queued).finished_at is None


@pytest.mark.django_db
def test_effective_status_do_fechado_e_o_gravado() -> None:
    feito = _pedido(_ativo("AAA3"), Status.DONE, VENCIDO)
    falho = _pedido(_ativo("BBB3"), Status.FAILED, VENCIDO)

    assert effective_status(feito, AGORA) == "done"
    assert effective_status(falho, AGORA) == "failed"


@pytest.mark.django_db
def test_expire_stale_grava_expired_so_nos_abertos_vencidos() -> None:
    queued = _pedido(_ativo("AAA3"), Status.QUEUED, VENCIDO)
    running = _pedido(_ativo("BBB3"), Status.RUNNING, VENCIDO)
    recente = _pedido(_ativo("CCC3"), Status.QUEUED, RECENTE)
    feito = _pedido(_ativo("DDD3"), Status.DONE, VENCIDO)

    assert expire_stale(AGORA) == 2

    for req in (queued, running):
        gravado = _gravado(req)
        assert gravado.status == Status.EXPIRED
        assert gravado.reason == "expirado (30 min)"
        assert gravado.finished_at == AGORA
    assert _gravado(recente).status == Status.QUEUED
    assert _gravado(feito).status == Status.DONE


# --- os fechos (RF-15) --------------------------------------------------------------------


@pytest.mark.django_db
def test_close_request_sobre_pedido_vencido_grava_expired_e_nao_o_desfecho() -> None:
    req = _pedido(_ativo("AAA3"), Status.RUNNING, VENCIDO)

    close_request(req, Status.FAILED, "falhou na coleta", "timeout do Yahoo", AGORA)

    gravado = _gravado(req)
    assert gravado.status == Status.EXPIRED
    assert gravado.reason == "expirado (30 min)"
    assert gravado.error == ""
    assert gravado.finished_at == AGORA


@pytest.mark.django_db
def test_close_request_dentro_do_prazo_grava_o_desfecho() -> None:
    req = _pedido(_ativo("AAA3"), Status.RUNNING, RECENTE)

    close_request(req, Status.FAILED, "falhou na coleta", "timeout do Yahoo", AGORA)

    gravado = _gravado(req)
    assert gravado.status == Status.FAILED
    assert gravado.reason == "falhou na coleta"
    assert gravado.error == "timeout do Yahoo"
    assert gravado.finished_at == AGORA


@pytest.mark.django_db
def test_close_request_nao_reabre_nem_muda_pedido_ja_fechado() -> None:
    req = _pedido(_ativo("AAA3"), Status.RUNNING, RECENTE)
    ComputeRequest.objects.filter(pk=req.pk).update(
        status=Status.EXPIRED, reason="expirado (30 min)", finished_at=RECENTE
    )

    close_request(req, Status.DONE, "calculado", "", AGORA)

    gravado = _gravado(req)
    assert gravado.status == Status.EXPIRED
    assert gravado.finished_at == RECENTE


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("run_status", "status", "reason"),
    [
        (RiskRun.Status.OK, Status.DONE, "calculado"),
        (RiskRun.Status.PARTIAL, Status.DONE, "calculado"),
        (RiskRun.Status.FAILED, Status.FAILED, "a execucao falhou"),
    ],
)
def test_close_linked_fecha_todos_os_abertos_ligados_pelo_status_da_execucao(
    run_status: str, status: str, reason: str
) -> None:
    asset = _ativo("AAA3")
    run = _execucao(asset, run_status)
    outro = _execucao(_ativo("BBB3"), run_status)
    # os abertos ligados ficam em ativos distintos: o indice parcial nao deixa dois abertos
    # do mesmo ativo
    queued = _pedido(asset, Status.QUEUED, RECENTE, run)
    running = _pedido(_ativo("CCC3"), Status.RUNNING, RECENTE, run)
    vencido = _pedido(_ativo("DDD3"), Status.RUNNING, VENCIDO, run)
    fechado = _pedido(asset, Status.DONE, VENCIDO, run)
    sem_ligacao = _pedido(_ativo("EEE3"), Status.RUNNING, RECENTE, outro)

    assert close_linked(run, AGORA) == 3

    for req in (queued, running):
        gravado = _gravado(req)
        assert gravado.status == status
        assert gravado.reason == reason
        assert gravado.finished_at == AGORA
        assert (gravado.error != "") == (status == Status.FAILED)
    gravado = _gravado(vencido)
    assert gravado.status == Status.EXPIRED
    assert gravado.reason == "expirado (30 min)"
    assert _gravado(fechado).status == Status.DONE
    assert _gravado(fechado).finished_at is None
    assert _gravado(sem_ligacao).status == Status.RUNNING


@pytest.mark.django_db
def test_close_linked_sem_pedido_ligado_nao_faz_nada() -> None:
    run = _execucao(_ativo("AAA3"), RiskRun.Status.OK)

    assert close_linked(run, AGORA) == 0


# --- o indice unico parcial (RF-16) -------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("primeiro", "segundo"),
    [
        (Status.QUEUED, Status.QUEUED),
        (Status.QUEUED, Status.RUNNING),
        (Status.RUNNING, Status.QUEUED),
    ],
)
def test_o_segundo_pedido_aberto_do_mesmo_ativo_levanta_integrity_error(
    primeiro: str, segundo: str
) -> None:
    asset = _ativo("AAA3")
    _pedido(asset, primeiro, RECENTE)

    with pytest.raises(IntegrityError), transaction.atomic():
        _pedido(asset, segundo, AGORA)


@pytest.mark.django_db
def test_pedido_fechado_nao_conta_para_o_indice() -> None:
    asset = _ativo("AAA3")
    for status in (Status.DONE, Status.FAILED, Status.EXPIRED):
        _pedido(asset, status, VENCIDO)

    aberto = _pedido(asset, Status.QUEUED, AGORA)

    assert ComputeRequest.objects.filter(asset=asset).count() == 4
    assert _gravado(aberto).status == Status.QUEUED


# --- a guarda das travas ------------------------------------------------------------------


@pytest.mark.django_db
def test_as_travas_dentro_de_transacao_sao_tomadas() -> None:
    with transaction.atomic():
        lock_on_demand()
        lock_asset(1)


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_as_travas_fora_de_transacao_levantam_runtime_error() -> None:
    # grava de proposito: e o que a guarda da limpeza, abaixo, observa
    asset = _ativo("AAA3")
    _pedido(asset, Status.QUEUED, AGORA)

    with pytest.raises(RuntimeError, match="fora de transacao"):
        lock_on_demand()
    with pytest.raises(RuntimeError, match="fora de transacao"):
        lock_asset(asset.pk)


# --- a guarda da limpeza ------------------------------------------------------------------

TABELAS_DE_DOMINIO = ("silver.price", "gold.risk_run", "core.compute_request")


def test_nenhuma_tabela_de_dominio_ficou_com_linha_depois_dos_transacionais(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    """Sem marca de banco: roda depois dos `transaction=True`, no banco de teste que os
    testes de banco do modulo criaram. Sozinho (`-k`), a conexao seria a do banco
    configurado, que tem dado de verdade -- e pula, com o motivo."""
    with django_db_blocker.unblock():
        if not connection.settings_dict["NAME"].startswith("test_"):
            pytest.skip("so vale junto com os testes de banco do modulo")
        with connection.cursor() as cursor:
            linhas = {}
            for tabela in TABELAS_DE_DOMINIO:
                cursor.execute(f"SELECT count(*) FROM {tabela}")
                linhas[tabela] = cursor.fetchone()[0]

    assert linhas == dict.fromkeys(TABELAS_DE_DOMINIO, 0)
