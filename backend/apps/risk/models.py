"""Camada 3: a execucao de risco e os resultados por (modelo, nivel), no esquema `gold`.

O esquema vai embutido no `db_table`, com aspas no meio, como em `analytics`: e o contrato
da D-38 — mudar as aspas muda o esquema em que a tabela nasce. A chave primaria nao e
declarada: o `DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

**Este modulo nao importa o motor.** E o que permite a `web`, que nao tem `engine`
instalado, continuar subindo com `apps.risk` em `INSTALLED_APPS`.

Nenhum `risk_result` e alterado nem apagado (D-16): recalcular insere execucao nova. A
`risk_run` recebe `status` e `finished_at` de `close_run` -- metadado de execucao, nao
resultado, e e a restricao a D-16 que a spec do M1.5 descreve. `close_run` so escreve sobre
execucao em `running` (D-150), e dois caminhos o chamam -- o fecho da execucao assincrona e a
varredura das execucoes presas (M1.5c, D-149) --, mais a abertura que nao consegue enfileirar.
Nenhum caminho do codigo faz `delete`. Os resultados pendem da execucao que os originou, e por
isso — e so por isso — a FK deles e `CASCADE`, nao `PROTECT`: o resultado nao tem vida
propria fora da execucao que o gerou.

O laboratorio (M2.4, RF-05 a RF-07) mora nas tres ultimas tabelas, `lab_run`, `lab_result` e
`lab_year`, que **so crescem**: no Django, o molde de `core.report`; no banco, os gatilhos da
migration `0004`.
"""

from __future__ import annotations

from typing import Any, ClassVar, TypeVar

from django.conf import settings
from django.db import models
from django.db.models import Q

_M = TypeVar("_M", bound=models.Model)


class RiskRun(models.Model):
    """Uma linha por `(asset, calculated_at)`: o manifesto de execucao que a D-15 exige.

    `calculated_at` nao leva `auto_now_add`: quem grava escreve o `now()`, uma vez por
    execucao. `price_run` e a coleta mais recente que tocou algum preco da janela usada —
    nao a coleta da linha de maior data, que e outro numero.

    `requested_by` e o autor do pedido sob demanda que abriu a execucao (M2.1a, RF-26).
    Fica nula na rotina, no caminho sincrono, no pedido anonimo e em toda execucao anterior
    ao M2.1a; o pedido que se liga a uma execucao ja em andamento nao a muda.

    `status` e `requested_models` **nao tem `default`** (RF-08): com `default=running`, o
    caminho que esquecesse de escrever o estado deixaria a linha `running` para sempre, em
    silencio. Para o `status` isso nao basta -- `CharField` sem padrao grava string vazia
    --, e quem o guarda e teste. `requested_models` e a lista de modelos pedidos, na ordem
    do pedido: e contra ela que o estado e decidido.

    `full_recompute` diz o que foi **pedido** -- `--full` ou nao --, e tambem nao tem
    `default` (M1.5b): quem cria a linha escreve o valor. As execucoes anteriores ao M1.5b
    nasceram `false` na migration `0003`.
    """

    class Status(models.TextChoices):
        RUNNING = "running"
        OK = "ok"
        PARTIAL = "partial"
        FAILED = "failed"

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="risk_runs",
    )
    calculated_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True)
    engine_version = models.CharField(max_length=32)
    seed = models.IntegerField()
    train_window_days = models.IntegerField()
    as_of_date = models.DateField()
    first_price_date = models.DateField()
    price_count = models.IntegerField()
    train_count = models.IntegerField()
    test_count = models.IntegerField()
    price_run = models.ForeignKey(
        "assets.CollectionRun",
        on_delete=models.PROTECT,
        related_name="risk_runs",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="risk_runs",
        null=True,
    )
    status = models.CharField(max_length=10, choices=Status)
    requested_models = models.JSONField()
    full_recompute = models.BooleanField()

    class Meta:
        db_table = 'gold"."risk_run'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["asset", "calculated_at"],
                name="risk_run_asset_calculated_at",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["asset", "-calculated_at"], name="risk_run_asset_recent"
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.calculated_at:%Y-%m-%d %H:%M:%S}"


class RiskResult(models.Model):
    """Um resultado por `(run, model_name, alpha)`: o VaR, os quatro backtests e o veredito.

    Quando `error` nao e vazio, todas as colunas de numero sao nulas — e assim que se
    distingue "o modelo falhou" de "o modelo rodou e foi reprovado".

    `reused_snapshots` e `trained_snapshots` contam os retratos que o motor restaurou e os
    que treinou naquele (modelo, nivel) -- so nos quatro modelos caros e so sem erro; nulos
    nos demais casos (M1.5b, RF-09).

    `violations` e `expected_violations` sao **os do Kupiec**, sobre o periodo de teste
    inteiro; a leitura regulatoria, que olha so os ultimos 250 pregoes, fica em
    `basel_zone`.
    """

    run = models.ForeignKey(
        RiskRun,
        on_delete=models.CASCADE,
        related_name="results",
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
    reused_snapshots = models.IntegerField(null=True)
    trained_snapshots = models.IntegerField(null=True)

    class Meta:
        db_table = 'gold"."risk_result'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["run", "model_name", "alpha"],
                name="risk_result_run_model_alpha",
            )
        ]

    def __str__(self) -> str:
        return f"{self.run_id} {self.model_name} {self.alpha}"


class ModelSnapshot(models.Model):
    """Um retrato por (identidade, ponto de retreino) de um modelo caro (M1.5b, RF-02).

    Imutavel: nenhum caminho do codigo faz `update` nem `delete`, e a insercao e
    idempotente pela unicidade `model_snapshot_identity`, que cobre **todos** os onze
    componentes da identidade (RF-03) -- os hiperparametros e as versoes de biblioteca pelo
    hash. `created_at` nao leva `auto_now_add`: quem grava escreve o `now()`, como nas
    outras tabelas de dado.

    O retrato nao pende de nenhuma `risk_run`: e reaproveitado por execucoes seguintes, e
    por isso a unica FK e o `asset`, com `PROTECT`.
    """

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="model_snapshots",
    )
    model_name = models.CharField(max_length=32)
    alpha = models.DecimalField(max_digits=6, decimal_places=4)
    position = models.IntegerField()
    trained_through = models.DateField()
    seed = models.IntegerField()
    engine_version = models.CharField(max_length=32)
    train_window_days = models.IntegerField()
    first_price_date = models.DateField()
    hyperparameters = models.JSONField()
    hyperparameters_hash = models.CharField(max_length=64)
    library_versions = models.JSONField()
    library_versions_hash = models.CharField(max_length=64)
    price_fingerprint = models.CharField(max_length=64)
    payload = models.BinaryField()
    payload_bytes = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'gold"."model_snapshot'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=[
                    "asset",
                    "model_name",
                    "alpha",
                    "position",
                    "seed",
                    "engine_version",
                    "hyperparameters_hash",
                    "library_versions_hash",
                    "train_window_days",
                    "first_price_date",
                    "price_fingerprint",
                ],
                name="model_snapshot_identity",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["asset", "model_name", "alpha", "position"],
                name="model_snapshot_lookup",
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.model_name} {self.alpha} {self.position}"


# --- o laboratorio (M2.4) -----------------------------------------------------------------


class LabQuerySet(models.QuerySet[_M]):
    """Recusa as escritas em massa: o laboratorio so cresce (M2.4, RF-06)."""

    def update(self, **kwargs: Any) -> int:
        raise TypeError("lab so cresce")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise TypeError("lab so cresce")


class LabManager(models.Manager[_M]):
    """O gerente das tres tabelas do laboratorio, com o queryset que recusa escrita em massa.

    E o gerente padrao e o base (`base_manager_name`), e o acessor reverso o subclassa: nenhum
    caminho do Django chega a um queryset que aceite `update` ou `delete`.
    """

    _queryset_class = LabQuerySet


class _GrowOnly(models.Model):
    """`save` de linha existente e `delete` da instancia levantam (o molde de `Report`)."""

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise TypeError("lab so cresce")
        super().save(*args, **kwargs)

    def delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        raise TypeError("lab so cresce")


class LabRun(_GrowOnly):
    """O experimento fixo da decada de um ativo: o manifesto (D-15), uma linha por tentativa.

    **Nasce fechada** (RF-06): o calculo inteiro acontece antes da escrita, e a execucao, os
    resultados e os anos entram numa transacao so, com `status` e `finished_at` ja finais.
    `status` e `origin` **nao tem `default`**, como em `risk_run`: quem grava escreve o valor.

    A identidade (RF-07) e (`asset`, `engine_version`, `seed`, `train_window_days`,
    `first_price_date`, `decade_end`, `library_versions_hash`); a restricao unica
    `lab_run_identity_ok` vale **so sobre `ok`** -- `partial` e `failed` ficam registrados e
    nao impedem a tentativa seguinte. `price_fingerprint` diz de que precos o experimento saiu
    e nao entra na identidade.
    """

    class Status(models.TextChoices):
        OK = "ok"
        PARTIAL = "partial"
        FAILED = "failed"

    class Origin(models.TextChoices):
        RISK_CLOSE = "risk_close"
        COMMAND = "command"

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="lab_runs",
    )
    calculated_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status)
    origin = models.CharField(max_length=16, choices=Origin)
    engine_version = models.CharField(max_length=32)
    seed = models.IntegerField()
    train_window_days = models.IntegerField()
    library_versions = models.JSONField()
    library_versions_hash = models.CharField(max_length=64)
    first_price_date = models.DateField()
    decade_end = models.DateField()
    as_of_date = models.DateField()
    price_count = models.IntegerField()
    train_count = models.IntegerField()
    test_count = models.IntegerField()
    year_count = models.IntegerField()
    price_run = models.ForeignKey(
        "assets.CollectionRun",
        on_delete=models.PROTECT,
        related_name="lab_runs",
    )
    price_fingerprint = models.CharField(max_length=64)
    requested_models = models.JSONField()
    error = models.TextField(default="")

    objects = LabManager["LabRun"]()

    class Meta:
        db_table = 'gold"."lab_run'
        base_manager_name = "objects"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=[
                    "asset",
                    "engine_version",
                    "seed",
                    "train_window_days",
                    "first_price_date",
                    "decade_end",
                    "library_versions_hash",
                ],
                condition=Q(status="ok"),
                name="lab_run_identity_ok",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["asset", "-calculated_at"], name="lab_run_asset_recent"
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.calculated_at:%Y-%m-%d %H:%M:%S} {self.status}"


class LabResult(_GrowOnly):
    """Um resultado por (`run`, `model_name`, `alpha`), sobre a decada inteira (RF-04).

    O que `risk_result` guarda, menos `var_latest`, `var_mean` e `basel_zone` (RF-08), mais
    `test_count`. Com `error` nao vazio, os numeros e o `adequate` sao nulos: "falhou" se
    distingue de "reprovado" pelo `adequate` nulo.
    """

    run = models.ForeignKey(
        LabRun,
        on_delete=models.PROTECT,
        related_name="results",
    )
    model_name = models.CharField(max_length=32)
    model_category = models.CharField(max_length=16)
    alpha = models.DecimalField(max_digits=6, decimal_places=4)
    hyperparameters = models.JSONField()
    test_count = models.IntegerField(null=True)
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
    adequate = models.BooleanField(null=True)
    error = models.TextField(default="")
    reused_snapshots = models.IntegerField(null=True)
    trained_snapshots = models.IntegerField(null=True)

    objects = LabManager["LabResult"]()

    class Meta:
        db_table = 'gold"."lab_result'
        base_manager_name = "objects"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["run", "model_name", "alpha"],
                name="lab_result_run_model_alpha",
            )
        ]

    def __str__(self) -> str:
        return f"{self.run_id} {self.model_name} {self.alpha}"


class LabYear(_GrowOnly):
    """Um trecho de teste por (`result`, `index`): 252 retornos a partir da posicao 0 (RF-03).

    Os testes e o veredito sao nulos a 99% e no trecho com menos de 126 retornos. So existe
    para resultado sem erro. FK `PROTECT`, e nao `CASCADE`: o gatilho recusa o `DELETE` do pai.
    """

    result = models.ForeignKey(
        LabResult,
        on_delete=models.PROTECT,
        related_name="years",
    )
    index = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    test_count = models.IntegerField()
    violations = models.IntegerField()
    expected_violations = models.DecimalField(max_digits=18, decimal_places=6)
    kupiec_passed = models.BooleanField(null=True)
    kupiec_p_value = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    christoffersen_passed = models.BooleanField(null=True)
    christoffersen_p_value = models.DecimalField(
        max_digits=18, decimal_places=10, null=True
    )
    adequate = models.BooleanField(null=True)

    objects = LabManager["LabYear"]()

    class Meta:
        db_table = 'gold"."lab_year'
        base_manager_name = "objects"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["result", "index"],
                name="lab_year_result_index",
            )
        ]

    def __str__(self) -> str:
        return f"{self.result_id} {self.index}"
