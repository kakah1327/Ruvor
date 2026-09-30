"""`manage.py close_stale_runs [--dry-run] [--older-than-min N]`: a casca de linha de comando
sobre `close_stale_runs` (M1.5c, RF-07, D-149).

Molde de `compute_risk.py`, inclusive na importacao pelo nome, e **a casca nao decide nada**:
quem lista, trava, rele, fecha e formata e `apps/risk/stale.py`. O comando so escolhe o prazo,
imprime `report.render()` e converte as falhas em codigo de saida.

- `--older-than-min N` ausente usa `settings.RUVOR_RISK_STALE_AFTER`. `N` menor que o
  `RUVOR_ON_DEMAND_TIMEOUT` e recusado com `CommandError`, pela mesma razao da validacao das
  settings: fechar antes de a abertura considerar a linha presa fecharia execucao que a D-92
  ainda protege.
- `--dry-run` so relata o que escreveria.
- Uma execucao que a varredura nao fechou sai com `CommandError` (codigo 1), **depois** de o
  relatorio inteiro ir para stdout. A excecao da listagem vira `CommandError` com a mensagem.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from apps.risk.stale import close_stale_runs


class Command(BaseCommand):
    help = "Fecha pela regra do fecho as execucoes de risco presas em running"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="So relata o que escreveria, sem escrever nada",
        )
        parser.add_argument(
            "--older-than-min",
            dest="older_than_min",
            type=int,
            default=None,
            metavar="N",
            help="Prazo em minutos (padrao: RUVOR_RISK_STALE_AFTER_MIN)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        older_than_min: int | None = options["older_than_min"]
        if older_than_min is None:
            older_than: timedelta = settings.RUVOR_RISK_STALE_AFTER
        else:
            older_than = timedelta(minutes=older_than_min)
            if older_than < settings.RUVOR_ON_DEMAND_TIMEOUT:
                raise CommandError(
                    "--older-than-min nao pode ser menor que RUVOR_ON_DEMAND_TIMEOUT "
                    f"({older_than} < {settings.RUVOR_ON_DEMAND_TIMEOUT})"
                )
        try:
            report = close_stale_runs(timezone.now(), older_than, dry_run=dry_run)
        except Exception as exc:
            raise CommandError(
                f"a listagem das execucoes presas falhou: {exc}"
            ) from exc
        # O relatorio inteiro vai para stdout; a CommandError vai para stderr e sai 1.
        self.stdout.write(report.render() + "\n")
        if report.failed:
            raise CommandError(
                f"{len(report.failed)} execucao(oes) presa(s) nao fechada(s)"
            )
