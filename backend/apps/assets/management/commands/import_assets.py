"""`manage.py import_assets`: a casca de linha de comando sobre `run_import`.

`B3Client` e importado pelo nome, e nao pelo modulo, de proposito: e o ponto que
`tests/assets/test_command.py` substitui com `monkeypatch`.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.assets.b3 import B3Client
from apps.assets.importer import CollectionFailed, run_import


class Command(BaseCommand):
    help = "Coleta as companhias listadas na B3 e conforma o catalogo de acoes"

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            report = run_import(B3Client())
        except CollectionFailed as exc:
            # O BaseCommand ja escreve a CommandError em stderr e sai com 1.
            raise CommandError(str(exc)) from exc
        self.stdout.write(report.render() + "\n")
