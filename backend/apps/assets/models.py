"""Catalogo de ativos: tres tabelas cruas na `bronze` e o estado conformado na `silver`.

O esquema vai embutido no `db_table`, com aspas no meio, como no `accounts`: e o contrato
da D-38 — mudar as aspas muda o esquema em que a tabela nasce. A chave primaria nao e
declarada: o `DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

As duas tabelas de payload (`b3_company_listing`, `b3_company_detail`) sao so-acrescimo:
nenhum caminho do codigo faz `update` ou `delete` nelas, e a FK `PROTECT` impede apagar
uma coleta que tenha dado. `collection_run` muda uma vez: de `running` para `ok` ou
`failed`.

O M1.2 acrescentou os precos: a resposta crua do Yahoo (`yahoo_chart`, so-acrescimo, na
`bronze`) e, na `silver`, um pregao por ativo (`price`) e os eventos corporativos
(`corporate_event`).
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


class YahooChart(models.Model):
    """Uma resposta do `chart` v8 do Yahoo, crua — inclusive a de erro (404 com `chart.error`).

    Sem restricao de unicidade: e so-acrescimo, e a rebusca por evento novo e uma segunda
    linha na mesma coleta. `symbol` e o `provider_symbol` pedido, copiado para a linha nao
    depender de o catalogo mudar.
    """

    run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name="yahoo_charts",
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="yahoo_charts",
    )
    symbol = models.CharField(max_length=20)
    period1 = models.BigIntegerField()
    period2 = models.BigIntegerField()
    http_status = models.IntegerField()
    payload = models.JSONField()

    class Meta:
        db_table = 'bronze"."yahoo_chart'

    def __str__(self) -> str:
        return f"{self.symbol} HTTP {self.http_status} (coleta {self.run_id})"


class Price(models.Model):
    """Um pregao por ativo, no fuso da bolsa. Unico em `(asset, date)`.

    `run` e `updated_at` avancam so quando a linha e criada ou algum valor muda — a mesma
    regra do `asset`; `updated_at` nao leva `auto_now`: quem grava escreve o `now()`. Nao ha
    `created_at`: a primeira versao da linha e a coleta em `run`. `log_return` e nulo so no
    primeiro pregao de toda a serie.
    """

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="prices",
    )
    date = models.DateField()
    open = models.DecimalField(max_digits=18, decimal_places=6)
    high = models.DecimalField(max_digits=18, decimal_places=6)
    low = models.DecimalField(max_digits=18, decimal_places=6)
    close = models.DecimalField(max_digits=18, decimal_places=6)
    adj_close = models.DecimalField(max_digits=18, decimal_places=6)
    volume = models.BigIntegerField()
    log_return = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name="prices_written",
    )
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'silver"."price'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(fields=["asset", "date"], name="price_asset_date")
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.date}"


class CorporateEvent(models.Model):
    """Um evento corporativo por ativo, data e tipo: dividendo (`amount`) ou desdobramento
    (`numerator`/`denominator`). Unico em `(asset, date, kind)`.
    """

    class Kind(models.TextChoices):
        DIVIDEND = "dividend"
        SPLIT = "split"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="corporate_events",
    )
    date = models.DateField()
    kind = models.CharField(max_length=10, choices=Kind)
    amount = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    numerator = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    denominator = models.DecimalField(max_digits=10, decimal_places=4, null=True)
    run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name="corporate_events_written",
    )

    class Meta:
        db_table = 'silver"."corporate_event'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["asset", "date", "kind"], name="corporate_event_asset_date_kind"
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.date} {self.kind}"
