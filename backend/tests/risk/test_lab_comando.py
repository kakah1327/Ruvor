"""A tarefa e o comando do laboratorio (M2.4, RF-10, RF-11): o V-09 do plano, Tarefa 4.

A tarefa e exercida pela funcao com sublinhado, `_calcular_laboratorio`; o comando, pela casca,
com `call_command` -- quem desligasse a ligacao entre o comando e o calculo veria estes testes
falharem. O motor e o de troca de `tests/risk/lab_de_teste.py`: nenhum modelo de verdade, nenhuma
rede.

O relatorio do comando tem as seis linhas do plano -- `gravado`, `já calculado`, `década
incompleta (completa em AAAA-MM-DD)`, `série curta`, `inativo` e `FALHOU` -- e o resumo; com um
`failed` gravado, sai com codigo 1 (`CommandError`), com o relatorio inteiro no `stdout`.
"""

from __future__ import annotations

from io import StringIO
from typing import Any

import pytest
from django.core.management import CommandError, call_command
from engine.backtesting import load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig
from engine.models import load_all_model_modules

import apps.risk.compute as compute_module
from apps.assets.models import Asset
from apps.risk.lab import run_lab
from apps.risk.models import LabResult, LabRun
from apps.risk.tasks import _calcular_laboratorio
from tests.risk.lab_de_teste import ativo, motor_parcial, serie_rala

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def registry() -> None:
    load_all_model_modules()
    load_all_backtest_modules()


# --- a tarefa ------------------------------------------------------------------------------


def test_a_tarefa_grava_o_experimento_com_a_origem(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    motor_parcial(monkeypatch)
    asset = ativo()
    serie_rala(asset)
    _calcular_laboratorio(asset.pk, "risk_close")
    run = LabRun.objects.get(asset=asset)
    assert run.status == LabRun.Status.OK
    assert run.origin == LabRun.Origin.RISK_CLOSE
    assert LabResult.objects.filter(run=run).count() == 18


def test_a_tarefa_com_run_lab_levantando_nao_levanta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("falha no laboratorio")

    monkeypatch.setattr("apps.risk.tasks.run_lab", explode)
    asset = ativo()
    serie_rala(asset)
    _calcular_laboratorio(asset.pk, "risk_close")  # nao levanta
    assert LabRun.objects.count() == 0


def test_a_tarefa_com_ativo_que_sumiu_nao_levanta() -> None:
    _calcular_laboratorio(999_999, "risk_close")
    assert LabRun.objects.count() == 0


def test_a_tarefa_com_o_experimento_ja_gravado_pula_sem_gravar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    motor = motor_parcial(monkeypatch)
    asset = ativo()
    serie_rala(asset)
    run_lab(asset, origin=LabRun.Origin.COMMAND)
    assert len(motor.chamadas) == 1
    _calcular_laboratorio(asset.pk, "risk_close")
    assert LabRun.objects.count() == 1
    assert len(motor.chamadas) == 1  # nem calculou


# --- o comando -----------------------------------------------------------------------------


def _comando(*tickers: str) -> tuple[str, CommandError | None]:
    saida = StringIO()
    try:
        call_command("compute_lab", *tickers, stdout=saida)
    except CommandError as exc:
        return saida.getvalue(), exc
    return saida.getvalue(), None


def _linhas(saida: str) -> dict[str, str]:
    return {
        linha[:12].strip(): linha[12:]
        for linha in saida.splitlines()
        if not linha.startswith("laboratorio:")
    }


def test_o_relatorio_tem_as_seis_linhas_e_sai_1_com_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    motor = motor_parcial(monkeypatch)
    # o motor de troca, por baixo de um que falha so no FALH3
    sintetico = vars(compute_module)["run_experiment"]

    def falha_no_falh3(config: ExperimentConfig, provider: Any) -> Any:
        if config.ticker == "FALH3":
            raise ValueError("serie ilegivel")
        return sintetico(config, provider)

    monkeypatch.setattr("apps.risk.compute.run_experiment", falha_no_falh3)

    for ticker in ("GRAV3", "JACA3", "FALH3"):
        serie_rala(ativo(ticker))
    serie_rala(ativo("INCO3"), 700)
    serie_rala(ativo("CURT3"), 400, passo=10)
    serie_rala(ativo("INAT3", status=Asset.Status.INACTIVE))
    run_lab(Asset.objects.get(ticker="JACA3"), origin=LabRun.Origin.COMMAND)

    saida, erro = _comando()

    assert erro is not None
    assert "FALH3" in str(erro)
    linhas = _linhas(saida)
    assert set(linhas) == {"CURT3", "FALH3", "GRAV3", "INCO3", "JACA3", "INAT3"}
    assert linhas["GRAV3"].startswith("gravado (ok)")
    assert "retratos: 0 reaproveitados, 0 treinados" in linhas["GRAV3"]
    assert linhas["JACA3"] == "já calculado"
    assert linhas["INCO3"] == "década incompleta (completa em 2025-01-05)"
    assert linhas["CURT3"] == "série curta (366 pregões, mínimo 503)"
    assert linhas["INAT3"] == "inativo"
    assert linhas["FALH3"] == "FALHOU (ValueError: serie ilegivel)"
    resumo = saida.splitlines()[-1]
    assert resumo.startswith(
        "laboratorio: 6 ativos, 1 gravados, 1 ja calculados, 1 falhos, 3 pulados,"
    ), resumo
    # o gravado e o falho sao `lab_run` com `origin = command`
    assert LabRun.objects.get(asset__ticker="GRAV3").origin == LabRun.Origin.COMMAND
    falho = LabRun.objects.get(asset__ticker="FALH3")
    assert falho.status == LabRun.Status.FAILED
    assert len(motor.chamadas) >= 2


def test_sem_failed_sai_0(monkeypatch: pytest.MonkeyPatch) -> None:
    motor_parcial(monkeypatch)
    serie_rala(ativo("GRAV3"))
    saida, erro = _comando("GRAV3")
    assert erro is None
    assert _linhas(saida)["GRAV3"].startswith("gravado (ok)")
    saida, erro = _comando("GRAV3")
    assert erro is None
    assert _linhas(saida)["GRAV3"] == "já calculado"
    assert LabRun.objects.count() == 1


@pytest.mark.parametrize("ticker", ["NADA3", "INAT3"])
def test_ticker_desconhecido_ou_inativo_aborta_antes_de_calcular(
    monkeypatch: pytest.MonkeyPatch, ticker: str
) -> None:
    motor = motor_parcial(monkeypatch)
    serie_rala(ativo("GRAV3"))
    serie_rala(ativo("INAT3", status=Asset.Status.INACTIVE))
    saida, erro = _comando("GRAV3", ticker)
    assert erro is not None
    assert str(erro) == f"tickers invalidos ou inativos: {ticker}"
    assert saida == ""
    assert motor.chamadas == []
    assert LabRun.objects.count() == 0


def test_o_ativo_pedido_sem_preco_e_serie_curta_com_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    motor_parcial(monkeypatch)
    ativo("VAZI3")
    saida, erro = _comando("VAZI3")
    assert erro is None
    assert _linhas(saida)["VAZI3"] == "série curta (0 pregões, mínimo 503)"


def test_a_excecao_que_escapa_do_run_lab_e_falhou_e_sai_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("escrita quebrada")

    monkeypatch.setattr("apps.risk.management.commands.compute_lab.run_lab", explode)
    serie_rala(ativo("GRAV3"))
    saida, erro = _comando("GRAV3")
    assert erro is not None
    assert _linhas(saida)["GRAV3"] == "FALHOU (RuntimeError: escrita quebrada)"


def test_sem_candidato_diz_informe_tickers() -> None:
    saida, erro = _comando()
    assert erro is None
    assert saida.strip() == "nenhum ativo ativo com preco; informe tickers"
