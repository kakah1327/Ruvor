"""A coleta de fundamentos: os zips da CVM para a `bronze` e, por (companhia, ano), em
transacao, as companhias e os balancos para a `silver`.

A ordem e contrato do plano (T5): as companhias novas do catalogo sao calculadas **antes**
da coleta e da conformacao dos anos alterados (RF-17 a), e o caminho (b) so conforma para
elas os anos que (a) nao conformou. Cada (tipo, ano) e coletado por `_collect`, que nunca
levanta por falha de rede ou zip ruim (RF-04, RF-05); cada ano e conformado por
`_conform_year`, que le cada zip do ano uma vez e grava companhia por companhia, cada uma no
seu `atomic()` (RF-16).

`write_company_year` e chamada pelo nome global, de proposito: e o ponto que o teste do
RF-16 substitui com `monkeypatch.setattr("apps.fundamentals.importer.write_company_year",
...)`, no molde de `write_conformed` em `apps/assets/prices.py`.
"""

from __future__ import annotations

import zipfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol, cast

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.assets.models import Asset, CollectionRun
from apps.fundamentals.conform import (
    ConformedStatement,
    conform_year,
    itr_superseded_by_dfp,
)
from apps.fundamentals.cvm import KINDS, CvmClientError, CvmDownload, CvmHead
from apps.fundamentals.documents import (
    DocumentsByCompany,
    documents_from_zip,
    normalize_code,
)
from apps.fundamentals.models import AccountPlan, Company, CvmFile, FinancialStatement
from apps.fundamentals.zipdata import content_sha256, read_rows

SOURCE = "cvm-dados-abertos"
FIRST_YEAR = 2016  # RF-03: o intervalo vai de 2016 ao ano corrente
Q2 = Decimal("0.01")  # as casas de `DecimalField(22, 2)`

Kind = Literal["itr", "dfp"]
FileStatus = Literal["novo", "inalterado", "nao modificado", "ausente", "falhou"]
Label = Literal["ano", "novas"]

# As colunas de `silver.financial_statement` que vem da conformacao, na ordem da tupla
# comparada (RF-18). `company`, `run` e `updated_at` sao da escrita.
STATEMENT_FIELDS = (
    "fiscal_year_start",
    "source",
    "version",
    "received_date",
    "scope",
    "account_plan",
    "total_assets",
    "cash",
    "gross_debt",
    "equity_parent",
    "revenue",
    "ebit",
    "net_income_parent",
    "shares_on",
    "shares_pn",
    "shares_scale",
    "share_composition",
)
MONEY_FIELDS = frozenset(
    (
        "total_assets",
        "cash",
        "gross_debt",
        "equity_parent",
        "revenue",
        "ebit",
        "net_income_parent",
    )
)


class CvmSource(Protocol):
    """O que a coleta pede da fonte. `CvmClient` satisfaz; a `FakeCvm` dos testes tambem."""

    def head(self, kind: str, year: int) -> CvmHead: ...

    def get(self, kind: str, year: int) -> CvmDownload: ...


class UnexpectedStatus(Exception):
    """Resposta da CVM com status que nao e 200 nem o 404 do ano corrente (RF-04)."""


@dataclass(frozen=True)
class FileResult:
    """Uma linha de arquivo do relatorio: o que aconteceu com um (tipo, ano)."""

    kind: str
    year: int
    status: FileStatus
    size: int | None = None
    error: str | None = None

    def render(self) -> str:
        prefix = f"{self.kind} {self.year}"
        if self.status in ("novo", "inalterado"):
            return f"{prefix}: baixado, {self.size} bytes, {self.status}"
        if self.status == "falhou":
            return f"{prefix}: FALHOU ({self.error})"
        return f"{prefix}: {self.status}"


@dataclass(frozen=True)
class YearCounts:
    """O que `write_company_year` escreveu para uma companhia num ano."""

    created: int
    updated: int
    missing: int  # campos nulos pela regra do RF-08, somados nos documentos
    unknown_plan: int  # documentos de plano `unknown` (RF-12)


@dataclass(frozen=True)
class YearResult:
    """As linhas de um ano no relatorio: o resumo, os descartes e as companhias falhas.

    `error` e a falha no nivel do ano — a leitura dos zips levantou antes do laco de
    companhias —, e entao o ano nao conformou nada.
    """

    label: Label
    year: int
    companies: int = 0
    created: int = 0
    updated: int = 0
    missing: int = 0
    unknown_plan: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)
    malformed: dict[str, int] = field(default_factory=dict)
    # `code_cvm` de cada ITR descartado por DFP na mesma data (RF-13b), um por ITR
    superseded: list[str] = field(default_factory=list)
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
            f"{self.updated} atualizados, {self.missing} ausentes, "
            f"{self.unknown_plan} plano desconhecido, {len(self.failures)} falhos"
        ]
        if self.malformed:
            members = ", ".join(
                f"{member}: {count}" for member, count in sorted(self.malformed.items())
            )
            lines.append(
                f"{prefix}: {sum(self.malformed.values())} registros mal formados "
                f"descartados ({members})"
            )
        if self.superseded:
            codes = ", ".join(sorted(set(self.superseded), key=int))
            lines.append(
                f"{prefix}: {len(self.superseded)} itr descartados por dfp na mesma "
                f"data ({codes})"
            )
        lines.extend(
            f"{prefix}: FALHOU {code} ({error})" for code, error in self.failures
        )
        return lines


@dataclass(frozen=True)
class ImportReport:
    """O relatorio de uma execucao (RF-27).

    Com `--reconform` (`collected` falso) nao houve coleta nem busca de novas: as linhas
    de arquivo, `catalogo:` e `coleta:` nao sao impressas.
    """

    files: list[FileResult]
    years: list[YearResult]
    collected: bool
    new_companies: int = 0
    without_documents: int = 0
    # (onde, erro): o (tipo, ano) cujo indice nao se leu, e a excecao
    catalog_failures: list[tuple[str, str]] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return (
            any(f.status == "falhou" for f in self.files)
            or any(y.failed for y in self.years)
            or bool(self.catalog_failures)
        )

    def render(self) -> str:
        lines = [f.render() for f in self.files] if self.collected else []
        for year in self.years:
            lines.extend(year.render())
        if self.collected:
            lines.extend(
                f"catalogo: FALHOU {where} ({error})"
                for where, error in self.catalog_failures
            )
            lines.append(
                f"catalogo: {self.new_companies} companhias novas, "
                f"{self.without_documents} sem documento na cvm"
            )
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
        """Os arquivos, anos, companhias e indices falhos, para o `error` da coleta."""
        items = [f"{f.kind} {f.year}" for f in self.files if f.status == "falhou"]
        for year in self.years:
            if year.error is not None:
                items.append(f"{year.label} {year.year}")
            items.extend(
                f"{year.label} {year.year} {code}" for code, _ in year.failures
            )
        items.extend(f"catalogo {where}" for where, _ in self.catalog_failures)
        return items


class FundamentalsImportFailed(Exception):
    """A coleta terminou `failed`. `report` e o relatorio inteiro, para a casca imprimir."""

    def __init__(self, report: ImportReport) -> None:
        super().__init__(", ".join(report.failures()))
        self.report = report


def run_import_fundamentals(
    source: CvmSource,
    *,
    full: bool = False,
    reconform: list[int] | None = None,
    now: Callable[[], datetime] = timezone.now,
) -> ImportReport:
    """Uma execucao do `import_fundamentals`. `reconform=[]` e "todos os anos"; `None`, a
    coleta normal. `full` e `reconform` juntos levantam `ValueError`, antes de tudo."""
    if full and reconform is not None:
        raise ValueError("full e reconform sao mutuamente exclusivos")
    run = CollectionRun.objects.create(source=SOURCE, started_at=now())
    try:
        report = _run(source, run, full=full, reconform=reconform, now=now)
    except BaseException as exc:  # a collection_run nunca fica `running`
        run.status = CollectionRun.Status.FAILED
        run.error = f"interrompida: {type(exc).__name__}: {exc}"
        run.finished_at = now()
        run.save(update_fields=["status", "error", "finished_at"])
        raise
    _close(run, report, now)
    if report.failed:
        raise FundamentalsImportFailed(report)
    return report


def _run(
    source: CvmSource,
    run: CollectionRun,
    *,
    full: bool,
    reconform: list[int] | None,
    now: Callable[[], datetime],
) -> ImportReport:
    files: list[FileResult] = []
    changed_years: set[int] = set()
    new_companies: set[str] = set()
    catalog_failures: dict[tuple[str, int], str] = {}
    index_cache: dict[int, set[str]] = {}
    if reconform is None:
        # RF-17 (b): ANTES de (a), sem `Company` no inicio, pela `bronze` anterior a coleta
        new_companies = _new_catalog_companies(run, index_cache, catalog_failures)
        for kind, year in _range(now):  # RF-03: por ano crescente, itr antes de dfp
            result = _collect(source, run, kind, year, full=full, now=now)
            files.append(result)
            if result.status == "novo":
                changed_years.add(year)
        years = _years_to_conform(changed_years, now)  # RF-17 (a): A e A+1
    else:
        years = set(reconform) or set(_all_years(now))
    year_results = [_conform_year(run, y, now) for y in sorted(years)]
    if reconform is None and new_companies:
        rest = sorted(set(_all_years(now)) - years)  # so os anos que (a) nao conformou
        year_results += [
            _conform_year(run, y, now, only=new_companies, label="novas") for y in rest
        ]
    without_documents = 0
    if reconform is None:
        without_documents = _without_documents(index_cache, catalog_failures)
    return ImportReport(
        files=files,
        years=year_results,
        collected=reconform is None,
        new_companies=len(new_companies),
        without_documents=without_documents,
        catalog_failures=[
            (f"{kind} {year}", error)
            for (kind, year), error in sorted(catalog_failures.items())
        ],
    )


def _close(
    run: CollectionRun, report: ImportReport, now: Callable[[], datetime]
) -> None:
    run.status = (
        CollectionRun.Status.FAILED if report.failed else CollectionRun.Status.OK
    )
    run.error = ", ".join(report.failures())
    run.finished_at = now()
    run.save(update_fields=["status", "error", "finished_at"])


def _current_year(now: Callable[[], datetime]) -> int:
    return timezone.localdate(now()).year


def _all_years(now: Callable[[], datetime]) -> range:
    return range(FIRST_YEAR, _current_year(now) + 1)


def _range(now: Callable[[], datetime]) -> list[tuple[Kind, int]]:
    """RF-03: ITR e DFP de 2016 ao ano corrente, por ano crescente, `itr` antes de `dfp`."""
    return [(cast("Kind", kind), year) for year in _all_years(now) for kind in KINDS]


def _years_to_conform(changed: set[int], now: Callable[[], datetime]) -> set[int]:
    """RF-17 (a): cada ano com `payload` novo e o seguinte, dentro do intervalo."""
    valid = set(_all_years(now))
    return {y for year in changed for y in (year, year + 1)} & valid


def _error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


# Coleta (RF-04, RF-05).


def _collect(
    source: CvmSource,
    run: CollectionRun,
    kind: Kind,
    year: int,
    *,
    full: bool,
    now: Callable[[], datetime],
) -> FileResult:
    """`HEAD`, decisao pelo ultimo visto, `GET`, hash e a linha na `bronze`.

    Captura so `CvmClientError` e `BadZipFile` — nunca `Exception`: um `AssertionError`
    da fonte falsa tem de estourar o teste, nao virar `FALHOU`.
    """
    current_year = _current_year(now)
    try:
        head = source.head(kind, year)
        if head.http_status == 404 and year == current_year:
            return FileResult(kind, year, "ausente")
        if head.http_status != 200:
            return _unexpected(kind, year, f"HEAD devolveu {head.http_status}")
        if not full and _is_last_seen(kind, year, head.last_modified):
            return FileResult(kind, year, "nao modificado")
        download = source.get(kind, year)
        if download.http_status != 200:
            _store(run, kind, year, download, None, None)
            if download.http_status == 404 and year == current_year:
                return FileResult(kind, year, "ausente")
            return _unexpected(kind, year, f"GET devolveu {download.http_status}")
        payload = download.payload or b""
        try:
            digest = content_sha256(payload)
        except zipfile.BadZipFile:
            _store(run, kind, year, download, None, None)
            raise
        if digest == _current_digest(kind, year):
            _store(run, kind, year, download, digest, None)
            return FileResult(kind, year, "inalterado", size=len(payload))
        _store(run, kind, year, download, digest, payload)
        return FileResult(kind, year, "novo", size=len(payload))
    except (CvmClientError, zipfile.BadZipFile) as exc:
        return FileResult(kind, year, "falhou", error=_error(exc))


def _unexpected(kind: str, year: int, message: str) -> FileResult:
    return FileResult(kind, year, "falhou", error=_error(UnexpectedStatus(message)))


def _is_last_seen(kind: str, year: int, last_modified: str | None) -> bool:
    """O `Last-Modified` e o do ultimo visto: maior `id` com 200 e `content_sha256`.

    Nulo nunca e igual; sem ultimo visto, nunca e (RF-04).
    """
    if last_modified is None:
        return False
    seen = (
        CvmFile.objects.filter(
            kind=kind, year=year, http_status=200, content_sha256__isnull=False
        )
        .order_by("-id")
        .values_list("last_modified", flat=True)
        .first()
    )
    return seen == last_modified


def _current_digest(kind: str, year: int) -> str | None:
    """O `content_sha256` da versao corrente: maior `id` com `payload` (RF-05)."""
    return (
        CvmFile.objects.filter(kind=kind, year=year, payload__isnull=False)
        .order_by("-id")
        .values_list("content_sha256", flat=True)
        .first()
    )


def _store(
    run: CollectionRun,
    kind: str,
    year: int,
    download: CvmDownload,
    digest: str | None,
    payload: bytes | None,
) -> None:
    CvmFile.objects.create(
        run=run,
        kind=kind,
        year=year,
        url=download.url,
        http_status=download.http_status,
        last_modified=download.last_modified,
        content_sha256=digest,
        payload=payload,
    )


# Versoes correntes, indices e o catalogo (RF-07, RF-17 b).


def _current_versions(
    exclude_run: CollectionRun | None = None,
) -> dict[tuple[str, int], int]:
    """(tipo, ano) → `id` da versao corrente, sem carregar o `payload`."""
    rows = CvmFile.objects.filter(payload__isnull=False)
    if exclude_run is not None:
        rows = rows.exclude(run=exclude_run)
    return {
        (row["kind"], row["year"]): row["current"]
        for row in rows.values("kind", "year").annotate(current=Max("id"))
    }


def _payload(file_id: int) -> bytes:
    value = CvmFile.objects.filter(pk=file_id).values_list("payload", flat=True).get()
    assert value is not None, f"cvm_file {file_id}: versao corrente sem payload"
    return bytes(value)


def _catalog() -> set[str]:
    """Os `code_cvm` do catalogo: `silver.asset` de `kind = stock` (RF-07)."""
    codes = Asset.objects.filter(kind=Asset.Kind.STOCK).values_list(
        "code_cvm", flat=True
    )
    return {code for code in codes if code}


def _pending() -> set[str]:
    """Os codigos do catalogo ainda sem `silver.company`."""
    return _catalog() - set(Company.objects.values_list("code_cvm", flat=True))


def _index_codes(payload: bytes, kind: str, year: int) -> set[str]:
    """Os `CD_CVM` normalizados do indice do zip, pelo nome exato do membro.

    Registro com numero de campos diferente do cabecalho e pulado, como em
    `documents.py`; o resto que levantar (zip ruim, membro ausente, CSV quebrado) atravessa.
    """
    codes: set[str] = set()
    for row in read_rows(payload, f"{kind}_cia_aberta_{year}.csv"):
        loose = cast("Mapping[object, object]", row)
        if None in loose or None in loose.values():
            continue
        codes.add(normalize_code(row["CD_CVM"]))
    return codes


def _indices(
    versions: Mapping[tuple[str, int], int],
    cache: dict[int, set[str]],
    failures: dict[tuple[str, int], str],
) -> Iterable[set[str]]:
    """Os codigos do indice de cada versao em `versions`, lidos uma vez por `id`.

    Falha ao ler um indice **nunca levanta**: aquele (tipo, ano) fica de fora e vai para
    `failures`.
    """
    for (kind, year), file_id in sorted(versions.items()):
        if file_id not in cache:
            try:
                cache[file_id] = _index_codes(_payload(file_id), kind, year)
            except Exception as exc:
                failures.setdefault((kind, year), _error(exc))
                continue
        yield cache[file_id]


def _new_catalog_companies(
    run: CollectionRun,
    cache: dict[int, set[str]],
    failures: dict[tuple[str, int], str],
) -> set[str]:
    """RF-17 (b): os codigos do catalogo sem `Company` no inicio da execucao e presentes no
    indice de alguma versao corrente **ja na `bronze`**, antes da coleta desta execucao.

    Le so o membro do indice de cada versao corrente. Sem codigo pendente, nao le nada.
    """
    pending = _pending()
    if not pending:
        return set()
    found: set[str] = set()
    for codes in _indices(_current_versions(exclude_run=run), cache, failures):
        found |= codes & pending
    return found


def _without_documents(
    cache: dict[int, set[str]], failures: dict[tuple[str, int], str]
) -> int:
    """`sem documento na cvm`, depois da coleta e das conformacoes: os codigos do catalogo
    ainda sem `Company` e ausentes de todo indice das versoes correntes."""
    pending = _pending()
    if not pending:
        return 0
    for codes in _indices(_current_versions(), cache, failures):
        pending -= codes
    return len(pending)


# Conformacao (RF-07, RF-16 a RF-19).


def _read_documents(
    kind: Kind, year: int, codes: set[str], malformed: dict[str, int]
) -> DocumentsByCompany:
    """Os documentos da versao corrente de (`kind`, `year`), ou vazio se nao ha."""
    file_id = _current_versions().get((kind, year))
    if file_id is None or not codes:
        return DocumentsByCompany()
    documents = documents_from_zip(_payload(file_id), kind, codes)
    for member, count in documents.malformed.items():
        malformed[member] = malformed.get(member, 0) + count
    return documents


def _conform_year(
    run: CollectionRun,
    year: int,
    now: Callable[[], datetime],
    only: set[str] | None = None,
    label: Label = "ano",
) -> YearResult:
    """Conforma um ano de zip: cada companhia do catalogo presente em algum dos tres
    indices (ITR e DFP do ano, ITR do ano anterior), cada uma no seu `atomic()`.

    Cada zip e lido uma vez. Se a leitura levanta, o ano falha inteiro, antes do laco.
    `only` restringe as companhias (o caminho b); `label` e o prefixo das linhas.
    """
    codes = _catalog()
    if only is not None:
        codes &= only
    malformed: dict[str, int] = {}
    try:
        itr = _read_documents("itr", year, codes, malformed)
        dfp = _read_documents("dfp", year, codes, malformed)
        itr_prev = _read_documents("itr", year - 1, codes, malformed)
    except Exception as exc:
        return YearResult(label, year, error=_error(exc))

    companies = created = updated = missing = unknown_plan = 0
    failures: list[tuple[str, str]] = []
    superseded: list[str] = []
    for code in sorted(set(itr) | set(dfp) | set(itr_prev)):
        superseded.extend(
            code
            for reference in itr_superseded_by_dfp(itr.get(code, []), dfp.get(code, []))
            if reference.year == year
        )
        try:
            conformed = [
                statement
                for statement in conform_year(
                    itr.get(code, []), dfp.get(code, []), itr_prev.get(code, [])
                )
                if statement.reference_date.year == year
            ]
            if not conformed:  # so no ITR do ano anterior: nao e desta companhia no ano
                continue
            with transaction.atomic():
                counts = write_company_year(code, year, conformed, run, now())
        except Exception as exc:
            failures.append((code, _error(exc)))
            continue
        companies += 1
        created += counts.created
        updated += counts.updated
        missing += counts.missing
        unknown_plan += counts.unknown_plan
    return YearResult(
        label,
        year,
        companies=companies,
        created=created,
        updated=updated,
        missing=missing,
        unknown_plan=unknown_plan,
        failures=failures,
        malformed=malformed,
        superseded=superseded,
    )


def _quantized(statement: ConformedStatement) -> tuple[object, ...]:
    values: list[object] = []
    for name in STATEMENT_FIELDS:
        value = getattr(statement, name)
        if name in MONEY_FIELDS and value is not None:
            value = Decimal(value).quantize(Q2)
        values.append(value)
    return tuple(values)


def _stored(row: FinancialStatement) -> tuple[object, ...]:
    return tuple(getattr(row, name) for name in STATEMENT_FIELDS)


def write_company_year(
    code_cvm: str,
    year: int,
    conformed: list[ConformedStatement],
    run: CollectionRun,
    now: datetime,
) -> YearCounts:
    """A escrita de uma companhia num ano: `silver.company` e as linhas do ano (RF-16).

    `Company` sem `update_or_create`: `cnpj`, `name`, `account_plan` e
    `source_reference_date` so mudam a partir de documento com `DT_REFER` maior ou igual
    ao `source_reference_date` gravado (RF-19), e so gravam — com `run` e `updated_at` —
    quando algum muda. `FinancialStatement` pela tupla quantizada (RF-18): linha sem
    mudanca nao avanca `run` nem `updated_at`. O molde de `write_conformed` do M1.2.
    """
    assert conformed, f"{code_cvm} {year}: nada a gravar"
    latest = max(conformed, key=lambda statement: statement.reference_date)
    incoming = (
        latest.cnpj,
        latest.name,
        latest.account_plan,
        latest.reference_date,
    )
    company = Company.objects.filter(code_cvm=code_cvm).first()
    if company is None:
        company = Company.objects.create(
            code_cvm=code_cvm,
            cnpj=latest.cnpj,
            name=latest.name,
            account_plan=latest.account_plan,
            source_reference_date=latest.reference_date,
            run=run,
            updated_at=now,
        )
    elif latest.reference_date >= company.source_reference_date:
        stored = (
            company.cnpj,
            company.name,
            company.account_plan,
            company.source_reference_date,
        )
        if incoming != stored:
            (
                company.cnpj,
                company.name,
                company.account_plan,
                company.source_reference_date,
            ) = incoming
            company.run = run
            company.updated_at = now
            company.save()

    created = updated = 0
    existing = {
        row.reference_date: row
        for row in FinancialStatement.objects.filter(
            company=company,
            reference_date__in=[s.reference_date for s in conformed],
        )
    }
    for statement in conformed:
        values = dict(zip(STATEMENT_FIELDS, _quantized(statement), strict=True))
        current = existing.get(statement.reference_date)
        if current is None:
            FinancialStatement.objects.create(
                company=company,
                reference_date=statement.reference_date,
                run=run,
                updated_at=now,
                **values,
            )
            created += 1
            continue
        if _quantized(statement) == _stored(current):
            continue
        for name, value in values.items():
            setattr(current, name, value)
        current.run = run
        current.updated_at = now
        current.save()
        updated += 1

    return YearCounts(
        created=created,
        updated=updated,
        missing=sum(len(statement.missing) for statement in conformed),
        unknown_plan=sum(
            1
            for statement in conformed
            if statement.account_plan == AccountPlan.UNKNOWN
        ),
    )
