"""`manage.py import_prices`: a casca entrega o relatorio e converte as falhas (RF-04, RF-13).

O `YahooClient` e substituido no ponto em que o comando o importa
(`apps.assets.management.commands.import_prices.YahooClient`) por uma `FakeYahoo`; o
`sem_rede` do `conftest` garante que nada sai para a rede se o patch falhar.
"""

from __future__ import annotations

import re
from io import StringIO
from typing import Any

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from apps.assets.models import Asset
from apps.assets.yahoo import ChartResponse
from tests.assets.conftest import FakeYahoo, fixture_json

pytestmark = pytest.mark.django_db

PATCH_POINT = "apps.assets.management.commands.import_prices.YahooClient"


def fake_yahoo_factory(source: FakeYahoo) -> Any:
    def factory(*args: object, **kwargs: object) -> FakeYahoo:
        return source

    return factory


def make_asset(ticker: str) -> Asset:
    now = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=now,
        updated_at=now,
    )


def chart(nome: str, status: int = 200) -> ChartResponse:
    return ChartResponse(status, fixture_json(nome, subdir="yahoo"))


def test_rf13_comando_escreve_o_relatorio_em_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_asset("PETR4")
    source = FakeYahoo({"PETR4.SA": [chart("PETR4_tail")]})
    monkeypatch.setattr(PATCH_POINT, fake_yahoo_factory(source))
    stdout = StringIO()

    call_command("import_prices", "PETR4", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(r"^PETR4 inicial: ", saida, re.MULTILINE)
    assert re.search(r"^coleta: ", saida, re.MULTILINE)


def test_rf13_falha_escreve_o_relatorio_e_vira_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    make_asset("PETR4")
    source = FakeYahoo({"PETR4.SA": [chart("not_found", status=404)]})
    monkeypatch.setattr(PATCH_POINT, fake_yahoo_factory(source))
    stdout = StringIO()

    with pytest.raises(CommandError, match=r"^coleta com falhas: PETR4$"):
        call_command("import_prices", "PETR4", stdout=stdout)

    saida = stdout.getvalue()
    assert re.search(r"^PETR4 inicial: FALHOU \(", saida, re.MULTILINE)
    assert re.search(r"^coleta: 1 ativos, 0 ok, 1 falhos, ", saida, re.MULTILINE)


def test_rf04_ticker_desconhecido_vira_command_error_sem_chamar_a_fonte(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = FakeYahoo({})
    monkeypatch.setattr(PATCH_POINT, fake_yahoo_factory(source))

    with pytest.raises(CommandError, match=r"^tickers invalidos ou inativos: XXXX9$"):
        call_command("import_prices", "XXXX9", stdout=StringIO())

    assert source.calls == []
