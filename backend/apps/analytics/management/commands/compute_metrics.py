"""`manage.py compute_metrics [TICKER ...]`: a casca de linha de comando sobre
`run_compute_metrics`.

`run_compute_metrics` e importada pelo nome, e nao pelo modulo, seguindo o molde de
`apps/assets/management/commands/import_prices.py`: e o ponto que
`tests/analytics/test_compute_metrics_command.py` alcanca.

Sem `--full`: nao ha modo de recoleta neste comando.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.analytics.compute import InvalidTickers, MetricsFailed, run_compute_metrics


class Command(BaseCommand):
    help = "Calcula as metricas de comportamento dos ativos e grava uma linha em gold"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("tickers", nargs="*")

    def handle(self, *args: Any, **options: Any) -> None:
        tickers: list[str] = options["tickers"]
        try:
            report = run_compute_metrics(tickers)
        except MetricsFailed as exc:
            # O relatorio inteiro vai para stdout; a CommandError vai para stderr e sai 1.
            self.stdout.write(exc.report.render() + "\n")
            failed = [r.ticker for r in exc.report.results if r.error]
            raise CommandError("calculo com falhas: " + ", ".join(failed)) from exc
        except InvalidTickers as exc:
            raise CommandError(
                "tickers invalidos ou inativos: " + ", ".join(exc.tickers)
            ) from exc
        self.stdout.write(report.render() + "\n")
