"""M5.1, T4 — V-10: a tarefa `calcular_retornos`, o quinto elo da `rotina_diaria`.

`_calcular_retornos` e chamada direto, como as funcoes com sublinhado das outras tarefas;
os duplos entram no modulo `apps.returns.tasks`, o nome global que ela chama. **A tarefa
nunca levanta**: a falha de um ativo e qualquer outra excecao viram `"FALHOU: ..."` e ficam
no log.
"""

from __future__ import annotations

import pytest
from django.conf import settings

from apps.returns.compute import ReturnsFailed, ReturnsReport
from apps.returns.models import ReturnRun
from apps.returns.tasks import _calcular_retornos, calcular_retornos
from tests.returns.test_compute import com_serie


@pytest.mark.django_db
def test_a_tarefa_calcula_os_ativos_com_preco_e_devolve_o_relatorio() -> None:
    com_serie("AAA3")
    saida = _calcular_retornos()
    assert ReturnRun.objects.count() == 1
    assert saida.startswith("AAA3")
    assert "retorno: 1 ativos, 1 ok, 0 falhos, 0 pulados" in saida


def test_o_calculo_que_levanta_vira_falhou_e_nao_levanta(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def explode(tickers: list[str]) -> ReturnsReport:
        raise RuntimeError("banco fora do ar")

    monkeypatch.setattr("apps.returns.tasks.run_compute_returns", explode)
    with caplog.at_level("ERROR", logger="apps.returns.tasks"):
        saida = _calcular_retornos()
    assert saida == "FALHOU: RuntimeError: banco fora do ar"
    assert any(r.exc_info is not None for r in caplog.records)


def test_ativo_falho_vira_falhou_com_o_relatorio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relatorio = ReturnsReport([], 0.0)

    def falha(tickers: list[str]) -> ReturnsReport:
        raise ReturnsFailed(relatorio)

    monkeypatch.setattr("apps.returns.tasks.run_compute_returns", falha)
    saida = _calcular_retornos()
    assert saida.startswith("FALHOU: ")


def test_o_nome_registrado_e_o_contrato() -> None:
    assert calcular_retornos.name == "apps.returns.tasks.calcular_retornos"


def test_o_beat_segue_com_as_mesmas_quatro_entradas() -> None:
    """Nenhuma entrada nova no Beat (RF-12): o retorno so entra pela corrente."""
    schedule = settings.CELERY_BEAT_SCHEDULE
    assert set(schedule) == {"catalogo", "precos", "fundamentos", "comunicados"}
    assert not [
        e for e in schedule.values() if str(e["task"]).startswith("apps.returns.")
    ]
