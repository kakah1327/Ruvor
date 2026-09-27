"""Os retratos dos modelos caros e de onde eles vieram (M1.5b, RF-02, RF-08, RF-09).

Escrita a mao, a partir do contrato da tabela do plano: `full_recompute` e um
`BooleanField` sem `default`, e o `makemigrations` pergunta o valor para as linhas
existentes -- o que nao roda com `exec -T`. O `default=False` do `AddField` so preenche as
execucoes anteriores ao bloco no instante da criacao (`preserve_default=False`): nenhuma
delas foi pedida como `--full`, e o campo diz o que foi **pedido**. As duas contagens do
`risk_result` nascem nulas nas linhas existentes, como o RF-09 manda para quem nao leu
retrato.

**Esta migration nao importa o motor**: a `web`, que nao o tem, precisa conseguir rodar
`migrate`.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0003_yahoo_chart_price_corporate_event"),
        ("risk", "0002_risk_run_status_e_modelos"),
    ]

    operations = [
        migrations.AddField(
            model_name="riskrun",
            name="full_recompute",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="riskresult",
            name="reused_snapshots",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="riskresult",
            name="trained_snapshots",
            field=models.IntegerField(null=True),
        ),
        migrations.CreateModel(
            name="ModelSnapshot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("model_name", models.CharField(max_length=32)),
                ("alpha", models.DecimalField(decimal_places=4, max_digits=6)),
                ("position", models.IntegerField()),
                ("trained_through", models.DateField()),
                ("seed", models.IntegerField()),
                ("engine_version", models.CharField(max_length=32)),
                ("train_window_days", models.IntegerField()),
                ("first_price_date", models.DateField()),
                ("hyperparameters", models.JSONField()),
                ("hyperparameters_hash", models.CharField(max_length=64)),
                ("library_versions", models.JSONField()),
                ("library_versions_hash", models.CharField(max_length=64)),
                ("price_fingerprint", models.CharField(max_length=64)),
                ("payload", models.BinaryField()),
                ("payload_bytes", models.IntegerField()),
                ("created_at", models.DateTimeField()),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="model_snapshots",
                        to="assets.asset",
                    ),
                ),
            ],
            options={
                "db_table": 'gold"."model_snapshot',
            },
        ),
        migrations.AddIndex(
            model_name="modelsnapshot",
            index=models.Index(
                fields=["asset", "model_name", "alpha", "position"],
                name="model_snapshot_lookup",
            ),
        ),
        migrations.AddConstraint(
            model_name="modelsnapshot",
            constraint=models.UniqueConstraint(
                fields=(
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
                ),
                name="model_snapshot_identity",
            ),
        ),
    ]
