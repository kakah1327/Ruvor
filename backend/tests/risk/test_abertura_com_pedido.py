"""V-19b: a abertura com pedido e o fecho que fecha o pedido ligado (RF-15, RF-20, RF-24).

As funcoes com sublinhado de `apps/risk/tasks.py` sao chamadas direto, como em
`tests/risk/test_tasks.py`, e o `_enqueue` e substituido em todo teste por um duplo que guarda
o que recebeu -- o nome global que o `on_commit` da abertura resolve na hora do commit.

- **A ligacao antes do `chord`**: o espiao do `_enqueue` le o pedido **do banco** quando e
  chamado, e o pedido ja aponta para a execucao.
- **O `chord` so sai depois do commit**: sem `execute=True`, o `_enqueue` nao e chamado, e o
  callback fica capturado.
- **A ligacao dentro da transacao da abertura**: num teste `django_db` comum o proprio teste
  esta num `atomic`, e o `on_commit` so roda quando a captura termina -- depois de a abertura
  devolver. Uma ligacao gravada depois do `atomic` da abertura ainda estaria la, e o espiao
  nao a distinguiria. Por isso esse caso e `transaction=True` (com `TRANSACIONAL` e
  `banco_limpo`, como todo teste assim): o commit e de verdade, e o `on_commit` roda na saida
  do `atomic` da abertura.
- **A serie curta** devolve `sessions` e fecha o pedido `done` com o motivo -- ou `expired`,
  se venceu; **o pedido ja fechado** sai `request_closed` sem criar execucao.
- **O fecho** fecha o pedido ligado pelo `status` da execucao; dois pedidos abertos ligados a
  mesma execucao fecham juntos; o pedido vencido e ainda gravado `running` fecha `expired`.

O prazo e fixado em 30 min pela fixture `prazo`, para que um `.env` com outro valor nao mude
o que se confere.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import pytest
from django.utils import timezone
from pytest_django import DjangoCaptureOnCommitCallbacks, Settings

from apps.api.models import ComputeRequest
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.models import RiskRun
from apps.risk.tasks import _abrir_execucao, _compute_asset_model, _fechar_execucao
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)

Status = ComputeRequest.Status

BARATOS = ["parametric", "historical"]
ULTIMO_PREGAO = date(2026, 9, 18)


@pytest.fixture(autouse=True)
def prazo(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """O duplo do `_enqueue`: guarda o que recebeu e nao fala com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.risk.tasks._enqueue", recebidos.append)
    return recebidos


def _ativo(ticker: str) -> Asset:
    agora = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )


def _serie(ticker: str, quantidade: int = config.MIN_SESSIONS) -> Asset:
    """`quantidade` pregoes em dias uteis terminando em `ULTIMO_PREGAO`."""
    asset = _ativo(ticker)
    coleta = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    datas: list[date] = []
    dia = ULTIMO_PREGAO
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    nivel = 100.0
    retornos = np.random.default_rng(7).normal(0, 0.01, quantidade)
    linhas = []
    for dia, retorno in zip(sorted(datas), retornos, strict=True):
        nivel *= math.exp(float(retorno))
        valor = Decimal(str(nivel)).quantize(Decimal("0.000001"))
        linhas.append(
            Price(
                asset=asset,
                date=dia,
                open=valor,
                high=valor,
                low=valor,
                close=valor,
                adj_close=valor,
                volume=1000,
                log_return=None,
                run=coleta,
                updated_at=timezone.now(),
            )
        )
    Price.objects.bulk_create(linhas)
    return asset


def _pedido(
    asset: Asset,
    status: str = Status.RUNNING,
    requested_at: datetime | None = None,
    risk_run: RiskRun | None = None,
) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset,
        status=status,
        requested_at=timezone.now() if requested_at is None else requested_at,
        risk_run=risk_run,
    )


def _instante(segundos: int = 10) -> str:
    """Um `calculated_at` dentro do prazo, em ISO, como a cadeia o passa."""
    return (timezone.now() - timedelta(seconds=segundos)).isoformat()


def _gravado(req: ComputeRequest) -> ComputeRequest:
    return ComputeRequest.objects.get(pk=req.pk)


# --- a ligacao antes do `chord`, e o `chord` depois do commit ------------------------------


@pytest.mark.django_db
def test_a_abertura_com_pedido_liga_a_execucao_antes_de_o_chord_sair(
    monkeypatch: pytest.MonkeyPatch,
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    req = _pedido(_serie("AAA3"))
    vistos: list[int | None] = []

    def espiao(signature: Any) -> None:
        vistos.append(ComputeRequest.objects.get(pk=req.pk).risk_run_id)

    monkeypatch.setattr("apps.risk.tasks._enqueue", espiao)

    with django_capture_on_commit_callbacks(execute=True):
        saida = _abrir_execucao("AAA3", _instante(), 42, BARATOS, request_id=req.pk)

    run = RiskRun.objects.get()
    assert saida == {"outcome": "opened", "run_id": run.pk, "sessions": None}
    assert vistos == [run.pk]
    assert run.status == RiskRun.Status.RUNNING
    # o pedido nao fecha na abertura: fecha com a execucao, no fecho
    gravado = _gravado(req)
    assert (gravado.status, gravado.finished_at) == (Status.RUNNING, None)


@pytest.mark.django_db
@pytest.mark.parametrize("com_pedido", [True, False], ids=["com_pedido", "sem_pedido"])
def test_o_chord_so_e_enfileirado_depois_do_commit(
    com_pedido: bool,
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    asset = _serie("AAA3")
    request_id = _pedido(asset).pk if com_pedido else None

    with django_capture_on_commit_callbacks() as callbacks:
        if request_id is None:
            _abrir_execucao("AAA3", _instante(), 42, BARATOS)
        else:
            _abrir_execucao("AAA3", _instante(), 42, BARATOS, request_id=request_id)

    assert fila == []
    assert len(callbacks) == 1
    callbacks[0]()
    assert len(fila) == 1
    assert fila[0].body.args == (RiskRun.objects.get().pk,)


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_a_ligacao_ja_esta_confirmada_quando_o_commit_da_abertura_solta_o_chord(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Commit de verdade: o `on_commit` roda na saida do `atomic` da abertura, e o espiao ve
    o pedido ligado -- a ligacao entrou na mesma transacao que a execucao."""
    req = _pedido(_serie("AAA3"))
    vistos: list[int | None] = []

    def espiao(signature: Any) -> None:
        vistos.append(ComputeRequest.objects.get(pk=req.pk).risk_run_id)

    monkeypatch.setattr("apps.risk.tasks._enqueue", espiao)

    saida = _abrir_execucao("AAA3", _instante(), 42, BARATOS, request_id=req.pk)

    run = RiskRun.objects.get()
    assert saida == {"outcome": "opened", "run_id": run.pk, "sessions": None}
    assert vistos == [run.pk]


# --- a serie curta e o pedido ja fechado ---------------------------------------------------


@pytest.mark.django_db
def test_serie_curta_com_pedido_devolve_sessions_e_fecha_done_com_o_motivo(
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    req = _pedido(_serie("AAA3", 100))

    with django_capture_on_commit_callbacks(execute=True):
        saida = _abrir_execucao("AAA3", _instante(), 42, BARATOS, request_id=req.pk)

    assert saida == {"outcome": "short_series", "run_id": None, "sessions": 100}
    gravado = _gravado(req)
    assert gravado.status == Status.DONE
    assert gravado.reason == "serie curta (100 pregoes, minimo 503)"
    assert gravado.error == ""
    assert gravado.finished_at is not None
    assert gravado.risk_run_id is None
    assert RiskRun.objects.count() == 0
    assert fila == []


@pytest.mark.django_db
def test_serie_curta_com_pedido_vencido_fecha_expired(
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    req = _pedido(
        _serie("AAA3", 100), requested_at=timezone.now() - timedelta(minutes=31)
    )

    with django_capture_on_commit_callbacks(execute=True):
        saida = _abrir_execucao("AAA3", _instante(), 42, BARATOS, request_id=req.pk)

    assert saida == {"outcome": "short_series", "run_id": None, "sessions": 100}
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason) == (Status.EXPIRED, "expirado (30 min)")
    assert gravado.finished_at is not None


@pytest.mark.django_db
@pytest.mark.parametrize("status", [Status.DONE, Status.FAILED, Status.EXPIRED])
def test_pedido_ja_fechado_sai_request_closed_sem_criar_execucao(
    status: str,
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    req = _pedido(_serie("AAA3"), status=status)

    with django_capture_on_commit_callbacks(execute=True):
        saida = _abrir_execucao("AAA3", _instante(), 42, BARATOS, request_id=req.pk)

    assert saida == {"outcome": "request_closed", "run_id": None, "sessions": None}
    assert RiskRun.objects.count() == 0
    assert fila == []
    gravado = _gravado(req)
    assert (gravado.status, gravado.risk_run_id) == (status, None)


# --- o fecho fecha o pedido ligado ---------------------------------------------------------


def _abre_com_pedido(
    req: ComputeRequest,
    captura: DjangoCaptureOnCommitCallbacks,
    modelos: list[str],
    fila: list[Any],
) -> RiskRun:
    with captura(execute=True):
        saida = _abrir_execucao(
            req.asset.ticker, _instante(), 42, modelos, request_id=req.pk
        )
    assert saida["outcome"] == "opened"
    assert saida["run_id"] is not None
    assert len(fila) == 1
    return RiskRun.objects.get(pk=saida["run_id"])


@pytest.mark.django_db
def test_o_fecho_fecha_o_pedido_ligado_done_calculado(
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    req = _pedido(_serie("AAA3"))
    run = _abre_com_pedido(req, django_capture_on_commit_callbacks, BARATOS, fila)
    (grupo,) = fila
    for tarefa in grupo.tasks:
        _compute_asset_model(*tarefa.args)

    _fechar_execucao([None] * len(grupo.tasks), *grupo.body.args)

    run.refresh_from_db()
    assert run.status == RiskRun.Status.OK
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.error) == (
        Status.DONE,
        "calculado",
        "",
    )
    assert gravado.finished_at == run.finished_at


@pytest.mark.django_db
def test_o_fecho_de_execucao_failed_fecha_o_pedido_failed(
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    req = _pedido(_serie("AAA3"))
    run = _abre_com_pedido(req, django_capture_on_commit_callbacks, BARATOS, fila)

    _fechar_execucao([], run.pk)  # nenhuma tarefa rodou: a execucao fecha `failed`

    run.refresh_from_db()
    assert run.status == RiskRun.Status.FAILED
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason) == (Status.FAILED, "a execucao falhou")
    assert gravado.error != ""


@pytest.mark.django_db
def test_dois_pedidos_ligados_a_mesma_execucao_fecham_juntos(
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    """O caminho real: o primeiro pedido abriu a execucao e expirou (o `POST` o gravou
    `expired`); o seguinte, do mesmo ativo, pulou e se ligou a ela. E, para que o fecho mostre
    que fecha **todo** aberto ligado, um segundo aberto ligado a ela noutro ativo -- o indice
    parcial nao deixa dois abertos do mesmo ativo."""
    asset = _serie("AAA3")
    primeiro = _pedido(asset)
    run = _abre_com_pedido(primeiro, django_capture_on_commit_callbacks, BARATOS, fila)
    ComputeRequest.objects.filter(pk=primeiro.pk).update(
        status=Status.EXPIRED, reason="expirado (30 min)", finished_at=timezone.now()
    )
    expirado_em = _gravado(primeiro).finished_at
    seguinte = _pedido(asset)
    with django_capture_on_commit_callbacks(execute=True):
        saida = _abrir_execucao(
            "AAA3", _instante(5), 42, BARATOS, request_id=seguinte.pk
        )
    assert saida == {"outcome": "already_running", "run_id": run.pk, "sessions": None}
    outro = _pedido(_ativo("BBB3"), risk_run=run)

    _fechar_execucao([], run.pk)

    for req in (seguinte, outro):
        gravado = _gravado(req)
        assert (gravado.status, gravado.risk_run_id) == (Status.FAILED, run.pk)
        assert gravado.reason == "a execucao falhou"
    gravado = _gravado(primeiro)
    assert (gravado.status, gravado.finished_at) == (Status.EXPIRED, expirado_em)


@pytest.mark.django_db
def test_pedido_vencido_e_ainda_running_liga_e_o_fecho_o_grava_expired(
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    """A abertura olha o estado gravado, nao o relogio: o pedido vencido e ainda `running`
    passa e se liga; quem o grava `expired` -- e nao `done` nem `failed` -- e o fecho."""
    req = _pedido(_serie("AAA3"), requested_at=timezone.now() - timedelta(minutes=31))
    run = _abre_com_pedido(req, django_capture_on_commit_callbacks, BARATOS, fila)
    (grupo,) = fila
    for tarefa in grupo.tasks:
        _compute_asset_model(*tarefa.args)

    _fechar_execucao([None] * len(grupo.tasks), run.pk)

    run.refresh_from_db()
    assert run.status == RiskRun.Status.OK
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason) == (Status.EXPIRED, "expirado (30 min)")
    assert gravado.risk_run_id == run.pk
