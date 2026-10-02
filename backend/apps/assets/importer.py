"""A coleta: listagem e detalhes para a `bronze`, depois a conformacao para a `silver`.

A sequencia e contrato da spec ("O comando"), porque o RF-10 depende dela: primeiro toda a
listagem, depois todo detalhe, e **so entao**, dentro de uma transacao, a conformacao e o
`ok` da `collection_run`. Falha em qualquer passo marca a coleta como `failed` fora da
transacao revertida — e por isso que a linha `failed` sobrevive — e levanta
`CollectionFailed`. A `bronze` fica com o que foi coletado ate a falha; a `silver` nunca
fica meio conformada.

`conform_company` e importada pelo nome, e nao pelo modulo, de proposito: e o ponto que o
teste do RF-02 substitui com `monkeypatch.setattr("apps.assets.importer.conform_company", ...)`.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol

from django.db import transaction
from django.utils import timezone

from apps.assets.b3 import Page
from apps.assets.classification import unknown_dotted
from apps.assets.conform import ConformedAsset, conform_company, is_company
from apps.assets.models import Asset, B3CompanyDetail, B3CompanyListing, CollectionRun

SOURCE = "b3-listed-companies"

# As colunas de `silver.asset` que a conformacao produz. Mudanca em qualquer uma delas e o
# que escreve `updated_at`; `last_seen_run` avanca sem toca-lo. `status` fica de fora: e
# tratado a parte, e conta em `reactivated`/`inactivated`, nunca em `updated`.
CONFORMED_FIELDS: tuple[str, ...] = (
    "isin",
    "name",
    "trading_name",
    "cnpj",
    "code_cvm",
    "issuer_code",
    "sector",
    "subsector",
    "segment",
    "listing_segment",
    "provider_symbol",
)


class CompanySource(Protocol):
    """O que o `importer` pede da fonte. `B3Client` satisfaz; a `FakeSource` dos testes tambem."""

    def list_companies(self) -> Iterator[Page]: ...

    def get_company(self, code_cvm: str) -> dict[str, Any]: ...


class CollectionFailed(Exception):
    """A coleta terminou `failed`. A mensagem e a que ficou em `collection_run.error`."""


@dataclass(frozen=True)
class Listing:
    """A listagem inteira, como veio, e em quantas paginas. E o `listed` do `run_import`.

    Carrega `pages` porque `_conform` monta o relatorio e recebe so `listed`.
    """

    items: list[dict[str, Any]]
    pages: int


@dataclass(frozen=True)
class ImportReport:
    """As contagens de uma coleta que terminou `ok` (RF-13).

    `dotted_outside_table` sao os textos de classificacao com ponto fora das duas listas da
    D-144 (M1.7, RF-09), distintos e em ordem alfabetica: o sinal para a tabela ganhar uma
    linha. Nao reprova a coleta. Tem padrao para as construcoes que nao o passam.
    """

    listed: int
    pages: int
    consulted: int
    conformed: int
    created: int
    updated: int
    inactivated: int
    reactivated: int
    empty_details: int
    quoted_without_code: int
    odd_classifications: int
    dotted_outside_table: tuple[str, ...] = ()

    def render(self) -> str:
        lines = [
            f"listagem: {self.listed} companhias em {self.pages} paginas",
            f"consultadas (type=1): {self.consulted}",
            (
                f"acoes conformadas: {self.conformed} (criadas {self.created}, "
                f"alteradas {self.updated}, inativadas {self.inactivated}, "
                f"reativadas {self.reactivated})"
            ),
            (
                f"casos de borda: detalhe vazio {self.empty_details}, "
                f"hasQuotation=S sem codigo de acao {self.quoted_without_code}, "
                f"classificacao fora de tres partes {self.odd_classifications}"
            ),
            (
                "classificacao com ponto fora da tabela: "
                f"{len(self.dotted_outside_table)}"
            ),
        ]
        if self.dotted_outside_table:
            lines.append(f"  {'; '.join(self.dotted_outside_table)}")
        return "\n".join(lines)


def run_import(source: CompanySource) -> ImportReport:
    run = CollectionRun.objects.create(source=SOURCE, started_at=timezone.now())
    try:
        listed = _collect_listing(run, source)  # bulk_create por pagina
        details = _collect_details(
            run, source, listed
        )  # so type == "1"; grava {} tambem
        with transaction.atomic():
            report = _conform(run, listed, details)  # levanta CollectionFailed no RF-16
            run.status = CollectionRun.Status.OK
            run.finished_at = timezone.now()
            run.save(update_fields=["status", "finished_at"])
        return report
    except Exception as exc:
        # fora de qualquer transacao revertida: e por isso que o `failed` sobrevive
        run.status = CollectionRun.Status.FAILED
        run.error = (
            f"{type(exc).__name__}: {exc}"  # o nome da classe e diagnostico na bronze
        )
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error", "finished_at"])
        if isinstance(exc, CollectionFailed):  # o RF-16 ja levantou a certa
            raise
        raise CollectionFailed(run.error) from exc


def _collect_listing(run: CollectionRun, source: CompanySource) -> Listing:
    """Grava cada item da listagem como veio, uma pagina por `bulk_create`."""
    items: list[dict[str, Any]] = []
    pages = 0
    for page in source.list_companies():
        pages += 1
        B3CompanyListing.objects.bulk_create(
            [
                B3CompanyListing(
                    run=run,
                    code_cvm=str(item["codeCVM"]),
                    page_number=page.page_number,
                    payload=item,
                )
                for item in page.items
            ]
        )
        items.extend(page.items)
    return Listing(items=items, pages=pages)


def _collect_details(
    run: CollectionRun, source: CompanySource, listed: Listing
) -> dict[str, dict[str, Any]]:
    """Consulta e grava o detalhe de cada companhia `type == "1"`, na ordem da listagem.

    A resposta vai para a `bronze` como veio, `{}` incluido. `code_cvm` e o pedido, nao o
    que veio — `{}` nao traz.
    """
    details: dict[str, dict[str, Any]] = {}
    for item in listed.items:
        if not is_company(item):
            continue
        code_cvm = str(item["codeCVM"])
        detail = source.get_company(code_cvm)
        B3CompanyDetail.objects.create(run=run, code_cvm=code_cvm, payload=detail)
        details[code_cvm] = detail
    return details


def _conform(
    run: CollectionRun,
    listed: Listing,
    details: dict[str, dict[str, Any]],
) -> ImportReport:
    """O *upsert* da `silver.asset`: cria, altera, inativa, reativa. Nunca apaga.

    Linhas `kind=index` nao sao lidas nem escritas (RF-12).
    """
    now = timezone.now()

    empty_details = 0
    quoted_without_code = 0
    odd_classifications = 0
    conformed: dict[str, ConformedAsset] = {}
    for item in listed.items:
        if not is_company(item):
            continue
        company = conform_company(item, details[str(item["codeCVM"])])
        empty_details += int(company.empty_detail)
        quoted_without_code += int(company.quoted_without_code)
        odd_classifications += int(company.odd_classification)
        for asset in company.assets:
            previous = conformed.get(asset.ticker)
            if previous is not None:
                # RF-16: inconsistencia da fonte. Detectada antes de qualquer escrita.
                raise CollectionFailed(
                    f"codigo {asset.ticker} aparece em duas companhias: "
                    f"codeCVM {previous.code_cvm} e codeCVM {asset.code_cvm}"
                )
            conformed[asset.ticker] = asset

    existing = {
        asset.ticker: asset for asset in Asset.objects.filter(kind=Asset.Kind.STOCK)
    }

    created = updated = reactivated = inactivated = 0
    for ticker, incoming in conformed.items():
        current = existing.get(ticker)
        if current is None:
            Asset.objects.create(
                ticker=ticker,
                kind=Asset.Kind.STOCK,
                status=Asset.Status.ACTIVE,
                first_seen_run=run,
                last_seen_run=run,
                created_at=now,
                updated_at=now,
                **{field: getattr(incoming, field) for field in CONFORMED_FIELDS},
            )
            created += 1
            continue

        changed = False
        for field in CONFORMED_FIELDS:
            value = getattr(incoming, field)
            if getattr(current, field) != value:
                setattr(current, field, value)
                changed = True
        reactivating = current.status == Asset.Status.INACTIVE
        if reactivating:
            current.status = Asset.Status.ACTIVE
        if changed or reactivating:
            current.updated_at = now
        current.last_seen_run = run  # sempre; e so isso nao toca em updated_at
        current.save()
        if reactivating:
            reactivated += 1
        elif changed:
            updated += 1

    for ticker, current in existing.items():
        if ticker in conformed or current.status != Asset.Status.ACTIVE:
            continue
        current.status = Asset.Status.INACTIVE
        current.updated_at = now  # last_seen_run fica na ultima coleta em que apareceu
        current.save(update_fields=["status", "updated_at"])
        inactivated += 1

    return ImportReport(
        listed=len(listed.items),
        pages=listed.pages,
        consulted=len(details),
        conformed=len(conformed),
        created=created,
        updated=updated,
        inactivated=inactivated,
        reactivated=reactivated,
        empty_details=empty_details,
        quoted_without_code=quoted_without_code,
        odd_classifications=odd_classifications,
        dotted_outside_table=tuple(
            unknown_dotted(
                text
                for asset in conformed.values()
                for text in (asset.sector, asset.subsector, asset.segment)
            )
        ),
    )
