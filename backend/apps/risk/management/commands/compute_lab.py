"""`manage.py compute_lab [TICKER ...]`: o experimento da decada, sincrono (M2.4, RF-11).

Roda no contêiner `worker`, com `origin = command`. Sem tickers, os ativos `active` com preco
-- o `_resolve` de `apps/risk/compute.py`, que pula os inativos com preco; com tickers, ticker
desconhecido ou inativo aborta antes de qualquer calculo (`InvalidTickers`, codigo 1).

Uma linha por ativo -- `gravado` (status, segundos, retratos reaproveitados e treinados), `já
calculado`, `década incompleta (completa em AAAA-MM-DD)`, `série curta`, `inativo` ou `FALHOU`
-- e o resumo. Sai com codigo 1 se algum ativo gravou `failed` (ou se o calculo levantou: a
excecao vira a linha `FALHOU` dele, e os outros seguem).

**Nao ha `--full` nem `--force`**: refazer o experimento `ok` da mesma identidade e o que o
RF-07 proibe; motor ou biblioteca novos sao identidade nova. Nenhuma entrada no Beat.

`run_compute_lab` e o `LabReport` moram aqui, e nao em `apps/risk/lab.py`, porque a T4 do plano
nao lista `lab.py` entre os arquivos que muda; a casca (`Command`) so imprime e converte o codigo.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.assets.models import Asset
from apps.risk import config
from apps.risk.compute import EXPENSIVE, NO_CANDIDATES, InvalidTickers, _resolve
from apps.risk.lab import LabOutcome, run_lab
from apps.risk.models import LabResult, LabRun

WRITTEN = "gravado"
ALREADY = "já calculado"
INACTIVE = "inativo"
FAILED = "FALHOU"


def incomplete(end: object) -> str:
    return f"década incompleta (completa em {end})"


def short(sessions: int) -> str:
    return f"série curta ({sessions} pregões, mínimo {config.MIN_SESSIONS})"


@dataclass(frozen=True)
class LabLine:
    """Uma linha do relatorio: o ativo e o que aconteceu com ele."""

    ticker: str
    text: str
    written: bool = False
    failed: bool = False
    already: bool = False

    def render(self) -> str:
        return f"{self.ticker:<12}{self.text}"


@dataclass(frozen=True)
class LabReport:
    lines: list[LabLine]
    elapsed: float

    @property
    def failed(self) -> bool:
        return any(line.failed for line in self.lines)

    def render(self) -> str:
        if not self.lines:
            return NO_CANDIDATES
        written = sum(1 for line in self.lines if line.written and not line.failed)
        failed = sum(1 for line in self.lines if line.failed)
        already = sum(1 for line in self.lines if line.already)
        skipped = len(self.lines) - written - failed - already
        resumo = (
            f"laboratorio: {len(self.lines)} ativos, {written} gravados, "
            f"{already} ja calculados, {failed} falhos, {skipped} pulados, "
            f"{self.elapsed:.1f}s"
        )
        return "\n".join([*(line.render() for line in self.lines), resumo])


def _line(asset: Asset, outcome: LabOutcome) -> LabLine:
    if outcome.kind == LabOutcome.WRITTEN:
        run = outcome.run
        assert run is not None
        if run.status == LabRun.Status.FAILED:
            return LabLine(asset.ticker, f"{FAILED} ({run.error})", True, True)
        caros = LabResult.objects.filter(run=run, model_name__in=EXPENSIVE)
        reused = sum(r.reused_snapshots or 0 for r in caros)
        trained = sum(r.trained_snapshots or 0 for r in caros)
        return LabLine(
            asset.ticker,
            f"{WRITTEN} ({run.status})  {outcome.elapsed:.1f}s  "
            f"retratos: {reused} reaproveitados, {trained} treinados",
            written=True,
        )
    if outcome.kind == LabOutcome.ALREADY:
        return LabLine(asset.ticker, ALREADY, already=True)
    if outcome.kind == LabOutcome.INACTIVE:
        return LabLine(asset.ticker, INACTIVE)
    if outcome.kind == LabOutcome.INCOMPLETE:
        assert outcome.decade is not None
        return LabLine(asset.ticker, incomplete(outcome.decade.end_date))
    # SHORT, e NO_PRICES: o ativo pedido por argumento sem pregao valido nenhum -- como no
    # `compute_risk`, e serie curta com zero pregoes
    sessions = 0 if outcome.decade is None else outcome.decade.sessions
    return LabLine(asset.ticker, short(sessions))


def run_compute_lab(tickers: list[str]) -> LabReport:
    """O experimento de cada ativo pedido, um de cada vez, com `origin = command`."""
    assets, skipped = _resolve(tickers)  # InvalidTickers antes de qualquer calculo
    started = time.monotonic()
    lines: list[LabLine] = []
    for asset in assets:
        try:
            outcome = run_lab(asset, origin=LabRun.Origin.COMMAND)
        except Exception as exc:
            lines.append(
                LabLine(
                    asset.ticker, f"{FAILED} ({type(exc).__name__}: {exc})", True, True
                )
            )
            continue
        lines.append(_line(asset, outcome))
    lines.extend(LabLine(a.ticker, INACTIVE) for a in skipped)
    return LabReport(lines, time.monotonic() - started)


class Command(BaseCommand):
    help = (
        "Calcula o experimento fixo da decada dos ativos e grava em gold (laboratorio)"
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("tickers", nargs="*")

    def handle(self, *args: Any, **options: Any) -> None:
        tickers: list[str] = options["tickers"]
        try:
            report = run_compute_lab(tickers)
        except InvalidTickers as exc:
            raise CommandError(
                "tickers invalidos ou inativos: " + ", ".join(exc.tickers)
            ) from exc
        self.stdout.write(report.render() + "\n")
        if report.failed:
            failed = [line.ticker for line in report.lines if line.failed]
            raise CommandError("laboratorio com falhas: " + ", ".join(failed))
