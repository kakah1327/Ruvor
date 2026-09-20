"""Catalogo de ativos: tres tabelas cruas na `bronze` e o estado conformado na `silver`.

O esquema vai embutido no `db_table`, com aspas no meio, como no `accounts`: e o contrato
da D-38 — mudar as aspas muda o esquema em que a tabela nasce. A chave primaria nao e
declarada: o `DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

As duas tabelas de payload (`b3_company_listing`, `b3_company_detail`) sao so-acrescimo:
nenhum caminho do codigo faz `update` ou `delete` nelas, e a FK `PROTECT` impede apagar
uma coleta que tenha dado. `collection_run` muda uma vez: de `running` para `ok` ou
`failed`.
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models


class CollectionRun(models.Model):
    """Uma execucao de coleta. E o que da data e hora a tudo o que a `bronze` guarda (D-13)."""

    class Status(models.TextChoices):
        RUNNING = "running"
        OK = "ok"
        FAILED = "failed"

    source = models.CharField(max_length=60)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.RUNNING)
    error = models.TextField(blank=True, default="")

    class Meta:
        db_table = 'bronze"."collection_run'

    def __str__(self) -> str:
        return f"{self.source} #{self.pk} ({self.status})"


class B3CompanyListing(models.Model):
    """Um item da listagem da B3, cru: o payload como veio, sem campo removido ou convertido."""

    run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name="listings",
    )
    code_cvm = models.CharField(max_length=20)
    page_number = models.IntegerField()
    payload = models.JSONField()

    class Meta:
        db_table = 'bronze"."b3_company_listing'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["run", "code_cvm"], name="b3_company_listing_run_code_cvm"
            )
        ]

    def __str__(self) -> str:
        return f"{self.code_cvm} (coleta {self.run_id})"


class B3CompanyDetail(models.Model):
    """Uma resposta de detalhe da B3, crua. `code_cvm` e o pedido, nao o que veio: `{}` nao traz."""

    run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name="details",
    )
    code_cvm = models.CharField(max_length=20)
    payload = models.JSONField()

    class Meta:
        db_table = 'bronze"."b3_company_detail'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["run", "code_cvm"], name="b3_company_detail_run_code_cvm"
            )
        ]

    def __str__(self) -> str:
        return f"{self.code_cvm} (coleta {self.run_id})"


class Asset(models.Model):
    """Uma linha por ticker: o estado conformado corrente. A historia esta na `bronze`.

    `created_at` e `updated_at` nao levam `auto_now_add` nem `auto_now`: o `importer` (e a
    migration do Ibovespa) os escreve com o mesmo `now()`. `updated_at` e a ultima vez que
    uma coluna conformada mudou — `last_seen_run` avanca em toda coleta sem toca-lo.
    """

    class Kind(models.TextChoices):
        STOCK = "stock"
        INDEX = "index"

    class Status(models.TextChoices):
        ACTIVE = "active"
        INACTIVE = "inactive"

    ticker = models.CharField(max_length=12, unique=True)
    kind = models.CharField(max_length=10, choices=Kind)
    isin = models.CharField(max_length=12, null=True)
    name = models.CharField(max_length=200)
    trading_name = models.CharField(max_length=60)
    cnpj = models.CharField(max_length=14, null=True)
    code_cvm = models.CharField(max_length=20, null=True)
    issuer_code = models.CharField(max_length=10, null=True)
    sector = models.CharField(max_length=120, null=True)
    subsector = models.CharField(max_length=120, null=True)
    segment = models.CharField(max_length=120, null=True)
    listing_segment = models.CharField(max_length=4, null=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.ACTIVE)
    provider_symbol = models.CharField(max_length=20)
    first_seen_run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name="first_seen_assets",
        null=True,
    )
    last_seen_run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name="last_seen_assets",
        null=True,
    )
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'silver"."asset'

    def __str__(self) -> str:
        return self.ticker
