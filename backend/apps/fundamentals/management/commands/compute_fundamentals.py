"""`manage.py compute_fundamentals`: a casca de linha de comando sobre
`run_compute_fundamentals`.

`run_compute_fundamentals` e importada pelo nome, e nao pelo modulo, seguindo o molde de
`apps/analytics/management/commands/compute_metrics.py`: e o ponto que
`tests/fundamentals/test_compute.py` alcanca.

Sem argumentos: calcula todas as acoes ativas do catalogo cuja companhia tem balanco.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.fundamentals.compute import FundamentalsFailed, run_compute_fundamentals


class Command(BaseCommand):
    help = "Calcula os indicadores fundamentalistas das acoes e grava uma linha em gold"

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            report = run_compute_fundamentals()
        except FundamentalsFailed as exc:
            # O relatorio inteiro vai para stdout; a CommandError vai para stderr e sai 1.
            self.stdout.write(exc.report.render() + "\n")
            failed = [r.ticker for r in exc.report.results if r.error]
            raise CommandError("calculo com falhas: " + ", ".join(failed)) from exc
        self.stdout.write(report.render() + "\n")
