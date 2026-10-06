"""M5.1, T3: `manage.py compute_returns`, pela casca (`call_command`): com e sem tickers, e
o codigo 1 (`CommandError`) numa falha, num ticker invalido e no registry incompleto."""

from __future__ import annotations

from io import StringIO
from typing import Any

import pytest
from django.core.management import CommandError, call_command

import apps.returns.compute as compute_module
from apps.returns.models import ReturnResult, ReturnRun
from apps.risk import config as risk_config
from tests.returns.test_compute import com_serie, cria_ativo, cria_serie

pytestmark = pytest.mark.django_db


def _roda(*args: str) -> str:
    saida = StringIO()
    call_command("compute_returns", *args, stdout=saida)
    return saida.getvalue()


def test_com_tickers_calcula_so_os_pedidos() -> None:
    com_serie("AAA3")
    com_serie("BBB3")
    saida = _roda("AAA3")
    assert list(ReturnRun.objects.values_list("asset__ticker", flat=True)) == ["AAA3"]
    assert ReturnResult.objects.count() == 2
    assert "AAA3" in saida and "retorno: 1 ativos, 1 ok, 0 falhos, 0 pulados" in saida


def test_sem_tickers_calcula_os_ativos_com_preco() -> None:
    com_serie("AAA3")
    com_serie("BBB3")
    inativo = cria_ativo("OLD3", status="inactive")
    cria_serie(inativo, risk_config.MIN_SESSIONS)
    saida = _roda()
    assert sorted(ReturnRun.objects.values_list("asset__ticker", flat=True)) == [
        "AAA3",
        "BBB3",
    ]
    assert "retorno: 3 ativos, 2 ok, 0 falhos, 1 pulados" in saida


def test_falha_de_um_ativo_sai_com_codigo_1_e_imprime_o_relatorio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    com_serie("AAA3")

    def explode(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("na escrita")

    monkeypatch.setattr(compute_module, "write_returns", explode)
    saida = StringIO()
    with pytest.raises(CommandError, match="retorno com falhas: AAA3"):
        call_command("compute_returns", "AAA3", stdout=saida)
    assert "FALHOU (RuntimeError: na escrita)" in saida.getvalue()
    assert ReturnRun.objects.count() == 0


def test_ticker_invalido_sai_com_codigo_1() -> None:
    with pytest.raises(CommandError, match="tickers invalidos ou inativos: NAO3"):
        _roda("NAO3")


def test_registry_incompleto_sai_com_codigo_1(monkeypatch: pytest.MonkeyPatch) -> None:
    com_serie("AAA3")
    monkeypatch.setattr(compute_module, "RETURN_MODELS", ("ar_1", "nao_existe"))
    with pytest.raises(CommandError, match="ausentes do registry: nao_existe"):
        _roda("AAA3")
    assert ReturnRun.objects.count() == 0


def test_o_codigo_de_saida_do_processo_e_1(monkeypatch: pytest.MonkeyPatch) -> None:
    """`CommandError` vira `SystemExit(1)` quando o comando roda pela linha de comando."""
    from django.core.management import ManagementUtility

    monkeypatch.setattr(compute_module, "RETURN_MODELS", ("nao_existe",))
    with pytest.raises(SystemExit) as exc:
        ManagementUtility(["manage.py", "compute_returns"]).execute()
    assert exc.value.code == 1
