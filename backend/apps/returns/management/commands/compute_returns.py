"""`manage.py compute_returns [TICKER ...]`: a casca de linha de comando sobre
`run_compute_returns` (M5.1, RF-11), so no `worker`.

Molde de `apps/risk/management/commands/compute_risk.py`. **A casca nao decide nada**:
selecao de ativos, piso, transacao e relatorio sao de `apps/returns/compute.py`. Sai com
codigo 1 (`CommandError`) se algum ativo falhou, com ticker invalido ou inativo, ou com
registry incompleto.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.returns.compute import (
    InvalidTickers,
    ReturnModelsMissing,
    ReturnsFailed,
    run_compute_returns,
)


class Command(BaseCommand):
    help = (
        "Valida os modelos de retorno contra a referencia zero e grava uma execucao "
        "em gold"
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("tickers", nargs="*")

    def handle(self, *args: Any, **options: Any) -> None:
        tickers: list[str] = options["tickers"]
        try:
            report = run_compute_returns(tickers)
        except ReturnsFailed as exc:
            # o relatorio inteiro vai para stdout; a CommandError vai para stderr e sai 1
            self.stdout.write(exc.report.render() + "\n")
            failed = [r.ticker for r in exc.report.results if r.error]
            raise CommandError("retorno com falhas: " + ", ".join(failed)) from exc
        except InvalidTickers as exc:
            raise CommandError(
                "tickers invalidos ou inativos: " + ", ".join(exc.tickers)
            ) from exc
        except ReturnModelsMissing as exc:
            raise CommandError(
                "modelos de retorno ausentes do registry: " + ", ".join(exc.models)
            ) from exc
        self.stdout.write(report.render() + "\n")
