"""A coleta do IPE: os zips de comunicados da CVM para a `bronze` e, por (companhia, ano),
em transacao, os documentos das tres categorias para `silver.disclosure` (M3.2).

A coleta reaproveita a do M3.1 (`_collect`, o "ultimo visto", o hash de conteudo); a
conformacao e propria. A ordem e contrato do plano (RF-07b): as companhias do catalogo sem
nenhuma linha em `silver.disclosure` sao calculadas **antes** da coleta e da conformacao dos
anos alterados (a), e o caminho (b) so conforma para elas os anos que (a) nao conformou. Nao
ha regra de `A+1`: um comunicado nao depende do ano seguinte.

A `silver` e o estado corrente do IPE (RF-04a): conformar (companhia, ano) remove as linhas
daquela companhia no ano cujo link nao esta em `year_links` — o conjunto de **todos** os
links conformados no ano, de todas as companhias lidas. Com os links so da companhia, o link
que passou de X para Y seria apagado por X quando X roda antes de Y, e o resultado dependeria
da ordem das companhias.

`write_disclosure_company_year` e chamada pelo nome global, de proposito: e o ponto que o
teste do RF-07 substitui com `monkeypatch.setattr(
"apps.fundamentals.disclosures_importer.write_disclosure_company_year", ...)`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.assets.models import CollectionRun
from apps.fundamentals.cvm import IPE
from apps.fundamentals.disclosures import (
    ConformedDisclosure,
    DisclosuresByCompany,
    disclosures_from_zip,
)
from apps.fundamentals.importer import (
    CvmSource,
    FileResult,
    Label,
    _catalog,
    _collect,
    _current_versions,
    _error,
    _payload,
)
from apps.fundamentals.models import Disclosure

SOURCE = "cvm-ipe"
FIRST_YEAR = 2016

# As colunas de `silver.disclosure` que vem da conformacao, na ordem da tupla comparada
# (RF-04). `code_cvm` entra: o link que passou de companhia e atualizado (RF-04a). `run` e
# `updated_at` sao da escrita.
DISCLOSURE_FIELDS = (
    "code_cvm",
    "cnpj",
    "company_name",
    "year",
    "link",
    "protocol",
    "version",
    "presentation",
    "category",
    "kind",
    "species",
    "title",
    "reference_date",
    "delivered_on",
)


@dataclass(frozen=True)
class DisclosureCounts:
    """O que `write_disclosure_company_year` escreveu para uma companhia num ano."""

    created: int
    updated: int
    removed: int


@dataclass(frozen=True)
class DisclosureYearResult:
    """As linhas de um ano no relatorio: o resumo, os descartes e as companhias falhas.

    `error` e a falha no nivel do ano — a leitura do zip levantou antes do laco de
    companhias —, e entao o ano nao conformou nada.
    """

    label: Label
    year: int
    companies: int = 0
    created: int = 0
    updated: int = 0
    removed: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)
    malformed: int = 0
    error: str | None = None

    @property
    def failed(self) -> bool:
        return self.error is not None or bool(self.failures)

    def render(self) -> list[str]:
        prefix = f"{self.label} {self.year}"
        if self.error is not None:
            return [f"{prefix}: FALHOU ({self.error})"]
        lines = [
            f"{prefix}: {self.companies} companhias, {self.created} criados, "
            f"{self.updated} atualizados, {self.removed} removidos, "
            f"{len(self.failures)} falhos"
        ]
        if self.malformed > 0:
            lines.append(
                f"{prefix}: {self.malformed} registros mal formados descartados"
            )
        lines.extend(
            f"{prefix}: FALHOU {code} ({error})" for code, error in self.failures
        )
        return lines


@dataclass(frozen=True)
class DisclosuresReport:
    """O relatorio de uma execucao (RF-09).

    Com `--reconform` (`collected` falso) nao houve coleta: as linhas de arquivo e a
    `coleta:` nao sao impressas.
    """

    files: list[FileResult]
    years: list[DisclosureYearResult]
    collected: bool

    @property
    def failed(self) -> bool:
        return any(f.status == "falhou" for f in self.files) or any(
            y.failed for y in self.years
        )

    def render(self) -> str:
        lines = [f.render() for f in self.files] if self.collected else []
        for year in self.years:
            lines.extend(year.render())
        if self.collected:
            counts = {
                status: sum(1 for f in self.files if f.status == status)
                for status in (
                    "novo",
                    "inalterado",
                    "nao modificado",
                    "ausente",
                    "falhou",
                )
            }
            lines.append(
                f"coleta: {len(self.files)} arquivos, {counts['novo']} novos, "
                f"{counts['inalterado']} inalterados, "
                f"{counts['nao modificado']} nao modificados, "
                f"{counts['ausente']} ausentes, {counts['falhou']} falhos"
            )
        return "\n".join(lines)

    def failures(self) -> list[str]:
        """Os arquivos, anos e companhias falhos, para o `error` da coleta."""
        items = [f"{f.kind} {f.year}" for f in self.files if f.status == "falhou"]
        for year in self.years:
            if year.error is not None:
                items.append(f"{year.label} {year.year}")
            items.extend(
                f"{year.label} {year.year} {code}" for code, _ in year.failures
            )
        return items


class DisclosuresImportFailed(Exception):
    """A coleta terminou `failed`. `report` e o relatorio inteiro, para a casca imprimir."""

    def __init__(self, report: DisclosuresReport) -> None:
        super().__init__(", ".join(report.failures()))
        self.report = report


def run_import_disclosures(
    source: CvmSource,
    *,
    full: bool = False,
    reconform: list[int] | None = None,
    now: Callable[[], datetime] = timezone.now,
) -> DisclosuresReport:
    """Uma execucao do `import_disclosures`. `reconform=[]` e "todos os anos"; `None`, a
    coleta normal. `full` e `reconform` juntos levantam `ValueError`, antes de tudo."""
    if full and reconform is not None:
        raise ValueError("full e reconform sao mutuamente exclusivos")
    started_at = now()
    current_year = timezone.localdate(started_at).year  # uma vez por execucao (RF-02)
    run = CollectionRun.objects.create(source=SOURCE, started_at=started_at)
    try:
        report = _run(
            source,
            run,
            full=full,
            reconform=reconform,
            now=now,
            current_year=current_year,
        )
    except BaseException as exc:  # a collection_run nunca fica `running`
        run.status = CollectionRun.Status.FAILED
        run.error = f"interrompida: {type(exc).__name__}: {exc}"
        run.finished_at = now()
        run.save(update_fields=["status", "error", "finished_at"])
        raise
    _close(run, report, now)
    if report.failed:
        raise DisclosuresImportFailed(report)
    return report


def _run(
    source: CvmSource,
    run: CollectionRun,
    *,
    full: bool,
    reconform: list[int] | None,
    now: Callable[[], datetime],
    current_year: int,
) -> DisclosuresReport:
    files: list[FileResult] = []
    changed: set[int] = set()
    new_companies: set[str] = set()
    # A ordem e literal do plano (RF-07b): (b) antes da coleta e de (a).
    if reconform is None:
        new_companies = _catalog() - set(
            Disclosure.objects.values_list("code_cvm", flat=True).distinct()
        )
        for year in range(FIRST_YEAR, current_year + 1):  # ano crescente
            result = _collect(
                source, run, IPE, year, full=full, current_year=current_year
            )
            files.append(result)
            if result.status == "novo":
                changed.add(year)
        years = changed  # sem A+1
    else:
        years = set(reconform) or set(range(FIRST_YEAR, current_year + 1))
    results = [_conform_disclosure_year(run, y, now) for y in sorted(years)]
    if reconform is None and new_companies:
        rest = sorted(set(range(FIRST_YEAR, current_year + 1)) - years)
        results += [
            _conform_disclosure_year(run, y, now, only=new_companies, label="novas")
            for y in rest
        ]
    return DisclosuresReport(files=files, years=results, collected=reconform is None)


def _close(
    run: CollectionRun, report: DisclosuresReport, now: Callable[[], datetime]
) -> None:
    """A copia do `_close` do `importer.py`, que tipa o relatorio como `ImportReport`."""
    run.status = (
        CollectionRun.Status.FAILED if report.failed else CollectionRun.Status.OK
    )
    run.error = ", ".join(report.failures())
    run.finished_at = now()
    run.save(update_fields=["status", "error", "finished_at"])


# Conformacao (RF-03, RF-04, RF-04a, RF-04b, RF-07).


def _conform_disclosure_year(
    run: CollectionRun,
    year: int,
    now: Callable[[], datetime],
    only: set[str] | None = None,
    label: Label = "ano",
) -> DisclosureYearResult:
    """Conforma um ano de zip: as companhias do catalogo presentes no zip e as que ja tem
    linha do ano na `silver`, cada uma no seu `atomic()`.

    Sem versao corrente do zip na `bronze`, o ano sai sem companhias e sem erro. Se a
    leitura levanta, o ano falha inteiro, antes do laco. `only` restringe as companhias (o
    caminho b); `label` e o prefixo das linhas.
    """
    codes = _catalog()
    if only is not None:
        codes &= only
    file_id = _current_versions(kinds=(IPE,)).get((IPE, year))
    if file_id is None:
        return DisclosureYearResult(label, year)
    try:
        read = disclosures_from_zip(_payload(file_id), year, codes)
    except Exception as exc:
        return DisclosureYearResult(label, year, error=_error(exc))

    # Todos os links conformados no ano, de todas as companhias lidas, uma vez, antes do
    # laco: e o que torna a remocao independente da ordem das companhias (RF-04a).
    year_links = frozenset(
        document.link
        for documents in read.by_company.values()
        for document in documents
    )
    in_silver = set(
        Disclosure.objects.filter(year=year, code_cvm__in=codes)
        .values_list("code_cvm", flat=True)
        .distinct()
    )
    companies_to_visit = (
        set(read.by_company) | set(read.conflicts) | in_silver
    ) & codes

    companies = created = updated = removed = 0
    failures: list[tuple[str, str]] = []
    for code in sorted(companies_to_visit):
        try:
            with transaction.atomic():
                counts = _write_company(code, year, read, year_links, run, now)
        except Exception as exc:
            failures.append((code, _error(exc)))
            continue
        companies += 1
        created += counts.created
        updated += counts.updated
        removed += counts.removed
    return DisclosureYearResult(
        label,
        year,
        companies=companies,
        created=created,
        updated=updated,
        removed=removed,
        failures=failures,
        malformed=read.malformed,
    )


def _write_company(
    code: str,
    year: int,
    read: DisclosuresByCompany,
    year_links: frozenset[str],
    run: CollectionRun,
    now: Callable[[], datetime],
) -> DisclosureCounts:
    """Uma companhia de um ano: o conflito do RF-04b e falha dela; senao, a escrita."""
    conflicted = read.conflicts.get(code)
    if conflicted:
        raise ValueError(f"link repetido com campos diferentes: {conflicted[0]}")
    return write_disclosure_company_year(
        code, year, read.by_company.get(code, []), year_links, run, now()
    )


def _values(document: ConformedDisclosure) -> tuple[object, ...]:
    return tuple(getattr(document, name) for name in DISCLOSURE_FIELDS)


def _stored(row: Disclosure) -> tuple[object, ...]:
    return tuple(getattr(row, name) for name in DISCLOSURE_FIELDS)


def write_disclosure_company_year(
    code_cvm: str,
    year: int,
    conformed: list[ConformedDisclosure],
    year_links: frozenset[str],
    run: CollectionRun,
    now: datetime,
) -> DisclosureCounts:
    """A escrita de uma companhia num ano (RF-04, RF-04a).

    Cada documento por `link`: ausente, cria; presente — sob esta ou outra companhia —,
    compara a tupla de `DISCLOSURE_FIELDS` e so grava, com `run` e `updated_at`, quando
    algo muda. Depois remove as linhas da companhia no ano cujo link nao esta em
    `year_links`. A remocao filtra em Python, e nao por `exclude(link__in=year_links)`, que
    passaria milhares de parametros por companhia nos anos cheios; o resultado e o mesmo.
    """
    created = updated = 0
    for document in conformed:
        values = dict(zip(DISCLOSURE_FIELDS, _values(document), strict=True))
        current = Disclosure.objects.filter(link=document.link).first()
        if current is None:
            Disclosure.objects.create(run=run, updated_at=now, **values)
            created += 1
            continue
        if _values(document) == _stored(current):
            continue
        for name, value in values.items():
            setattr(current, name, value)
        current.run = run
        current.updated_at = now
        current.save()
        updated += 1

    stale = [
        pk
        for pk, link in Disclosure.objects.filter(
            code_cvm=code_cvm, year=year
        ).values_list("pk", "link")
        if link not in year_links
    ]
    removed = 0
    if stale:
        removed, _ = Disclosure.objects.filter(pk__in=stale).delete()
    return DisclosureCounts(created=created, updated=updated, removed=removed)
