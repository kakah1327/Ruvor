"""O retorno (M5.1, RF-10): a execucao e os resultados por modelo, no esquema `gold`.

O esquema vai embutido no `db_table`, com aspas no meio, como em `risk`: e o contrato da
D-38. A chave primaria nao e declarada: o `DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

**Este modulo nao importa o motor.** E o que permite a `web`, que nao tem `engine`
instalado, subir com `apps.returns` em `INSTALLED_APPS`.

As duas tabelas sao **imutaveis** (D-16): so `create`; nenhum caminho do codigo faz `update`
ou `delete`, e recalcular insere execucao nova. Os resultados pendem da execucao que os
originou -- por isso, e so por isso, a FK deles e `CASCADE`.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class ReturnRun(models.Model):
    """Uma linha por `(asset, calculated_at)`: o manifesto de execucao (D-15).

    Sem `seed`: nada e aleatorio nos dois modelos (RF-04, D-189). As datas e as contagens
    descrevem a serie que o motor viu, depois do criterio do `clean_prices`; `price_run` e a
    coleta mais recente que tocou um preco da janela, a regra do risco. `requested_by` e o
    autor do pedido sob demanda; nulo na rotina e no comando.
    """

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="return_runs",
    )
    calculated_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    engine_version = models.CharField(max_length=32)
    train_window_days = models.IntegerField()
    as_of_date = models.DateField()
    first_price_date = models.DateField()
    price_count = models.IntegerField()
    train_count = models.IntegerField()
    test_count = models.IntegerField()
    price_run = models.ForeignKey(
        "assets.CollectionRun",
        on_delete=models.PROTECT,
        related_name="return_runs",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="return_runs",
        null=True,
    )

    class Meta:
        db_table = 'gold"."return_run'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["asset", "calculated_at"],
                name="return_run_asset_calculated_at",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["asset", "-calculated_at"], name="return_run_asset_recent"
            )
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.calculated_at:%Y-%m-%d %H:%M:%S}"


class ReturnResult(models.Model):
    """Um resultado por `(run, model_name)`: a validacao, o veredito e a previsao do
    proximo pregao.

    Com `error`, todas as colunas de numero, a data e os dois booleanos sao nulos -- e assim
    que se distingue "o modelo falhou" de "o modelo rodou e nao bateu a referencia".
    """

    run = models.ForeignKey(
        ReturnRun,
        on_delete=models.CASCADE,
        related_name="results",
    )
    model_name = models.CharField(max_length=32)
    hyperparameters = models.JSONField()
    mse = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    mse_reference = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    r2_os = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    direction_days = models.IntegerField(null=True)
    hit_rate = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    up_share = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    forecast_up_share = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    dm_statistic = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    dm_p_value = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    cw_statistic = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    cw_p_value = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    pt_statistic = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    pt_p_value = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    beats_reference = models.BooleanField(null=True)
    direction_skill = models.BooleanField(null=True)
    next_forecast = models.DecimalField(max_digits=18, decimal_places=10, null=True)
    next_forecast_date = models.DateField(null=True)
    error = models.TextField(default="")

    class Meta:
        db_table = 'gold"."return_result'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["run", "model_name"], name="return_result_run_model"
            )
        ]

    def __str__(self) -> str:
        return f"{self.run_id} {self.model_name}"
