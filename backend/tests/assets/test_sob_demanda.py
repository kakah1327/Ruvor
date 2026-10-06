"""V-19: a cadeia por ticker de um pedido sob demanda (RF-15, RF-20 do M1.6a).

`_calcular_sob_demanda` e chamada direto, como as funcoes com sublinhado de
`tests/risk/test_tasks.py` -- nunca a tarefa registrada. **Os duplos entram no modulo
`apps.assets.tasks`**, o nome global que a cadeia chama: `run_import_prices`,
`run_compute_metrics`, `run_compute_returns` (M5.1), `_missing_models` e `_abrir_execucao`. A coleta e as metricas sao
sempre duplos -- nenhum teste sai para o Yahoo, e a guarda de rede do `conftest` barraria.

- **A ordem das quatro etapas** -- coleta, metricas, retorno (M5.1) e abertura --, com os
  argumentos que cada uma recebe; a falha do retorno so e registrada, e o pedido segue;
- **o pedido vai a `running` e nao fecha** quando a abertura devolve `opened`: quem o fecha e
  o fecho da execucao, no teste de ponta a ponta;
- **cada etapa que falha** fecha o pedido `failed` com o motivo dela e o erro, e as seguintes
  nao rodam; o registry incompleto e falha da abertura;
- **a serie curta** e a execucao fechada `failed` passam pela abertura e pelo fecho reais;
- **o prazo**: o pedido vencido antes de comecar grava `expired` e nenhuma etapa roda; o que
  vence durante a cadeia continua `expired` quando ela termina.

O `_enqueue` de `apps.risk.tasks` e substituido em todo teste: a abertura real so entrega o
`chord` a ele, depois do commit. O prazo e fixado em 30 min pela fixture `prazo`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from celery import chord
from django.utils import timezone
from engine.experiments.runner import ExperimentResult, run_experiment
from pytest_django import DjangoCaptureOnCommitCallbacks, Settings

from apps.accounts.models import Organization, User
from apps.api.models import ComputeRequest
from apps.api.ondemand import (
    REASON_CALCULATED,
    REASON_RUN_FAILED,
    expire_stale,
    expired_reason,
)
from apps.assets.models import Asset, CollectionRun, Price
from apps.assets.tasks import (
    REASON_COLLECT_FAILED,
    REASON_METRICS_FAILED,
    REASON_OPENING_FAILED,
    _calcular_sob_demanda,
)
from apps.assets.yahoo import YahooClient
from apps.risk import config
from apps.risk.compute import MODELS
from apps.risk.models import RiskRun
from apps.risk.tasks import OpeningResult, _compute_asset_model, _fechar_execucao

Status = ComputeRequest.Status

ULTIMO_PREGAO = date(2026, 9, 18)
BARATOS = ("parametric", "historical")


@pytest.fixture(autouse=True)
def prazo(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """O duplo do `_enqueue` da abertura: guarda o que recebeu e nao fala com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.risk.tasks._enqueue", recebidos.append)
    return recebidos


@dataclass
class Etapas:
    """Os duplos das etapas, no modulo `apps.assets.tasks`.

    `chamadas` guarda `(etapa, args, kwargs)` na ordem. `falha[etapa]` e a excecao que a
    etapa levanta; `durante[etapa]` roda antes de a etapa devolver. `abertura` e o que o
    duplo da abertura devolve; com `abertura_real`, a abertura verdadeira roda.
    """

    chamadas: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = field(
        default_factory=list
    )
    falha: dict[str, Exception] = field(default_factory=dict)
    durante: dict[str, Callable[[], None]] = field(default_factory=dict)
    abertura: OpeningResult = field(
        default_factory=lambda: OpeningResult(
            outcome="opened", run_id=None, sessions=None
        )
    )

    def etapa(self, nome: str) -> Callable[..., Any]:
        def duplo(*args: Any, **kwargs: Any) -> Any:
            self.chamadas.append((nome, args, kwargs))
            if nome in self.durante:
                self.durante[nome]()
            if nome in self.falha:
                raise self.falha[nome]
            return self.abertura if nome == "abertura" else None

        return duplo

    def nomes(self) -> list[str]:
        return [nome for nome, _, _ in self.chamadas]


def _etapas(monkeypatch: pytest.MonkeyPatch, *, abertura_real: bool = False) -> Etapas:
    etapas = Etapas()
    monkeypatch.setattr("apps.assets.tasks.run_import_prices", etapas.etapa("coleta"))
    monkeypatch.setattr(
        "apps.assets.tasks.run_compute_metrics", etapas.etapa("metricas")
    )
    monkeypatch.setattr(
        "apps.assets.tasks.run_compute_returns", etapas.etapa("retorno")
    )
    if not abertura_real:
        monkeypatch.setattr(
            "apps.assets.tasks._abrir_execucao", etapas.etapa("abertura")
        )
    return etapas


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


def _pedido(asset: Asset, requested_at: datetime | None = None) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset,
        status=Status.QUEUED,
        requested_at=timezone.now() if requested_at is None else requested_at,
    )


def _gravado(req: ComputeRequest) -> ComputeRequest:
    return ComputeRequest.objects.get(pk=req.pk)


# --- a ordem e o pedido que so fecha no fecho ----------------------------------------------


@pytest.mark.django_db
def test_as_quatro_etapas_rodam_na_ordem_com_os_argumentos_da_cadeia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    etapas = _etapas(monkeypatch)
    req = _pedido(_ativo("AAA3"))
    antes = timezone.now()

    _calcular_sob_demanda(req.pk)

    depois = timezone.now()
    assert etapas.nomes() == ["coleta", "metricas", "retorno", "abertura"]
    (
        (_, coleta, kw_coleta),
        (_, metricas, kw_metricas),
        (_, retorno, kw_retorno),
        (_, abertura, kw_abertura),
    ) = etapas.chamadas
    assert isinstance(coleta[0], YahooClient)
    assert (coleta[1:], kw_coleta) == ((["AAA3"],), {})
    assert (metricas, kw_metricas) == ((["AAA3"],), {})
    assert (retorno, kw_retorno) == ((["AAA3"],), {"requested_by": None})
    ticker, instante, semente, modelos = abertura
    assert (ticker, semente, modelos) == ("AAA3", config.DEFAULT_SEED, list(MODELS))
    assert kw_abertura == {"request_id": req.pk}
    assert antes <= datetime.fromisoformat(instante) <= depois


@pytest.mark.django_db
def test_com_a_abertura_opened_o_pedido_fica_running_e_nao_fecha(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    etapas = _etapas(monkeypatch)
    vistos: list[str] = []
    req = _pedido(_ativo("AAA3"))
    # o pedido ja esta `running` quando a coleta comeca
    etapas.durante["coleta"] = lambda: vistos.append(_gravado(req).status)

    _calcular_sob_demanda(req.pk)

    assert vistos == [Status.RUNNING]
    gravado = _gravado(req)
    assert (gravado.status, gravado.finished_at, gravado.reason, gravado.error) == (
        Status.RUNNING,
        None,
        "",
        "",
    )


# --- o retorno (M5.1, RF-12): o autor do pedido, e a falha que nao fecha o pedido -----------


@pytest.mark.django_db
def test_o_retorno_recebe_o_requested_by_do_pedido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    etapas = _etapas(monkeypatch)
    usuario = User.objects.create_user(
        email="quem@pediu.com",
        name="Quem Pediu",
        organization=Organization.objects.get(slug="ruvor"),
        password="x" * 12,
    )
    req = ComputeRequest.objects.create(
        asset=_ativo("AAA3"),
        status=Status.QUEUED,
        requested_at=timezone.now(),
        requested_by=usuario,
    )

    _calcular_sob_demanda(req.pk)

    (_, args, kwargs) = etapas.chamadas[2]
    assert etapas.nomes()[2] == "retorno"
    assert (args, kwargs) == ((["AAA3"],), {"requested_by": usuario})


@pytest.mark.django_db
def test_a_falha_do_retorno_e_registrada_e_o_pedido_segue_para_a_abertura(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    etapas = _etapas(monkeypatch)
    etapas.falha["retorno"] = RuntimeError("retorno quebrado de proposito")
    req = _pedido(_ativo("AAA3"))

    with caplog.at_level("ERROR", logger="apps.assets.tasks"):
        _calcular_sob_demanda(req.pk)

    assert etapas.nomes() == ["coleta", "metricas", "retorno", "abertura"]
    gravado = _gravado(req)
    # a abertura devolveu `opened`: o pedido segue `running`, sem `failed` nem motivo
    assert (gravado.status, gravado.reason, gravado.error, gravado.finished_at) == (
        Status.RUNNING,
        "",
        "",
        None,
    )
    assert any(
        "o retorno falhou" in r.getMessage() and r.exc_info is not None
        for r in caplog.records
    )


# --- as falhas de cada etapa ---------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("etapa", "motivo", "rodaram"),
    [
        ("coleta", REASON_COLLECT_FAILED, ["coleta"]),
        ("metricas", REASON_METRICS_FAILED, ["coleta", "metricas"]),
        (
            "abertura",
            REASON_OPENING_FAILED,
            ["coleta", "metricas", "retorno", "abertura"],
        ),
    ],
)
def test_a_etapa_que_falha_fecha_o_pedido_failed_com_o_motivo_e_o_erro(
    etapa: str, motivo: str, rodaram: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    etapas = _etapas(monkeypatch)
    etapas.falha[etapa] = RuntimeError(f"{etapa} quebrada de proposito")
    req = _pedido(_ativo("AAA3"))

    _calcular_sob_demanda(req.pk)

    assert etapas.nomes() == rodaram
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.error) == (
        Status.FAILED,
        motivo,
        f"RuntimeError: {etapa} quebrada de proposito",
    )
    assert gravado.finished_at is not None


@pytest.mark.django_db
def test_registry_incompleto_fecha_failed_na_abertura_sem_abrir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    etapas = _etapas(monkeypatch)
    pedidos: list[list[str]] = []

    def faltando(requested: list[str]) -> list[str]:
        pedidos.append(requested)
        return ["lstm"]

    monkeypatch.setattr("apps.assets.tasks._missing_models", faltando)
    req = _pedido(_ativo("AAA3"))

    _calcular_sob_demanda(req.pk)

    assert pedidos == [list(MODELS)]
    assert etapas.nomes() == ["coleta", "metricas", "retorno"]
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason) == (Status.FAILED, REASON_OPENING_FAILED)
    assert gravado.error.startswith("ModelsMissing: ")
    assert "lstm" in gravado.error


# --- a abertura real: serie curta e execucao que fecha failed ------------------------------


@pytest.mark.django_db
def test_serie_curta_fecha_o_pedido_done_com_o_motivo(
    monkeypatch: pytest.MonkeyPatch,
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    _etapas(monkeypatch, abertura_real=True)
    req = _pedido(_serie("AAA3", 10))

    with django_capture_on_commit_callbacks(execute=True):
        _calcular_sob_demanda(req.pk)

    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.error, gravado.risk_run) == (
        Status.DONE,
        f"serie curta (10 pregoes, minimo {config.MIN_SESSIONS})",
        "",
        None,
    )
    assert gravado.finished_at is not None
    assert fila == []
    assert RiskRun.objects.count() == 0


@pytest.mark.django_db
def test_execucao_fechada_failed_fecha_o_pedido_failed(
    monkeypatch: pytest.MonkeyPatch,
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    """Nenhuma tarefa por modelo roda: sem resultado gravado, o `close_run` da `failed`."""
    _etapas(monkeypatch, abertura_real=True)
    req = _pedido(_serie("AAA3"))

    with django_capture_on_commit_callbacks(execute=True):
        _calcular_sob_demanda(req.pk)

    run = RiskRun.objects.get()
    assert len(fila) == 1
    _fechar_execucao([], run.id)

    run.refresh_from_db()
    assert run.status == RiskRun.Status.FAILED
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.risk_run_id) == (
        Status.FAILED,
        REASON_RUN_FAILED,
        run.id,
    )
    assert gravado.error != ""


# --- o prazo -------------------------------------------------------------------------------


@pytest.mark.django_db
def test_pedido_vencido_antes_de_comecar_grava_expired_e_nenhuma_etapa_roda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    etapas = _etapas(monkeypatch)
    req = _pedido(_ativo("AAA3"), timezone.now() - timedelta(minutes=31))

    _calcular_sob_demanda(req.pk)

    assert etapas.nomes() == []
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.error) == (
        Status.EXPIRED,
        expired_reason(),
        "",
    )
    assert gravado.finished_at is not None


@pytest.mark.django_db
def test_pedido_expirado_pelo_post_durante_a_cadeia_continua_expired(
    monkeypatch: pytest.MonkeyPatch,
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    """O `POST` grava `expired` durante a coleta; a cadeia segue, a abertura real acha o
    pedido fechado (`request_closed`), e nada muda nele nem abre execucao."""
    etapas = _etapas(monkeypatch, abertura_real=True)
    req = _pedido(_serie("AAA3"))

    def post_expira() -> None:
        ComputeRequest.objects.filter(pk=req.pk).update(
            requested_at=timezone.now() - timedelta(minutes=31)
        )
        assert expire_stale(timezone.now()) == 1

    etapas.durante["coleta"] = post_expira

    with django_capture_on_commit_callbacks(execute=True):
        _calcular_sob_demanda(req.pk)

    assert etapas.nomes() == ["coleta", "metricas", "retorno"]
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.error, gravado.risk_run) == (
        Status.EXPIRED,
        expired_reason(),
        "",
        None,
    )
    assert RiskRun.objects.count() == 0
    assert fila == []


@pytest.mark.django_db
def test_pedido_vencido_pelo_relogio_durante_a_cadeia_fecha_expired_e_nao_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O relogio da cadeia anda 31 min entre a checagem do comeco e a falha das metricas: o
    pedido, ainda gravado `running`, fecha `expired`, nao `failed`."""
    etapas = _etapas(monkeypatch)
    etapas.falha["metricas"] = RuntimeError("metricas quebradas de proposito")
    inicio = timezone.now()
    instantes = iter([inicio, inicio + timedelta(minutes=31)])
    monkeypatch.setattr(
        "apps.assets.tasks.timezone", SimpleNamespace(now=lambda: next(instantes))
    )
    req = _pedido(_ativo("AAA3"), inicio)

    _calcular_sob_demanda(req.pk)

    assert etapas.nomes() == ["coleta", "metricas"]
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.error) == (
        Status.EXPIRED,
        expired_reason(),
        "",
    )


# --- ponta a ponta: a abertura, as tarefas e o fecho reais ---------------------------------


@pytest.mark.django_db
def test_ponta_a_ponta_o_pedido_termina_done_calculado_quando_o_fecho_roda(
    monkeypatch: pytest.MonkeyPatch,
    fila: list[Any],
    django_capture_on_commit_callbacks: DjangoCaptureOnCommitCallbacks,
) -> None:
    """Coleta e metricas por duplo; abertura real, com o `_enqueue` espiado; as tarefas por
    modelo chamadas a mao, com o motor verdadeiro so para os baratos -- os outros levantam
    no `run_experiment` e gravam o par de erro --; e o fecho chamado a mao."""
    etapas = _etapas(monkeypatch, abertura_real=True)

    def motor(experiment: Any, provider: Any) -> ExperimentResult:
        if experiment.model_names[0] not in BARATOS:
            raise ValueError("modelo caro fora do teste")
        return run_experiment(experiment, provider)

    monkeypatch.setattr("apps.risk.compute.run_experiment", motor)
    req = _pedido(_serie("AAA3"))

    with django_capture_on_commit_callbacks(execute=True):
        _calcular_sob_demanda(req.pk)

    assert etapas.nomes() == ["coleta", "metricas", "retorno"]
    run = RiskRun.objects.get()
    gravado = _gravado(req)
    assert (gravado.status, gravado.risk_run_id, gravado.finished_at) == (
        Status.RUNNING,
        run.id,
        None,
    )
    assert len(fila) == 1
    grupo = fila[0]
    assert isinstance(grupo, chord)

    for assinatura in grupo.tasks:
        _compute_asset_model(*assinatura.args)
    # as tarefas gravaram, mas o pedido so fecha no fecho
    assert _gravado(req).status == Status.RUNNING

    _fechar_execucao([None] * len(grupo.tasks), run.id)

    run.refresh_from_db()
    assert run.status == RiskRun.Status.PARTIAL
    assert run.results.exclude(error="").count() == 2 * (len(MODELS) - len(BARATOS))
    gravado = _gravado(req)
    assert (gravado.status, gravado.reason, gravado.error) == (
        Status.DONE,
        REASON_CALCULATED,
        "",
    )
    assert gravado.finished_at is not None
