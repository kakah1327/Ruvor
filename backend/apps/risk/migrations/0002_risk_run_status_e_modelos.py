"""O estado da execucao e os modelos pedidos, e o dado que ja existe (M1.5, RF-08).

As duas colunas nascem sem `default` no modelo; o valor dos `AddField` so preenche a
tabela no instante da criacao (`preserve_default=False`) e e em seguida **sobrescrito**
pelo `backfill`, que deriva cada linha existente do proprio dado: o M1.4 grava modelo que
falha como linha com `error`, entao os nomes dos resultados de uma execucao **sao** o que
ela pediu -- inclusive numa execucao com `--model`.

**Esta migration nao importa `apps.risk.compute`**: ele importa o motor, e a `web`, que
nao o tem, deixaria de conseguir rodar `migrate`. Por isso a lista dos nove e a regra do
fecho estao copiadas aqui, e um teste confere a copia contra o original.
"""

from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps

# Os nove modelos, na ordem de `apps.risk.compute.MODELS`.
MODELS = [
    "caviar",
    "egarch",
    "garch_1_1",
    "garchnet",
    "gru",
    "historical",
    "lstm",
    "monte_carlo",
    "parametric",
]


def status_for(expected: int, written: int, with_error: int) -> str:
    """Copia de `apps.risk.compute.status_for`, com os valores do `RiskRun.Status`."""
    if written == 0 or with_error == written:
        return "failed"
    if written == expected and with_error == 0:
        return "ok"
    return "partial"


def backfill(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """`requested_models` e `status` de cada execucao existente, derivados dos resultados."""
    RiskRun = apps.get_model("risk", "RiskRun")
    RiskResult = apps.get_model("risk", "RiskResult")
    order = {name: i for i, name in enumerate(MODELS)}
    for run in RiskRun.objects.order_by("pk"):
        results = RiskResult.objects.filter(run=run)
        names = set(results.values_list("model_name", flat=True))
        # Na ordem de `MODELS`; um nome fora dela -- que o M1.4 nao grava -- vai ao fim,
        # em ordem alfabetica, em vez de sumir.
        requested = sorted(names, key=lambda n: (n not in order, order.get(n, 0), n))
        written = results.count()
        with_error = results.exclude(error="").count()
        run.requested_models = requested
        run.status = status_for(len(requested) * 2, written, with_error)
        run.save(update_fields=["requested_models", "status"])


class Migration(migrations.Migration):
    dependencies = [("risk", "0001_gold_risk_run")]

    operations = [
        migrations.AddField(
            model_name="riskrun",
            name="status",
            field=models.CharField(
                choices=[
                    ("running", "Running"),
                    ("ok", "Ok"),
                    ("partial", "Partial"),
                    ("failed", "Failed"),
                ],
                default="ok",
                max_length=10,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="riskrun",
            name="requested_models",
            field=models.JSONField(default=list(MODELS)),
            preserve_default=False,
        ),
        migrations.RunPython(backfill, reverse_code=migrations.RunPython.noop),
    ]
