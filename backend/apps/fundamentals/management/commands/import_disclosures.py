"""`manage.py import_disclosures [--full | --reconform [ANO ...]]`: a casca de linha de
comando sobre `run_import_disclosures`, no molde de `import_fundamentals`.

`CvmClient` e importado pelo nome, e nao pelo modulo, de proposito: e o ponto que um teste
pode substituir com `monkeypatch`. `run_import_disclosures` tambem e chamado pelo nome
global, e o que `tests/fundamentals/test_import_disclosures_command.py` substitui.

`--full` e `--reconform` ficam num grupo mutuamente exclusivo: o `argparse` recusa os dois
juntos antes de o comando chamar qualquer coisa. `--reconform` sem ano e "todos os anos"
(`[]`); ausente, a coleta normal (`None`).
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.fundamentals.cvm import CvmClient
from apps.fundamentals.disclosures_importer import (
    DisclosuresImportFailed,
    run_import_disclosures,
)


class Command(BaseCommand):
    help = "Coleta na CVM os documentos do IPE e conforma a silver.disclosure"

    def add_arguments(self, parser: CommandParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--full", action="store_true")
        group.add_argument("--reconform", nargs="*", type=int, default=None)

    def handle(self, *args: Any, **options: Any) -> None:
        full: bool = options["full"]
        reconform: list[int] | None = options["reconform"]
        try:
            report = run_import_disclosures(CvmClient(), full=full, reconform=reconform)
        except DisclosuresImportFailed as exc:
            # O relatorio inteiro vai para stdout; a CommandError vai para stderr e sai 1.
            self.stdout.write(exc.report.render() + "\n")
            raise CommandError(
                "coleta com falhas: " + ", ".join(exc.report.failures())
            ) from exc
        self.stdout.write(report.render() + "\n")
