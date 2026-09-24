"""`manage.py compute_metrics`: a casca entrega o relatorio e converte as falhas.

Os tres casos rodam **pela casca**, com `call_command`, e nunca chamando
`run_compute_metrics` direto: o M1.2 registrou como lacuna ter testado o `--full` do
`import_prices` so por dentro, onde trocar o argumento passado pela casca nao reprovaria
nada. Aqui, quem desligasse a ligacao entre o comando e o calculo veria estes testes
falharem.

A serie e mensal, como em `test_compute.py`, pelo mesmo motivo: exerce as janelas de
calendario sem criar milhares de linhas. Os numeros das metricas nao se conferem aqui --
isso e de `test_metrics.py`.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from apps.analytics.metrics import Metrics
from apps.analytics.models import BehaviorMetric
from apps.assets.models import Asset, CollectionRun, Price

pytestmark = pytest.mark.django_db

Q10 = Decimal("0.0000000001")
DIA = 15


def meses(ano: int, mes: int, quantidade: int) -> list[date]:
    """`quantidade` datas mensais consecutivas, dia 15, a partir de `(ano, mes)`."""
    datas = []
    for i in range(quantidade):
        total = ano * 12 + (mes - 1) + i
        y, m = divmod(total, 12)
        datas.append(date(y, m + 1, DIA))
    return datas


# 129 meses de 2016-01-15 a 2026-09-15: toda janela de retorno existe.
SERIE_LONGA = meses(2016, 1, 129)


def make_asset(ticker: str, *, status: str = Asset.Status.ACTIVE) -> Asset:
    now = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=now,
        updated_at=now,
    )


def make_prices(asset: Asset, datas: list[date]) -> None:
    """Serie crescente: `adj_close` 100, 101, 102... e `log_return` = ln(adj/anterior)."""
    run = CollectionRun.objects.create(source="teste", started_at=timezone.now())
    now = timezone.now()
    anterior: Decimal | None = None
    linhas = []
    for i, d in enumerate(datas):
        adj = Decimal(100 + i)
        log_return = None if anterior is None else (adj / anterior).ln().quantize(Q10)
        linhas.append(
            Price(
                asset=asset,
                date=d,
                open=adj,
                high=adj,
                low=adj,
                close=adj,
                adj_close=adj,
                volume=1000 + i,
                log_return=log_return,
                run=run,
                updated_at=now,
            )
        )
        anterior = adj
    Price.objects.bulk_create(linhas)


def com_serie_longa(ticker: str) -> Asset:
    asset = make_asset(ticker)
    make_prices(asset, SERIE_LONGA)
    return asset


def test_comando_grava_e_escreve_o_relatorio_em_stdout() -> None:
    make_prices(Asset.objects.get(ticker="IBOV"), SERIE_LONGA)  # o IBOV da migration
    com_serie_longa("AAA3")
    stdout = StringIO()

    call_command("compute_metrics", "AAA3", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(r"^AAA3\s+129 pregoes  ate 2026-09-15  ok", saida, re.MULTILINE)
    assert re.search(
        r"^metricas: 1 ativos, 1 ok, 0 falhos, 0 pulados, ", saida, re.MULTILINE
    )
    assert BehaviorMetric.objects.filter(asset__ticker="AAA3").count() == 1


def test_ticker_invalido_vira_command_error_com_saida_1_e_nao_escreve() -> None:
    com_serie_longa("AAA3")

    with pytest.raises(CommandError) as info:
        call_command("compute_metrics", "AAA3", "XPTO9", stdout=StringIO())

    assert str(info.value) == "tickers invalidos ou inativos: XPTO9"
    assert info.value.returncode == 1
    assert BehaviorMetric.objects.count() == 0


def test_falha_escreve_o_relatorio_antes_de_sair_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_prices(Asset.objects.get(ticker="IBOV"), SERIE_LONGA)
    com_serie_longa("AAA3")
    com_serie_longa("BBB3")

    def fake_write(
        asset: Asset, calculated_at: datetime, metrics: Metrics
    ) -> BehaviorMetric:
        raise RuntimeError("gravacao quebrou")

    monkeypatch.setattr("apps.analytics.compute.write_metrics", fake_write)
    stdout = StringIO()

    with pytest.raises(CommandError) as info:
        call_command("compute_metrics", "AAA3", "BBB3", stdout=stdout)

    assert str(info.value) == "calculo com falhas: AAA3, BBB3"
    assert info.value.returncode == 1
    saida = stdout.getvalue()  # o relatorio inteiro saiu antes do erro
    assert re.search(
        r"^AAA3\s+129 pregoes  ate 2026-09-15  FALHOU \(RuntimeError: gravacao quebrou\)",
        saida,
        re.MULTILINE,
    )
    assert re.search(
        r"^metricas: 2 ativos, 0 ok, 2 falhos, 0 pulados, ", saida, re.MULTILINE
    )
    assert BehaviorMetric.objects.count() == 0
