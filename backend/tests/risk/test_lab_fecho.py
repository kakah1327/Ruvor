"""O disparo do laboratorio no fecho do risco (M2.4, RF-09): o V-08 do plano, Tarefa 4.

Todo teste aqui e `transaction=True` (`TRANSACIONAL` e `banco_limpo`): o `on_commit` so roda
num commit de verdade (aprendizado "Num teste `db` comum, o `on_commit`..."), e o callback do
fecho e o que se prova. O fecho e chamado pela funcao com sublinhado, `_fechar_execucao`, fora de
qualquer `atomic` do teste: o `on_commit` dele roda na saida do `atomic` do proprio fecho.

**O `_enqueue` e substituido** por um espiao que guarda a assinatura e o
`connection.in_atomic_block` do instante da chamada -- que tem de ser falso: depois do commit, e
nao dentro da transacao do fecho. Um espiao em `lab_due` registra o mesmo.

A execucao de risco e montada no banco: `open_run` com um modelo barato e as duas linhas dele
gravadas a mao -- limpas (`ok`), uma com erro (`partial`) ou nenhuma (`failed`). O ativo do
experimento devido tem a serie rala de `tests/risk/lab_de_teste.py` (a decada completa).

**O broker real nunca e chamado**: o ultimo teste nao substitui o `_enqueue`; troca o
`apply_async` de `calcular_laboratorio` por um que reprova, e fecha a execucao de um ativo sem a
decada -- o callback roda (o espiao de `lab_due` o ve) e nao enfileira.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from django.db import DatabaseError, connection
from django.utils import timezone

from apps.assets.models import Asset
from apps.risk import config
from apps.risk.compute import open_run
from apps.risk.decade import valid_bars
from apps.risk.lab import lab_due
from apps.risk.models import LabRun, RiskResult, RiskRun
from apps.risk.tasks import _fechar_execucao, calcular_laboratorio
from tests.api.migracao import TRANSACIONAL, banco_limpo  # noqa: F401
from tests.risk.lab_de_teste import ativo, serie_rala

pytestmark = [TRANSACIONAL, pytest.mark.usefixtures("banco_limpo")]


@pytest.fixture
def fila(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Any, bool]]:
    """O espiao do `_enqueue`: a assinatura e se havia transacao aberta na chamada."""
    recebidos: list[tuple[Any, bool]] = []

    def espiao(signature: Any) -> None:
        recebidos.append((signature, connection.in_atomic_block))

    monkeypatch.setattr("apps.risk.tasks._enqueue", espiao)
    return recebidos


@pytest.fixture
def consultas(monkeypatch: pytest.MonkeyPatch) -> list[bool]:
    """O espiao de `lab_due`: o `in_atomic_block` de cada consulta; delega ao verdadeiro."""
    vistos: list[bool] = []

    def espiao(asset: Asset) -> Any:
        vistos.append(connection.in_atomic_block)
        return lab_due(asset)

    monkeypatch.setattr("apps.risk.tasks.lab_due", espiao)
    return vistos


def _execucao(asset: Asset, desfecho: str) -> RiskRun:
    """Uma `risk_run` `running` de um modelo, com as linhas do desfecho pedido."""
    run = open_run(
        asset,
        timezone.now(),
        config.DEFAULT_SEED,
        valid_bars(asset),
        ["parametric"],
        full=False,
    )
    erros = {"ok": ("", ""), "partial": ("", "boom"), "failed": None}[desfecho]
    if erros is not None:
        for alpha, erro in zip(("0.0500", "0.0100"), erros, strict=True):
            RiskResult.objects.create(
                run=run,
                model_name="parametric",
                model_category="traditional",
                alpha=Decimal(alpha),
                hyperparameters={},
                error=erro,
            )
    return run


def _ativo_devido(ticker: str = "LABS3") -> Asset:
    asset = ativo(ticker)
    serie_rala(asset)
    assert lab_due(asset) is not None
    return asset


def _so_o_laboratorio(fila: list[tuple[Any, bool]], asset: Asset) -> None:
    assert len(fila) == 1, fila
    assinatura, em_transacao = fila[0]
    assert assinatura.task == "apps.risk.tasks.calcular_laboratorio"
    assert tuple(assinatura.args) == (asset.pk, "risk_close")
    assert em_transacao is False


# --- enfileira ----------------------------------------------------------------------------


@pytest.mark.parametrize("desfecho", ["ok", "partial"])
def test_o_fecho_ok_ou_partial_enfileira_o_experimento_devido(
    fila: list[tuple[Any, bool]], consultas: list[bool], desfecho: str
) -> None:
    asset = _ativo_devido()
    run = _execucao(asset, desfecho)
    _fechar_execucao([], run.pk)
    run.refresh_from_db()
    assert run.status == desfecho
    _so_o_laboratorio(fila, asset)
    assert consultas == [False]  # a consulta "e devido?" fora do `atomic` do fecho


def test_com_so_um_partial_gravado_enfileira(fila: list[tuple[Any, bool]]) -> None:
    asset = _ativo_devido()
    devido = lab_due(asset)
    assert devido is not None
    _grava_lab(asset, devido[0], LabRun.Status.PARTIAL)
    _fechar_execucao([], _execucao(asset, "ok").pk)
    _so_o_laboratorio(fila, asset)


# --- nao enfileira ------------------------------------------------------------------------


def _grava_lab(asset: Asset, ident: Any, status: str) -> LabRun:
    ultimo = valid_bars(asset)[-1]
    return LabRun.objects.create(
        asset=asset,
        calculated_at=timezone.now(),
        finished_at=timezone.now(),
        status=status,
        origin=LabRun.Origin.COMMAND,
        library_versions=ident.library_versions,
        as_of_date=ultimo.date,
        price_count=1,
        train_count=252,
        test_count=1,
        year_count=1,
        price_run=ultimo.run,
        price_fingerprint="f" * 64,
        requested_models=[],
        **{k: v for k, v in ident.fields().items() if k != "asset_id"},
    )


def test_com_ok_da_identidade_nao_enfileira(fila: list[tuple[Any, bool]]) -> None:
    asset = _ativo_devido()
    devido = lab_due(asset)
    assert devido is not None
    _grava_lab(asset, devido[0], LabRun.Status.OK)
    _fechar_execucao([], _execucao(asset, "ok").pk)
    assert fila == []


def test_o_fecho_failed_nao_enfileira(
    fila: list[tuple[Any, bool]], consultas: list[bool]
) -> None:
    asset = _ativo_devido()
    run = _execucao(asset, "failed")
    _fechar_execucao([], run.pk)
    run.refresh_from_db()
    assert run.status == RiskRun.Status.FAILED
    assert fila == []
    assert consultas == []  # o callback nem e registrado


def test_close_run_devolvendo_none_nao_enfileira(
    fila: list[tuple[Any, bool]], consultas: list[bool]
) -> None:
    asset = _ativo_devido()
    run = _execucao(asset, "ok")
    _fechar_execucao([], run.pk)  # fecha `ok`, e enfileira uma vez
    assert len(fila) == 1
    fila.clear()
    consultas.clear()
    _fechar_execucao([], run.pk)  # ja fechada: `close_run` devolve `None`
    assert fila == []
    assert consultas == []


def test_o_ativo_inativo_nao_enfileira(fila: list[tuple[Any, bool]]) -> None:
    asset = _ativo_devido()
    run = _execucao(asset, "ok")
    Asset.objects.filter(pk=asset.pk).update(status=Asset.Status.INACTIVE)
    _fechar_execucao([], run.pk)
    assert fila == []


def test_a_decada_incompleta_nao_enfileira(fila: list[tuple[Any, bool]]) -> None:
    asset = ativo()
    serie_rala(asset, 700)
    _fechar_execucao([], _execucao(asset, "ok").pk)
    assert fila == []


# --- o fecho nunca falha pelo experimento --------------------------------------------------


def test_lab_due_levantando_o_fecho_nao_levanta_e_a_execucao_fica_ok(
    monkeypatch: pytest.MonkeyPatch, fila: list[tuple[Any, bool]]
) -> None:
    def quebra(asset: Asset) -> Any:
        raise DatabaseError("banco fora")

    monkeypatch.setattr("apps.risk.tasks.lab_due", quebra)
    asset = _ativo_devido()
    run = _execucao(asset, "ok")
    _fechar_execucao([], run.pk)  # nao levanta
    assert RiskRun.objects.get(pk=run.pk).status == RiskRun.Status.OK
    assert fila == []


def test_o_broker_levantando_o_fecho_nao_levanta_e_a_execucao_fica_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def recusa(signature: Any) -> None:
        raise ConnectionError("broker fora")

    monkeypatch.setattr("apps.risk.tasks._enqueue", recusa)
    asset = _ativo_devido()
    run = _execucao(asset, "ok")
    _fechar_execucao([], run.pk)  # nao levanta
    assert RiskRun.objects.get(pk=run.pk).status == RiskRun.Status.OK


# --- o broker real nunca e chamado ---------------------------------------------------------


def test_o_callback_sem_experimento_devido_nao_chama_o_broker(
    monkeypatch: pytest.MonkeyPatch, consultas: list[bool]
) -> None:
    """Sem o `_enqueue` substituido: so o `apply_async` da tarefa, trocado por um que reprova."""
    chamadas: list[Any] = []

    def reprova(*args: Any, **kwargs: Any) -> None:
        chamadas.append((args, kwargs))
        raise AssertionError("o broker real foi chamado")

    monkeypatch.setattr(calcular_laboratorio, "apply_async", reprova)
    asset = ativo()
    serie_rala(asset, 700)  # sem a decada
    run = _execucao(asset, "ok")
    _fechar_execucao([], run.pk)
    assert consultas == [False]  # o callback rodou
    assert chamadas == []
    assert RiskRun.objects.get(pk=run.pk).status == RiskRun.Status.OK
