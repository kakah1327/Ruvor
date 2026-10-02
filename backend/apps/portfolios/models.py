"""A carteira (M2.2a): a composicao em `core` e o risco dela em `gold` (RF-01 a RF-05, RF-18).

O esquema vai embutido no `db_table`, com aspas no meio, o contrato da D-38: as de `core` no
molde de `core.report`, as de `gold` no de `gold.risk_run`. A chave primaria nao e declarada: o
`DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

**As cinco sao privadas** (RF-18, D-112): o gerente padrao, `objects`, filtra pela organizacao
do contexto pelo `organization_field` de cada uma e levanta sem ela; o gerente base, `unscoped`,
sem escopo, e o que o Django usa no `refresh_from_db`, na insercao e na coleta da exclusao.

**Versao e posicao so crescem** (RF-03, D-114), em duas camadas, o molde de `core.report`: no
Django, o `save` de linha existente, o `delete` da instancia e as escritas em massa dos dois
gerentes levantam; no banco, os gatilhos `portfolio_version_so_cresce` e
`portfolio_holding_so_cresce` da migration `0001_portfolio` recusam `UPDATE` e `DELETE`. O
`TRUNCATE` passa -- e como o `banco_limpo` limpa a suite.

**Este modulo nao importa o motor**: de `apps.risk`, so a classe `RiskRun.Status`, de um modulo
que tambem nao o importa.
"""

from __future__ import annotations

import uuid
from typing import Any, ClassVar

from django.conf import settings
from django.db import models

from apps.accounts.tenancy import OrganizationScopedManager
from apps.risk.models import RiskRun


class Portfolio(models.Model):
    """Uma carteira da organizacao (RF-01). A unica das cinco com campo de dominio que muda:
    `name`, `notional`, `updated_at` e `archived_at`.

    `public_id` e o identificador da API; o `id` nunca sai. `created_at` e `updated_at` nao
    levam `auto_now`: quem grava escreve o instante, como nas outras tabelas de dado.
    """

    organization_field = "organization_id"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True)
    organization = models.ForeignKey(
        "accounts.Organization", on_delete=models.PROTECT, related_name="+"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    name = models.CharField(max_length=100)
    notional = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    archived_at = models.DateTimeField(null=True)

    objects = OrganizationScopedManager[
        "Portfolio"
    ]()  # o primeiro declarado: o gerente padrao
    unscoped = models.Manager["Portfolio"]()

    class Meta:
        db_table = 'core"."portfolio'
        base_manager_name = "unscoped"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["organization", "created_at"], name="portfolio_org_created"
            )
        ]

    def __str__(self) -> str:
        return str(self.public_id)


class PortfolioVersionQuerySet(models.QuerySet["PortfolioVersion"]):
    """Recusa as escritas em massa: a versao so cresce (RF-03)."""

    def update(self, **kwargs: Any) -> int:
        raise TypeError("portfolio_version so cresce")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise TypeError("portfolio_version so cresce")


class VersionManager(OrganizationScopedManager["PortfolioVersion"]):
    """O gerente padrao da versao: o escopo e, pelo `_queryset_class`, o queryset que recusa
    escrita em massa -- o molde de `ReportManager`."""

    _queryset_class = PortfolioVersionQuerySet


class VersionBaseManager(models.Manager["PortfolioVersion"]):
    """O gerente base da versao, sem escopo, com o mesmo queryset que recusa escrita."""

    _queryset_class = PortfolioVersionQuerySet


class PortfolioVersion(models.Model):
    """Uma composicao da carteira (RF-02): 1, 2, 3... por carteira, sem buraco. A corrente e a
    de maior `number`. So cresce."""

    organization_field = "portfolio__organization_id"

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.PROTECT, related_name="versions"
    )
    number = models.IntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField()

    objects = VersionManager()  # o primeiro declarado: o gerente padrao
    unscoped = VersionBaseManager()

    class Meta:
        db_table = 'core"."portfolio_version'
        base_manager_name = "unscoped"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["portfolio", "number"], name="portfolio_version_number"
            ),
            models.CheckConstraint(
                condition=models.Q(number__gte=1), name="portfolio_version_number_min"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.portfolio_id} v{self.number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise TypeError("portfolio_version so cresce")
        super().save(*args, **kwargs)

    def delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        raise TypeError("portfolio_version so cresce")


class PortfolioHoldingQuerySet(models.QuerySet["PortfolioHolding"]):
    """Recusa as escritas em massa: a posicao so cresce (RF-03)."""

    def update(self, **kwargs: Any) -> int:
        raise TypeError("portfolio_holding so cresce")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise TypeError("portfolio_holding so cresce")


class HoldingManager(OrganizationScopedManager["PortfolioHolding"]):
    """O gerente padrao da posicao, no molde de `VersionManager`."""

    _queryset_class = PortfolioHoldingQuerySet


class HoldingBaseManager(models.Manager["PortfolioHolding"]):
    """O gerente base da posicao, sem escopo, com o mesmo queryset que recusa escrita."""

    _queryset_class = PortfolioHoldingQuerySet


class PortfolioHolding(models.Model):
    """Uma acao de uma versao (RF-03), com o peso em %, exatamente o que a pessoa mandou.

    A soma igual a 100 e regra do servico (RF-09), nao do banco: as linhas nascem juntas, numa
    transacao so, pelo unico servico que as escreve. So cresce.
    """

    organization_field = "version__portfolio__organization_id"

    version = models.ForeignKey(
        PortfolioVersion, on_delete=models.PROTECT, related_name="holdings"
    )
    asset = models.ForeignKey(
        "assets.Asset", on_delete=models.PROTECT, related_name="+"
    )
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    objects = HoldingManager()  # o primeiro declarado: o gerente padrao
    unscoped = HoldingBaseManager()

    class Meta:
        db_table = 'core"."portfolio_holding'
        base_manager_name = "unscoped"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["version", "asset"], name="portfolio_holding_version_asset"
            ),
            models.CheckConstraint(
                condition=models.Q(weight__gt=0) & models.Q(weight__lte=100),
                name="portfolio_holding_weight_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.version_id} {self.asset_id} {self.weight}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise TypeError("portfolio_holding so cresce")
        super().save(*args, **kwargs)

    def delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        raise TypeError("portfolio_holding so cresce")


class PortfolioRiskRun(models.Model):
    """Uma linha por calculo do risco de uma versao (RF-04), com o manifesto da D-15.

    `engine_version` nasce vazio: a `web` cria a linha e nao tem o motor; a abertura, no
    `worker`, a escreve. Sao tres os `update` permitidos, todos sob a trava da execucao e
    condicionados a `running`: a versao do motor, pela abertura; `status` e `finished_at`, pelo
    fecho; e `status` e `finished_at`, pela web, quando o corretor recusa.

    `status` e `requested_models` nao tem `default`, como em `RiskRun`: quem cria a linha
    escreve os dois.
    """

    organization_field = "version__portfolio__organization_id"

    version = models.ForeignKey(
        PortfolioVersion, on_delete=models.PROTECT, related_name="risk_runs"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    calculated_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=10, choices=RiskRun.Status)
    engine_version = models.CharField(max_length=32)
    seed = models.IntegerField()
    train_window_days = models.IntegerField()
    first_date = models.DateField()
    as_of_date = models.DateField()
    session_count = models.IntegerField()
    train_count = models.IntegerField()
    test_count = models.IntegerField()
    requested_models = models.JSONField()
    price_run = models.ForeignKey(
        "assets.CollectionRun", on_delete=models.PROTECT, related_name="+"
    )
    series_sha256 = models.CharField(max_length=64)

    objects = OrganizationScopedManager[
        "PortfolioRiskRun"
    ]()  # o primeiro declarado: o gerente padrao
    unscoped = models.Manager["PortfolioRiskRun"]()

    class Meta:
        db_table = 'gold"."portfolio_risk_run'
        base_manager_name = "unscoped"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["version", "calculated_at"],
                name="prisk_run_version_calculated",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["version", "-calculated_at"], name="prisk_run_version_recent"
            )
        ]

    def __str__(self) -> str:
        return f"{self.version_id} {self.calculated_at:%Y-%m-%d %H:%M:%S}"


class PortfolioRiskResult(models.Model):
    """Um resultado por `(run, model_name, alpha)` (RF-05): as colunas, os tipos e as regras de
    `gold.risk_result`, menos `reused_snapshots` e `trained_snapshots` -- a carteira nao usa
    retratos. Nunca muda depois de escrito (D-16); pende da execucao, e por isso a FK e
    `CASCADE`."""

    organization_field = "run__version__portfolio__organization_id"

    run = models.ForeignKey(
        PortfolioRiskRun, on_delete=models.CASCADE, related_name="results"
    )
    model_name = models.CharField(max_length=32)
    model_category = models.CharField(max_length=16)
    alpha = models.DecimalField(max_digits=6, decimal_places=4)
    hyperparameters = models.JSONField()
    var_latest = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    var_mean = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    violations = models.IntegerField(null=True)
    expected_violations = models.DecimalField(
        max_digits=18, decimal_places=6, null=True
    )
    kupiec_passed = models.BooleanField(null=True)
    kupiec_p_value = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    christoffersen_passed = models.BooleanField(null=True)
    christoffersen_p_value = models.DecimalField(
        max_digits=18, decimal_places=10, null=True
    )
    dq_passed = models.BooleanField(null=True)
    dq_p_value = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    basel_zone = models.CharField(max_length=16, null=True)
    adequate = models.BooleanField(null=True)
    error = models.TextField(default="")

    objects = OrganizationScopedManager[
        "PortfolioRiskResult"
    ]()  # o primeiro declarado: o gerente padrao
    unscoped = models.Manager["PortfolioRiskResult"]()

    class Meta:
        db_table = 'gold"."portfolio_risk_result'
        base_manager_name = "unscoped"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["run", "model_name", "alpha"],
                name="prisk_result_run_model_alpha",
            )
        ]

    def __str__(self) -> str:
        return f"{self.run_id} {self.model_name} {self.alpha}"
