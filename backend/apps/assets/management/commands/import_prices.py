"""`manage.py import_prices [TICKER ...] [--full]`: a casca de linha de comando sobre
`run_import_prices`.

`YahooClient` e importado pelo nome, e nao pelo modulo, de proposito: e o ponto que
`tests/assets/test_import_prices_command.py` substitui com `monkeypatch`.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.assets.prices import InvalidTickers, PricesFailed, run_import_prices
from apps.assets.yahoo import YahooClient


class Command(BaseCommand):
    help = "Coleta no Yahoo os precos historicos dos ativos e conforma a serie diaria"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("tickers", nargs="*")
        parser.add_argument("--full", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        tickers: list[str] = options["tickers"]
        full: bool = options["full"]
        try:
            report = run_import_prices(YahooClient(), tickers, full=full)
        except PricesFailed as exc:
            # O relatorio inteiro vai para stdout; a CommandError vai para stderr e sai 1.
            self.stdout.write(exc.report.render() + "\n")
            failed = [r.ticker for r in exc.report.results if r.error]
            raise CommandError("coleta com falhas: " + ", ".join(failed)) from exc
        except InvalidTickers as exc:
            raise CommandError(
                "tickers invalidos ou inativos: " + ", ".join(exc.tickers)
            ) from exc
        self.stdout.write(report.render() + "\n")
