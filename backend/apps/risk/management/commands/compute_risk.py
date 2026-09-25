"""`manage.py compute_risk [TICKER ...] [--seed N] [--model NOME ...] [--async]`: a casca
de linha de comando sobre `run_compute_risk` e, com `--async`, sobre `enqueue_compute`.

Molde de `apps/analytics/management/commands/compute_metrics.py`, do M1.3, inclusive na
importacao pelo nome -- e nao pelo modulo --, que e o ponto que
`tests/risk/test_compute_risk_command.py` alcanca.

**A casca nao decide nada**: nao filtra ativo, nao formata relatorio, nao trata metrica.
Selecao de ativos, piso, transacao e relatorio sao de `apps/risk/compute.py`.

As duas opcoes existem porque criterios de verificacao precisam delas:

- `--seed N`, omitida vale `config.DEFAULT_SEED`, aplicado em `run_compute_risk`;
- `--model NOME`, repetivel, omitida valem os nove. A forma imita a do `--model` do
  `ruvor run`, em `engine/cli.py`.

O RF-17 se aplica ao que foi **pedido**: com os nove por padrao, `ModelsMissing` denuncia
registry incompleto; com `--model`, nome errado. E a mesma regra, e e o que impede a
selecao de virar porta dos fundos.

`--async` enfileira uma abertura por ativo e devolve: quem cria a `risk_run` e o worker
(RF-03), entao o relatorio traz os tickers, nunca `run_id`. `InvalidTickers` e
`ModelsMissing` valem nos dois caminhos, com as mesmas mensagens e codigo 1; `RiskFailed`
nao existe no assincrono, porque o comando nao espera resultado.

Sem `--full`: nao ha modo de recoleta neste comando.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.risk.compute import (
    InvalidTickers,
    ModelsMissing,
    RiskFailed,
    run_compute_risk,
)
from apps.risk.tasks import enqueue_compute


class Command(BaseCommand):
    help = "Calcula o VaR e o backtesting dos ativos e grava uma execucao em gold"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("tickers", nargs="*")
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument(
            "--model",
            dest="models",
            action="append",
            default=None,
            metavar="NOME",
            help="Repetir para varios modelos (padrao: os nove do registry)",
        )
        parser.add_argument(
            "--async",
            dest="async_",
            action="store_true",
            help="Enfileira uma abertura por ativo no worker e devolve",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        tickers: list[str] = options["tickers"]
        seed: int | None = options["seed"]
        models: list[str] | None = options["models"]
        try:
            if options["async_"]:
                queued = enqueue_compute(tickers, seed=seed, models=models)
                self.stdout.write(queued.render() + "\n")
                return
            report = run_compute_risk(tickers, seed=seed, models=models)
        except RiskFailed as exc:
            # O relatorio inteiro vai para stdout; a CommandError vai para stderr e sai 1.
            self.stdout.write(exc.report.render() + "\n")
            failed = [r.ticker for r in exc.report.results if r.error]
            raise CommandError("risco com falhas: " + ", ".join(failed)) from exc
        except InvalidTickers as exc:
            raise CommandError(
                "tickers invalidos ou inativos: " + ", ".join(exc.tickers)
            ) from exc
        except ModelsMissing as exc:
            raise CommandError(
                "modelos ausentes do registry: " + ", ".join(exc.models)
            ) from exc
        self.stdout.write(report.render() + "\n")
