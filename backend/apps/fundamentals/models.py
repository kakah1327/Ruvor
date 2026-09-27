"""Fundamentos da CVM: o zip cru na `bronze`, a companhia e o balanco na `silver`, os
indicadores na `gold`.

O esquema vai embutido no `db_table`, com aspas no meio, como em `assets`: e o contrato da
D-38 — mudar as aspas muda o esquema em que a tabela nasce. A chave primaria nao e
declarada: o `default_auto_field` do app e `BigAutoField`.

`cvm_file` e so-acrescimo, sem unicidade (D-16). `company` e `financial_statement` sao o
estado conformado corrente, atualizado por reconformacao (RF-18). `fundamental_indicator` e
imutavel: recalcular insere linha nova, como `gold.behavior_metric` (D-55).

`silver.company` **nao tem FK para `silver.asset`**: a ligacao e por valor,
`company.code_cvm = asset.code_cvm`.
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models


class AccountPlan(models.TextChoices):
    """O plano de contas de um documento, pela descricao da `3.01` da DRE (RF-12)."""

    GENERAL = "general"
    BANK = "bank"
    INSURANCE = "insurance"
    UNKNOWN = "unknown"


class CvmFile(models.Model):
    """Um `GET` a um zip da CVM, cru. `payload` so quando o conteudo e novo (RF-05)."""

    class Kind(models.TextChoices):
        ITR = "itr"
        DFP = "dfp"

    run = models.ForeignKey(
        "assets.CollectionRun",
        on_delete=models.PROTECT,
        related_name="cvm_files",
    )
    kind = models.CharField(max_length=3, choices=Kind)
    year = models.IntegerField()
    url = models.CharField(max_length=200)
    http_status = models.IntegerField()
    last_modified = models.CharField(max_length=40, null=True)
    content_sha256 = models.CharField(max_length=64, null=True)
    payload = models.BinaryField(null=True)

    class Meta:
        db_table = 'bronze"."cvm_file'

    def __str__(self) -> str:
        return f"{self.kind} {self.year} #{self.pk} ({self.http_status})"


class Company(models.Model):
    """Uma linha por `code_cvm` normalizado, sem zeros a esquerda.

    `updated_at` nao leva `auto_now`: quem grava escreve o `now()`. `name` e `account_plan`
    so mudam com documento de `DT_REFER` maior ou igual ao `source_reference_date` (RF-19).
    """

    Plan = AccountPlan

    code_cvm = models.CharField(max_length=20, unique=True)
    cnpj = models.CharField(max_length=14)
    name = models.CharField(max_length=200)
    account_plan = models.CharField(max_length=10, choices=AccountPlan)
    source_reference_date = models.DateField()
    run = models.ForeignKey(
        "assets.CollectionRun",
        on_delete=models.PROTECT,
        related_name="companies_written",
    )
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'silver"."company'

    def __str__(self) -> str:
        return f"{self.code_cvm} {self.name}"


class FinancialStatement(models.Model):
    """Um trimestre do exercicio de uma companhia, larga e tipada (D-56).

    Valores monetarios em reais; balanco e a posicao na data, resultado e o do trimestre
    isolado. `updated_at` nao leva `auto_now` (RF-18).
    """

    Plan = AccountPlan

    class Scope(models.TextChoices):
        CONSOLIDATED = "consolidated"
        INDIVIDUAL = "individual"

    class Source(models.TextChoices):
        ITR = "itr"
        DFP = "dfp"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="statements",
    )
    reference_date = models.DateField()
    fiscal_year_start = models.DateField(null=True)
    source = models.CharField(max_length=3, choices=Source)
    version = models.IntegerField()
    received_date = models.DateField(null=True)
    scope = models.CharField(max_length=12, choices=Scope)
    account_plan = models.CharField(max_length=10, choices=AccountPlan)
    total_assets = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    cash = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    gross_debt = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    equity_parent = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    revenue = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    ebit = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    net_income_parent = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    shares_on = models.BigIntegerField(null=True)
    shares_pn = models.BigIntegerField(null=True)
    shares_scale = models.IntegerField(null=True)
    share_composition = models.BooleanField()
    run = models.ForeignKey(
        "assets.CollectionRun",
        on_delete=models.PROTECT,
        related_name="statements_written",
    )
    updated_at = models.DateTimeField()

    class Meta:
        db_table = 'silver"."financial_statement'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["company", "reference_date"],
                name="financial_statement_company_reference_date",
            )
        ]

    def __str__(self) -> str:
        return f"{self.company_id} {self.reference_date:%Y-%m-%d}"


class FundamentalIndicator(models.Model):
    """Uma linha por `(asset, calculated_at)`: os indicadores daquela execucao. Imutavel.

    `calculated_at` nao leva `auto_now_add`: um `now()` por execucao. `account_plan` e
    `scope` sao copias do `statement`, para a linha se explicar sozinha.
    """

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="fundamental_indicators",
    )
    calculated_at = models.DateTimeField()
    statement = models.ForeignKey(
        FinancialStatement,
        on_delete=models.PROTECT,
        related_name="indicators",
    )
    account_plan = models.CharField(max_length=10, choices=AccountPlan)
    scope = models.CharField(max_length=12, choices=FinancialStatement.Scope)
    revenue_ttm = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    ebit_ttm = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    net_income_ttm = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    equity_parent = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    total_assets = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    gross_debt = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    cash = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    net_debt = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    net_margin = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    ebit_margin = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    roe = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    net_debt_to_equity = models.DecimalField(
        max_digits=18, decimal_places=10, null=True
    )
    price_date = models.DateField(null=True)
    close = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    shares_total = models.BigIntegerField(null=True)
    eps = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    bvps = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    pe = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    pb = models.DecimalField(max_digits=18, decimal_places=6, null=True)
    per_share_missing = models.CharField(max_length=24, null=True)
    market_cap = models.DecimalField(max_digits=22, decimal_places=2, null=True)
    market_cap_missing = models.CharField(max_length=24, null=True)

    class Meta:
        db_table = 'gold"."fundamental_indicator'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["asset", "calculated_at"],
                name="fundamental_indicator_asset_calculated_at",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["asset", "-calculated_at"], name="fund_indicator_asset_recent"
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.calculated_at:%Y-%m-%d %H:%M:%S}"
