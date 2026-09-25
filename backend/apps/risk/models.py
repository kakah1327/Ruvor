"""Camada 3: a execucao de risco e os resultados por (modelo, nivel), no esquema `gold`.

O esquema vai embutido no `db_table`, com aspas no meio, como em `analytics`: e o contrato
da D-38 — mudar as aspas muda o esquema em que a tabela nasce. A chave primaria nao e
declarada: o `DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

**Este modulo nao importa o motor.** E o que permite a `web`, que nao tem `engine`
instalado, continuar subindo com `apps.risk` em `INSTALLED_APPS`.

`risk_run` e so-acrescimo (D-16): recalcular insere execucao nova, nenhum caminho do
codigo faz `update` ou `delete`. Os resultados pendem da execucao que os originou, e por
isso — e so por isso — a FK deles e `CASCADE`, nao `PROTECT`: o resultado nao tem vida
propria fora da execucao que o gerou.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class RiskRun(models.Model):
    """Uma linha por `(asset, calculated_at)`: o manifesto de execucao que a D-15 exige.

    `calculated_at` nao leva `auto_now_add`: quem grava escreve o `now()`, uma vez por
    execucao. `price_run` e a coleta mais recente que tocou algum preco da janela usada —
    nao a coleta da linha de maior data, que e outro numero.

    `requested_by` nasce anulavel e sempre nula: nao ha usuario autenticado antes do M2.1,
    e a D-15 fica cumprida pela metade, declaradamente.

    `status` e `requested_models` **nao tem `default`** (RF-08): com `default=running`, o
    caminho que esquecesse de escrever o estado deixaria a linha `running` para sempre, em
    silencio. Para o `status` isso nao basta -- `CharField` sem padrao grava string vazia
    --, e quem o guarda e teste. `requested_models` e a lista de modelos pedidos, na ordem
    do pedido: e contra ela que o estado e decidido.
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
