"""V-19c: nunca duas execucoes assincronas no mesmo ativo (RF-24), e a abertura x o fecho.

Todo teste aqui e `transaction=True` -- com `TRANSACIONAL` e `banco_limpo` de
`tests/api/migracao.py`, como todo teste assim --, porque as corridas precisam de commit de
verdade entre conexoes, e cada thread abre a sua (o Django da uma por thread).

**O pulo, sem corrida**: com uma `running` recente no ativo, a abertura pula -- sem pedido
devolve `None`; com pedido, liga o pedido a ela e devolve `already_running`. Com a `running`
mais velha que o prazo, abre.

**As corridas**, pelos pontos de desvio `_after_read_running` e `_after_close_lock` de
`apps/risk/tasks.py`, substituidos por funcoes que esperam. Quem parte primeiro e o evento que
libera o outro sao os da tabela das esperas do plano:

- **duas aberturas**: `Barrier(2)` entre a leitura da `running` e a criacao. Com a trava, a
  segunda espera a trava, a barreira estoura (2 s) na primeira, e a segunda ve a `running` da
  primeira; sem a trava, as duas passam juntas e abrem as duas;
- **fecho sem trava**: parte a abertura com pedido, sobre uma `running`; ela para depois de
  ler; o fecho so parte depois. Com a trava, o fecho espera a abertura ligar e confirmar, e
  fecha o pedido; sem ela, fecha a execucao sem ver a ligacao, e o pedido fica aberto sobre
  execucao fechada;
- **fecho sem transacao**: parte o fecho; ele para depois de tomar a trava; a abertura so
  parte depois. Com a transacao, a abertura nao le enquanto o fecho segura a trava, e abre
  outra execucao; sem ela, a trava `xact` se soltou no fim da propria consulta, a abertura le
  a `running`, o fecho a fecha, e a abertura liga o pedido a execucao fechada.

**As pre-condicoes**, sem as quais a mutacao sobrevive em silencio: o registry e carregado
**antes** das threads (a primeira importacao do TensorFlow num processo frio passaria da
espera de 2 s); as esperas de partida sao `assert`; as do lado que a mutacao precisa sao de
5 s, as que so existem para estourar no caso correto, de 2 s; o ativo tem 503 pregoes (senao
as duas aberturas saem por serie curta); os `calculated_at` sao `timezone.now()` menos
segundos -- dentro do prazo -- e distintos entre si. A `BrokenBarrierError` e engolida no ponto
de desvio: nao pode virar erro da abertura nem do fecho.

**O invariante**, conferido no fim de cada teste: nenhum pedido aberto aponta para
`risk_run` fechada, e ha no maximo um pedido aberto por ativo.

Cada thread chama `connections.close_all()` no `finally`; o teste faz `join(timeout=30)` e
reprova se alguma ficou viva -- antes da desmontagem, cujo `TRUNCATE` travaria na trava de
uma thread viva em vez de reprovar.

**A guarda dos dados de migration** e o ultimo teste do modulo: depois dos anteriores, a
organizacao `ruvor` e o `IBOV` estao de volta -- tirar a recriacao da `banco_limpo` o reprova
rodando este arquivo sozinho.
"""

from __future__ import annotations

import math
import threading
from collections.abc import Callable
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import numpy as np
import pytest
from django.db import connections
from django.db.models import Count
from django.utils import timezone
from engine.backtesting import load_all_backtest_modules
from engine.models import load_all_model_modules
from pytest_django import Settings

from apps.accounts.models import Organization
from apps.api.models import ComputeRequest
from apps.api.ondemand import OPEN_STATUSES
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.models import RiskRun
from apps.risk.tasks import _abrir_execucao, _fechar_execucao
from tests.api.migracao import (  # noqa: F401 -- fixture, achada pelo pytest no modulo
    TRANSACIONAL,
    banco_limpo,
)

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]

Status = ComputeRequest.Status

BARATOS = ["parametric", "historical"]
ULTIMO_PREGAO = date(2026, 9, 18)
ESPERA_DO_LADO_DA_MUTACAO = 5
ESPERA_QUE_ESTOURA = 2
JOIN = 30


@pytest.fixture(autouse=True)
def prazo(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=30)


@pytest.fixture(autouse=True)
def registry() -> None:
    """Carregado antes de qualquer thread: a abertura o carrega antes do `atomic`, e a
    primeira importacao do TensorFlow num processo frio passaria das esperas."""
    load_all_model_modules()
    load_all_backtest_modules()


@pytest.fixture(autouse=True)
def fila(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """O duplo do `_enqueue`, que o `on_commit` da abertura chama: nao fala com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.risk.tasks._enqueue", recebidos.append)
    return recebidos


# --- os dados ------------------------------------------------------------------------------


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
    """`quantidade` pregoes em dias uteis terminando em `ULTIMO_PREGAO` -- 503 por padrao,
    o piso: com menos, as aberturas sairiam por serie curta e as corridas nao morderiam."""
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


def _running(asset: Asset, calculated_at: datetime) -> RiskRun:
    """Uma execucao `running` semeada direto no banco, sem resultado nenhum."""
    coleta = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    return RiskRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=None,
        engine_version="0.3.0",
        seed=42,
        train_window_days=252,
        as_of_date=ULTIMO_PREGAO,
        first_price_date=date(2024, 9, 18),
        price_count=503,
        train_count=252,
        test_count=250,
        price_run=coleta,
        requested_by=None,
        status=RiskRun.Status.RUNNING,
        requested_models=list(BARATOS),
        full_recompute=False,
    )


def _pedido(asset: Asset) -> ComputeRequest:
    return ComputeRequest.objects.create(
        asset=asset, status=Status.RUNNING, requested_at=timezone.now()
    )


def _antes(segundos: int) -> datetime:
    """Um instante dentro do prazo: `timezone.now()` menos segundos."""
    return timezone.now() - timedelta(seconds=segundos)


# --- as threads ----------------------------------------------------------------------------


def _parte(
    nome: str, alvo: Callable[[], object], saida: list[tuple[str, object]]
) -> threading.Thread:
    """Roda `alvo` numa thread; o resultado -- ou a excecao -- volta por `saida`."""

    def corre() -> None:
        try:
            saida.append((nome, alvo()))
        except BaseException as exc:  # a excecao volta ao teste, que a reprova
            saida.append((nome, exc))
        finally:
            connections.close_all()

    thread = threading.Thread(target=corre, name=nome, daemon=True)
    thread.start()
    return thread


def _junta(*threads: threading.Thread) -> None:
    for thread in threads:
        thread.join(timeout=JOIN)
    vivas = [t.name for t in threads if t.is_alive()]
    assert vivas == [], f"threads vivas depois de {JOIN} s: {vivas}"


def _resultados(saida: list[tuple[str, object]]) -> dict[str, object]:
    erros = [(nome, r) for nome, r in saida if isinstance(r, BaseException)]
    assert erros == []
    return dict(saida)


def _invariante() -> None:
    """Nenhum pedido aberto aponta para `risk_run` fechada; no maximo um aberto por ativo."""
    abertos = ComputeRequest.objects.filter(status__in=OPEN_STATUSES)
    sobre_fechada = list(
        abertos.filter(risk_run__isnull=False)
        .exclude(risk_run__status=RiskRun.Status.RUNNING)
        .values_list("pk", "risk_run_id", "risk_run__status")
    )
    assert sobre_fechada == []
    por_ativo = list(abertos.values("asset_id").annotate(n=Count("pk")).filter(n__gt=1))
    assert por_ativo == []


# --- o pulo, sem corrida -------------------------------------------------------------------


def test_com_running_recente_a_abertura_sem_pedido_pula_e_devolve_none(
    fila: list[Any],
) -> None:
    asset = _serie("AAA3")
    running = _running(asset, _antes(60))

    assert _abrir_execucao("AAA3", _antes(5).isoformat(), 42, BARATOS) is None

    assert list(RiskRun.objects.values_list("pk", flat=True)) == [running.pk]
    assert fila == []
    _invariante()


def test_com_running_recente_a_abertura_com_pedido_liga_e_devolve_already_running(
    fila: list[Any],
) -> None:
    asset = _serie("AAA3")
    running = _running(asset, _antes(60))
    req = _pedido(asset)

    saida = _abrir_execucao(
        "AAA3", _antes(5).isoformat(), 42, BARATOS, request_id=req.pk
    )

    assert saida == {
        "outcome": "already_running",
        "run_id": running.pk,
        "sessions": None,
    }
    gravado = ComputeRequest.objects.get(pk=req.pk)
    assert (gravado.status, gravado.risk_run_id) == (Status.RUNNING, running.pk)
    assert RiskRun.objects.count() == 1
    assert fila == []
    _invariante()


def test_com_running_mais_velha_que_o_prazo_a_abertura_abre(fila: list[Any]) -> None:
    asset = _serie("AAA3")
    presa = _running(asset, timezone.now() - timedelta(minutes=31))

    run_id = _abrir_execucao("AAA3", _antes(5).isoformat(), 42, BARATOS)

    assert run_id is not None
    assert run_id != presa.pk
    assert RiskRun.objects.get(pk=run_id).status == RiskRun.Status.RUNNING
    assert len(fila) == 1
    _invariante()


# --- as corridas ---------------------------------------------------------------------------


def test_duas_aberturas_concorrentes_do_mesmo_ativo_abrem_uma_so(
    monkeypatch: pytest.MonkeyPatch, fila: list[Any]
) -> None:
    _serie("AAA3")
    barreira = threading.Barrier(2)

    def espera_a_outra() -> None:
        try:
            barreira.wait(timeout=ESPERA_QUE_ESTOURA)
        except threading.BrokenBarrierError:
            pass

    monkeypatch.setattr("apps.risk.tasks._after_read_running", espera_a_outra)
    instantes = [_antes(10).isoformat(), _antes(20).isoformat()]
    assert instantes[0] != instantes[1]
    saida: list[tuple[str, object]] = []

    def abre(instante: str) -> Callable[[], int | None]:
        return lambda: _abrir_execucao("AAA3", instante, 42, BARATOS)

    threads = [
        _parte(f"abertura{i}", abre(instante), saida)
        for i, instante in enumerate(instantes)
    ]
    _junta(*threads)

    resultados = _resultados(saida)
    assert RiskRun.objects.count() == 1
    run = RiskRun.objects.get()
    assert sorted(resultados.values(), key=lambda r: r is None) == [run.pk, None]
    assert len(fila) == 1
    _invariante()


def test_o_fecho_espera_a_abertura_que_leu_a_running_e_fecha_o_pedido_ligado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fecho sem trava: parte a abertura com pedido; ela para depois de ler a `running`; o
    fecho so parte depois. Com a trava, o fecho espera a abertura ligar e confirmar."""
    asset = _serie("AAA3")
    running = _running(asset, _antes(60))
    req = _pedido(asset)
    abertura_leu = threading.Event()
    fecho_terminou = threading.Event()

    def abertura_para() -> None:
        abertura_leu.set()
        fecho_terminou.wait(ESPERA_DO_LADO_DA_MUTACAO)

    monkeypatch.setattr("apps.risk.tasks._after_read_running", abertura_para)

    def fecha() -> None:
        try:
            _fechar_execucao([], running.pk)
        finally:
            fecho_terminou.set()

    saida: list[tuple[str, object]] = []
    abertura = _parte(
        "abertura",
        lambda: _abrir_execucao(
            "AAA3", _antes(5).isoformat(), 42, BARATOS, request_id=req.pk
        ),
        saida,
    )
    assert abertura_leu.wait(ESPERA_DO_LADO_DA_MUTACAO)
    fecho = _parte("fecho", fecha, saida)
    _junta(abertura, fecho)

    resultados = _resultados(saida)
    assert resultados["abertura"] == {
        "outcome": "already_running",
        "run_id": running.pk,
        "sessions": None,
    }
    running.refresh_from_db()
    assert running.status == RiskRun.Status.FAILED
    gravado = ComputeRequest.objects.get(pk=req.pk)
    assert (gravado.status, gravado.reason, gravado.risk_run_id) == (
        Status.FAILED,
        "a execucao falhou",
        running.pk,
    )
    _invariante()


def test_a_abertura_nao_le_enquanto_o_fecho_segura_a_trava(
    monkeypatch: pytest.MonkeyPatch, fila: list[Any]
) -> None:
    """Fecho sem transacao: parte o fecho; ele para depois de tomar a trava; a abertura so
    parte depois. Com a transacao, a abertura espera a trava, le a execucao ja fechada e abre
    outra."""
    asset = _serie("AAA3")
    running = _running(asset, _antes(60))
    req = _pedido(asset)
    fecho_travou = threading.Event()
    abertura_leu = threading.Event()
    fecho_terminou = threading.Event()

    def fecho_para() -> None:
        fecho_travou.set()
        abertura_leu.wait(ESPERA_QUE_ESTOURA)

    def abertura_para() -> None:
        abertura_leu.set()
        fecho_terminou.wait(ESPERA_DO_LADO_DA_MUTACAO)

    monkeypatch.setattr("apps.risk.tasks._after_close_lock", fecho_para)
    monkeypatch.setattr("apps.risk.tasks._after_read_running", abertura_para)

    def fecha() -> None:
        try:
            _fechar_execucao([], running.pk)
        finally:
            fecho_terminou.set()

    saida: list[tuple[str, object]] = []
    fecho = _parte("fecho", fecha, saida)
    assert fecho_travou.wait(ESPERA_DO_LADO_DA_MUTACAO)
    abertura = _parte(
        "abertura",
        lambda: _abrir_execucao(
            "AAA3", _antes(5).isoformat(), 42, BARATOS, request_id=req.pk
        ),
        saida,
    )
    _junta(fecho, abertura)

    resultados = _resultados(saida)
    running.refresh_from_db()
    assert running.status == RiskRun.Status.FAILED
    nova = RiskRun.objects.exclude(pk=running.pk).get()
    assert resultados["abertura"] == {
        "outcome": "opened",
        "run_id": nova.pk,
        "sessions": None,
    }
    assert nova.status == RiskRun.Status.RUNNING
    gravado = ComputeRequest.objects.get(pk=req.pk)
    assert (gravado.status, gravado.risk_run_id) == (Status.RUNNING, nova.pk)
    assert len(fila) == 1
    _invariante()


# --- a guarda dos dados de migration -------------------------------------------------------


def test_os_dados_de_migration_voltaram_depois_dos_transacionais() -> None:
    """O ultimo do modulo: os anteriores truncaram os quatro esquemas, e a `banco_limpo` os
    recriou. Sem a recriacao, a organizacao e o `IBOV` sumiriam daqui em diante."""
    assert list(Organization.objects.values_list("slug", flat=True)) == ["ruvor"]
    assert list(Asset.objects.values_list("ticker", flat=True)) == ["IBOV"]
