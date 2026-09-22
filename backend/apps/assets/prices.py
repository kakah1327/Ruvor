"""A coleta de precos: por ativo, a resposta do Yahoo para a `bronze` e, em transacao, os
pregoes e eventos para a `silver`.

A sequencia por ativo e contrato da spec ("O comando", passo 3) e vai literal em
`_import_asset`: buscar → gravar `bronze` → validar → conformar → decidir a rebusca →
`atomic()` so em volta de `write_conformed`. Ativo que falha nao muda nada na `silver` e
nao impede os demais (RF-12); a `collection_run` termina `failed` com os tickers falhos e
`run_import_prices` levanta `PricesFailed` carregando o relatorio.

`write_conformed` e chamada pelo nome global, de proposito: e o ponto que o teste da forma
(d) do RF-12 substitui com `monkeypatch.setattr("apps.assets.prices.write_conformed", ...)`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal, Protocol
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from apps.assets.conform_prices import ConformedChart, conform_chart
from apps.assets.models import Asset, CollectionRun, CorporateEvent, Price, YahooChart
from apps.assets.yahoo import ChartResponse

SOURCE = "yahoo-chart"
SAO_PAULO = ZoneInfo("America/Sao_Paulo")
Q10 = Decimal("0.0000000001")

Mode = Literal["inicial", "incremental", "completa"]


class ChartSource(Protocol):
    """O que a coleta pede da fonte. `YahooClient` satisfaz; a `FakeYahoo` dos testes tambem."""

    def chart(self, symbol: str, period1: int, period2: int) -> ChartResponse: ...


class InvalidTickers(Exception):
    """Ticker desconhecido ou inativo pedido por argumento (RF-04). Nada foi chamado."""

    def __init__(self, tickers: list[str]) -> None:
        super().__init__(", ".join(tickers))
        self.tickers = tickers


class InvalidResponse(Exception):
    """Formas (a) e (b) do RF-12: a resposta veio, foi para a `bronze`, mas nao tem serie."""


@dataclass(frozen=True)
class WriteCounts:
    """O que `write_conformed` escreveu para um ativo."""

    created: int
    updated: int
    events_created: int


@dataclass(frozen=True)
class AssetResult:
    """Uma linha do relatorio (RF-13): o que aconteceu com um ativo."""

    ticker: str
    mode: Mode
    received: int
    discarded: int
    created: int
    updated: int
    events: int
    error: str | None
    skipped: bool

    def render(self) -> str:
        if self.skipped:
            return f"{self.ticker}: pulado, inativo no catalogo"
        if self.error is not None:
            return f"{self.ticker} {self.mode}: FALHOU ({self.error})"
        return (
            f"{self.ticker} {self.mode}: {self.received} pregoes, "
            f"{self.discarded} descartados, {self.created} criados, "
            f"{self.updated} atualizados, {self.events} eventos"
        )


@dataclass(frozen=True)
class PricesReport:
    """O relatorio de uma coleta (RF-13): uma linha por ativo e a linha final."""

    results: list[AssetResult]

    @property
    def failed(self) -> bool:
        return any(r.error for r in self.results)

    def render(self) -> str:
        lines = [r.render() for r in self.results]
        asked = [r for r in self.results if not r.skipped]
        if not asked:
            lines.append("nenhum ativo ativo com preco; informe tickers")
            return "\n".join(lines)
        failed = sum(1 for r in asked if r.error)
        lines.append(
            f"coleta: {len(asked)} ativos, {len(asked) - failed} ok, "
            f"{failed} falhos, {len(self.results) - len(asked)} pulados"
        )
        return "\n".join(lines)


class PricesFailed(Exception):
    """A coleta terminou `failed`: algum ativo falhou. `report` e o relatorio inteiro."""

    def __init__(self, report: PricesReport) -> None:
        super().__init__(", ".join(r.ticker for r in report.results if r.error))
        self.report = report


def sp_midnight(d: date) -> int:
    """Meia-noite de `d` em `America/Sao_Paulo`, em segundos unix (RF-10)."""
    return int(datetime(d.year, d.month, d.day, tzinfo=SAO_PAULO).timestamp())


def period1_for(mode: Mode, asset: Asset, now: Callable[[], datetime]) -> int:
    """O `period1` do RF-10: dez anos atras, ultima `date` menos 7 dias, ou a primeira `date`."""
    if mode == "inicial":
        today = now().astimezone(SAO_PAULO).date()
        try:
            start = today.replace(year=today.year - 10)
        except ValueError:  # 29/02 num ano que nao e bissexto
            start = today.replace(year=today.year - 10, day=28)
        return sp_midnight(start)
    if mode == "incremental":
        last = Price.objects.filter(asset=asset).order_by("-date").first()
        assert last is not None, "modo incremental exige preco no banco"
        return sp_midnight(last.date - timedelta(days=7))
    first = Price.objects.filter(asset=asset).order_by("date").first()
    assert first is not None, "modo completa exige preco no banco"
    return sp_midnight(first.date)


def run_import_prices(
    source: ChartSource,
    tickers: list[str],
    *,
    full: bool = False,
    now: Callable[[], datetime] = timezone.now,
) -> PricesReport:
    assets, skipped = _resolve(tickers)  # InvalidTickers antes de qualquer chamada
    if not assets:
        return PricesReport([_skipped(a) for a in skipped])  # sem collection_run
    run = CollectionRun.objects.create(source=SOURCE, started_at=now())
    results = [_skipped(a) for a in skipped]
    for asset in assets:
        results.append(_import_asset(source, run, asset, full=full, now=now))
    failed = any(r.error for r in results)
    run.status = CollectionRun.Status.FAILED if failed else CollectionRun.Status.OK
    run.error = ", ".join(r.ticker for r in results if r.error)
    run.finished_at = now()
    run.save(update_fields=["status", "error", "finished_at"])
    report = PricesReport(results)
    if failed:
        raise PricesFailed(report)
    return report


def _resolve(tickers: list[str]) -> tuple[list[Asset], list[Asset]]:
    """Passo 1 do comando: `(assets, skipped)`, os dois em ordem de ticker.

    Com argumentos: deduplica, ordena, e qualquer ticker ausente ou nao-`active` aborta
    com `InvalidTickers` (RF-04). Sem argumentos: os ativos com preco; os `inactive` sao
    pulados, os `active` sao os pedidos (RF-05).
    """
    if tickers:
        wanted = sorted(set(tickers))
        found = {a.ticker: a for a in Asset.objects.filter(ticker__in=wanted)}
        offenders = [
            t
            for t in wanted
            if t not in found or found[t].status != Asset.Status.ACTIVE
        ]
        if offenders:
            raise InvalidTickers(offenders)
        return [found[t] for t in wanted], []
    candidates = (
        Asset.objects.filter(prices__isnull=False).distinct().order_by("ticker")
    )
    assets = [a for a in candidates if a.status == Asset.Status.ACTIVE]
    skipped = [a for a in candidates if a.status != Asset.Status.ACTIVE]
    return assets, skipped


def _skipped(asset: Asset) -> AssetResult:
    return AssetResult(asset.ticker, "incremental", 0, 0, 0, 0, 0, None, True)


def _mode(asset: Asset, full: bool) -> Mode:
    if not Price.objects.filter(asset=asset).exists():
        return "inicial"  # `--full` sem preco e o mesmo que inicial (RF-11)
    return "completa" if full else "incremental"


def _import_asset(
    source: ChartSource,
    run: CollectionRun,
    asset: Asset,
    *,
    full: bool,
    now: Callable[[], datetime],
) -> AssetResult:
    mode = _mode(asset, full)
    try:
        response = _fetch_and_store(source, run, asset, mode, now)  # forma (c): levanta
        conformed = _validate_and_conform(response)  # formas (a)/(b): levanta
        if mode == "incremental" and _has_new_event(asset, conformed):
            mode = "completa"
            response = _fetch_and_store(source, run, asset, mode, now)
            conformed = _validate_and_conform(response)
        with transaction.atomic():
            counts = write_conformed(asset, run, conformed)  # forma (d): reverte
    except (
        Exception
    ) as exc:  # (a)-(d): YahooClientError, InvalidResponse, e o que a gravacao levantar
        return AssetResult(
            asset.ticker, mode, 0, 0, 0, 0, 0, f"{type(exc).__name__}: {exc}", False
        )
    return AssetResult(
        asset.ticker,
        mode,
        len(conformed.bars) + conformed.discarded,
        conformed.discarded,
        counts.created,
        counts.updated,
        counts.events_created,
        None,
        False,
    )


def _fetch_and_store(
    source: ChartSource,
    run: CollectionRun,
    asset: Asset,
    mode: Mode,
    now: Callable[[], datetime],
) -> ChartResponse:
    """Passo 3.2: pede a serie e grava a resposta como veio, 200 ou nao (RF-03).

    O simbolo sai so de `provider_symbol` (RF-16). `YahooClientError` atravessa: nao ha
    o que gravar.
    """
    symbol = asset.provider_symbol
    period1 = period1_for(mode, asset, now)
    period2 = int(now().timestamp())
    response = source.chart(symbol, period1, period2)
    YahooChart.objects.create(
        run=run,
        asset=asset,
        symbol=symbol,
        period1=period1,
        period2=period2,
        http_status=response.http_status,
        payload=response.payload,
    )
    return response


def _validate_and_conform(response: ChartResponse) -> ConformedChart:
    """Passo 3.3: HTTP != 200, `chart.error` ou sem `chart.result[0]` e `InvalidResponse`."""
    chart = response.payload.get("chart") or {}
    error = chart.get("error")
    if response.http_status != 200 or error:
        description = (error or {}).get("description") or "resposta sem serie"
        raise InvalidResponse(f"HTTP {response.http_status}: {description}")
    if not chart.get("result"):
        raise InvalidResponse(f"HTTP {response.http_status}: sem chart.result[0]")
    return conform_chart(response.payload)


def _has_new_event(asset: Asset, conformed: ConformedChart) -> bool:
    """Passo 3.4: algum evento da resposta ainda nao esta em `corporate_event` (RF-11)."""
    known = set(CorporateEvent.objects.filter(asset=asset).values_list("date", "kind"))
    return any((e.date, e.kind) not in known for e in conformed.events)


def _log_return(current: Decimal, previous: Decimal | None) -> Decimal | None:
    """RF-07: `ln(adj_close_t / adj_close_{t-1})` em `Decimal`, a dez casas."""
    if previous is None:
        return None
    return (current / previous).ln().quantize(Q10)


def write_conformed(
    asset: Asset, run: CollectionRun, conformed: ConformedChart
) -> WriteCounts:
    """O *upsert* de `silver.price` e `silver.corporate_event` de um ativo (RF-07/08/09).

    O antecessor do primeiro pregao e o ultimo ja no banco anterior a ele; dos demais, o
    pregao anterior da resposta. Linha existente so muda — e so entao avanca `run` e
    `updated_at` — quando a tupla quantizada difere. Eventos: `get_or_create`.
    """
    now = timezone.now()
    created = updated = events_created = 0
    bars = conformed.bars
    if bars:
        before = (
            Price.objects.filter(asset=asset, date__lt=bars[0].date)
            .order_by("-date")
            .first()
        )
        previous = before.adj_close if before is not None else None
        existing = {
            p.date: p for p in Price.objects.filter(asset=asset, date__gte=bars[0].date)
        }
        for bar in bars:
            log_return = _log_return(bar.adj_close, previous)
            previous = bar.adj_close
            current = existing.get(bar.date)
            if current is None:
                Price.objects.create(
                    asset=asset,
                    date=bar.date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    adj_close=bar.adj_close,
                    volume=bar.volume,
                    log_return=log_return,
                    run=run,
                    updated_at=now,
                )
                created += 1
                continue
            incoming = (
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.adj_close,
                bar.volume,
                log_return,
            )
            stored = (
                current.open,
                current.high,
                current.low,
                current.close,
                current.adj_close,
                current.volume,
                current.log_return,
            )
            if incoming == stored:
                continue
            (
                current.open,
                current.high,
                current.low,
                current.close,
                current.adj_close,
                current.volume,
                current.log_return,
            ) = incoming
            current.run = run
            current.updated_at = now
            current.save()
            updated += 1

    for event in conformed.events:
        _, was_created = CorporateEvent.objects.get_or_create(
            asset=asset,
            date=event.date,
            kind=CorporateEvent.Kind(event.kind),
            defaults={
                "amount": event.amount,
                "numerator": event.numerator,
                "denominator": event.denominator,
                "run": run,
            },
        )
        events_created += int(was_created)

    return WriteCounts(created=created, updated=updated, events_created=events_created)
