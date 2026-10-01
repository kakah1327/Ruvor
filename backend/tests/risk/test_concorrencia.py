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

**As corridas do M1.5c**, pelos pontos de desvio `_after_close_count` de `apps/risk/compute.py`
e `_before_write_lock` de `apps/risk/tasks.py`. A execucao semeada tem `calculated_at` de 7 h
atras, e a varredura e chamada com `older_than` de 6 h. O que um desvio precisa reprovar e
gravado numa lista e conferido depois do `_junta`: um `assert` dentro do desvio seria engolido
pelo `try` da tarefa ou da varredura.

- **a varredura x o fecho (V-08)**: parte a varredura; ela para dentro da trava, entre a
  contagem e o `UPDATE`, esperando um evento que nao chega (2 s); o fecho so parte depois e
  bloqueia na trava. A espera estoura, a varredura escreve e solta; o fecho rele e chama o
  `close_run`, que acha a linha fechada e nao escreve. Sem o filtro `status=running` do
  `close_run`, o fecho reescreve `status` e `finished_at` e fecha os pedidos;
- **a varredura x a tarefa por modelo (V-08b)**: parte a tarefa; ela para antes do bloco
  travado da escrita; a varredura so parte depois, toma a trava, conta e, antes do `UPDATE`,
  libera a tarefa e espera (2 s) o evento que a tarefa marca depois de gravar. Com as duas
  travas, a tarefa para na trava, a espera estoura, a varredura escreve e solta, e a tarefa
  rele, acha fechada e descarta; sem uma delas, a tarefa grava no meio, o evento chega e as
  linhas passam das contadas;
- **a abertura que nao enfileira (V-09)**: sem thread. O broker recusa o `chord` no
  `on_commit`, que roda de verdade na saida do `atomic`; a abertura fecha a propria execucao
  `failed`, sem resultado, e o pedido ligado a ela.

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
from apps.risk.compute import status_for, write_failed
from apps.risk.models import RiskResult, RiskRun
from apps.risk.stale import StaleReport, close_stale_runs
from apps.risk.tasks import _abrir_execucao, _compute_asset_model, _fechar_execucao
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


# --- M1.5c: a varredura, o fecho e a tarefa por modelo (V-08, V-08b, V-09) ---------------

VELHA = timedelta(hours=7)
PRAZO_DA_VARREDURA = timedelta(hours=6)


def test_varredura_e_fecho_concorrentes_um_so_escreve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """V-08 -- guarda do filtro `status=running` do `close_run`. A varredura parte primeiro e
    para dentro da trava, entre a contagem e o UPDATE, esperando 2 s (`ESPERA_QUE_ESTOURA`)
    por um evento que nao chega; o fecho do `chord` parte e bloqueia na trava; a varredura
    escreve e solta; o fecho rele e chama `close_run`, que acha a linha fechada e nao escreve.
    Sem o filtro, o fecho reescreve `status` e `finished_at` e fecha os pedidos."""
    asset = _serie("AAA3")
    run = _running(asset, timezone.now() - VELHA)
    agora_da_varredura = timezone.now()
    varredura_contou = threading.Event()
    nunca = threading.Event()
    esperas: list[bool] = []
    fechou_pedidos: list[int] = []

    def varredura_para() -> None:
        # o `close_run` do fecho passa pelo mesmo desvio: so a varredura para
        if threading.current_thread().name != "varredura":
            return
        varredura_contou.set()
        esperas.append(nunca.wait(ESPERA_QUE_ESTOURA))

    def espiao_close_linked(run_: RiskRun, now: datetime) -> int:
        fechou_pedidos.append(run_.pk)
        return 0

    monkeypatch.setattr("apps.risk.compute._after_close_count", varredura_para)
    monkeypatch.setattr("apps.risk.tasks.close_linked", espiao_close_linked)

    saida: list[tuple[str, object]] = []
    varredura = _parte(
        "varredura",
        lambda: close_stale_runs(agora_da_varredura, PRAZO_DA_VARREDURA),
        saida,
    )
    assert varredura_contou.wait(ESPERA_DO_LADO_DA_MUTACAO)
    fecho = _parte("fecho", lambda: _fechar_execucao([], run.pk), saida)
    _junta(varredura, fecho)

    resultados = _resultados(saida)
    assert esperas == [False]  # ninguem marcou: a espera estourou
    relatorio = resultados["varredura"]
    assert isinstance(relatorio, StaleReport)
    [fechada] = relatorio.runs
    assert (fechada.run_id, fechada.already_closed) == (run.pk, False)
    run.refresh_from_db()
    # o que ficou gravado e o da varredura, nao o do fecho
    assert (run.status, run.finished_at) == (fechada.status, agora_da_varredura)
    assert fechou_pedidos == []  # o fecho nao fechou pedido nenhum


def test_a_contagem_da_varredura_vale_no_update_com_a_tarefa_gravando_no_meio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """V-08b -- guarda das duas travas. Ordem fixa: (1) a tarefa parte e para antes do bloco
    travado; (2) a varredura parte, toma a trava, conta e para antes do UPDATE; (3) a tarefa e
    liberada; (4) a varredura espera, por 2 s (`ESPERA_QUE_ESTOURA`), o evento que a tarefa marca
    depois de confirmar a gravacao. A serie do `_serie` esta na janela do `_running`, entao a
    tarefa passa da conferencia da janela e cai no `RuntimeError` do duplo -- o par de erro. Correto: a tarefa esta parada na trava, o evento nao chega, a espera
    estoura, a varredura escreve e solta; a tarefa rele, acha fechada e descarta. Sem uma das
    travas, a tarefa grava no meio e o evento chega: as linhas passam das contadas."""
    asset = _serie("AAA3")
    run = _running(asset, timezone.now() - VELHA)  # BARATOS: 4 esperados
    write_failed(run, "historical", "RuntimeError: semeado")  # 2 gravados antes

    tarefa_no_desvio = threading.Event()
    libera_tarefa = threading.Event()
    tarefa_gravou = threading.Event()
    esperas_da_tarefa: list[bool] = []
    esperas_da_varredura: list[bool] = []

    def tarefa_para() -> None:
        tarefa_no_desvio.set()
        esperas_da_tarefa.append(libera_tarefa.wait(ESPERA_DO_LADO_DA_MUTACAO))

    def varredura_para() -> None:
        libera_tarefa.set()
        # estoura no caso correto; no mutante, a tarefa grava e marca antes
        esperas_da_varredura.append(tarefa_gravou.wait(ESPERA_QUE_ESTOURA))

    def instantaneo(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(
            "calculo instantaneo do teste"
        )  # cai no par de erro, sem motor

    monkeypatch.setattr("apps.risk.tasks._before_write_lock", tarefa_para)
    monkeypatch.setattr("apps.risk.compute._after_close_count", varredura_para)
    monkeypatch.setattr("apps.risk.tasks.run_models", instantaneo)

    def tarefa() -> None:
        _compute_asset_model(
            run.pk, "parametric"
        )  # nunca levanta; devolve depois do commit
        tarefa_gravou.set()

    saida: list[tuple[str, object]] = []
    t_tarefa = _parte("tarefa", tarefa, saida)
    assert tarefa_no_desvio.wait(ESPERA_DO_LADO_DA_MUTACAO)
    t_varredura = _parte(
        "varredura",
        lambda: close_stale_runs(timezone.now(), PRAZO_DA_VARREDURA),
        saida,
    )
    _junta(t_tarefa, t_varredura)

    resultados = _resultados(saida)
    assert esperas_da_tarefa == [True]
    relatorio = resultados["varredura"]
    assert isinstance(relatorio, StaleReport)
    assert relatorio.failed == []
    [fechada] = relatorio.runs
    gravadas = RiskResult.objects.filter(run_id=run.pk)
    # o coracao: o que foi contado e o que ficou gravado
    assert gravadas.count() == fechada.written == 2
    run.refresh_from_db()
    assert run.status == status_for(
        4, gravadas.count(), gravadas.exclude(error="").count()
    )
    assert esperas_da_varredura == [False]  # a tarefa nao gravou no meio


def test_a_abertura_que_nao_enfileira_fecha_a_execucao_failed_e_o_pedido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """V-09 -- RF-11. Transacional: o `on_commit` roda de verdade na saida do `atomic`."""
    asset = _serie("AAA3")
    req = _pedido(asset)

    def broker_recusa(group: Any) -> None:
        raise ConnectionError("broker fora do ar")

    monkeypatch.setattr("apps.risk.tasks._enqueue", broker_recusa)

    with pytest.raises(ConnectionError):
        _abrir_execucao("AAA3", _antes(5).isoformat(), 42, BARATOS, request_id=req.pk)

    [run] = RiskRun.objects.filter(asset=asset)
    assert run.status == RiskRun.Status.FAILED
    assert run.finished_at is not None
    assert run.results.count() == 0
    gravado = ComputeRequest.objects.get(pk=req.pk)
    assert (gravado.status, gravado.reason, gravado.risk_run_id) == (
        Status.FAILED,
        "a execucao falhou",
        run.pk,
    )
    _invariante()


# --- a guarda dos dados de migration -------------------------------------------------------


def test_os_dados_de_migration_voltaram_depois_dos_transacionais() -> None:
    """O ultimo do modulo: os anteriores truncaram os quatro esquemas, e a `banco_limpo` os
    recriou. Sem a recriacao, a organizacao e o `IBOV` sumiriam daqui em diante."""
    assert list(Organization.objects.values_list("slug", flat=True)) == ["ruvor"]
    assert list(Asset.objects.values_list("ticker", flat=True)) == ["IBOV"]
