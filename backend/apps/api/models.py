"""O pedido de calculo sob demanda, no esquema `core` (RF-15 do M1.6a).

Dado operacional (D-37), num esquema que e da aplicacao, nao de uma frente. O esquema vai
embutido no `db_table`, com aspas no meio, como em `apps/risk/models.py`: e o contrato da
D-38 -- mudar as aspas muda o esquema em que a tabela nasce. A chave primaria nao e
declarada: o `DEFAULT_AUTO_FIELD` ja e `BigAutoField`.

**Este modulo nao importa o motor** (RF-10): a `web` o carrega.
"""

from __future__ import annotations

from typing import ClassVar

from django.db import models


class ComputeRequest(models.Model):
    """Um pedido de calculo de risco para um ativo nunca calculado.

    O indice unico parcial sobre `asset`, para `queued` e `running`, e a guarda do banco do
    RF-16: quem governa a concorrencia e a trava global do `POST`, e o indice so barra o
    caminho que inserir sem ela -- com `IntegrityError`, que a view nao trata.

    `reason` e o desfecho legivel, preenchido ao fechar, da lista fechada de
    `apps/api/ondemand.py`; `error`, so quando falhou. `risk_run` nao e unica: varios
    pedidos podem se ligar a mesma execucao em andamento (RF-24).
    """

    class Status(models.TextChoices):
        QUEUED = "queued"
        RUNNING = "running"
        DONE = "done"
        FAILED = "failed"
        EXPIRED = "expired"

    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="compute_requests",
    )
    requested_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status)
    finished_at = models.DateTimeField(null=True)
    reason = models.TextField(default="")
    error = models.TextField(default="")
    risk_run = models.ForeignKey(
        "risk.RiskRun",
        on_delete=models.PROTECT,
        related_name="compute_requests",
        null=True,
    )

    class Meta:
        db_table = 'core"."compute_request'
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["asset"],
                condition=models.Q(status__in=["queued", "running"]),
                name="compute_request_one_open_per_asset",
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["status"], name="compute_request_status_idx")
        ]

    def __str__(self) -> str:
        return f"{self.asset_id} {self.status} {self.requested_at:%Y-%m-%d %H:%M:%S}"
