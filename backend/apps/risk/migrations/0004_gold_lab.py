"""As tres tabelas do laboratorio na `gold` (M2.4, RF-05 a RF-07), e os gatilhos que as fazem
so crescer.

Gerada pelo `makemigrations` (Django 6.1.1) a partir de `apps/risk/models.py`; o `RunSQL` do fim
foi acrescentado a mao, no molde de `accounts.0006_report`: uma funcao, `gold.lab_so_cresce`, e um
gatilho `BEFORE UPDATE OR DELETE ... FOR EACH ROW` em cada tabela (RF-06). O `TRUNCATE` passa. A
volta desfaz os tres gatilhos e a funcao antes de as tabelas cairem.

**A dependencia da `assets` e a `0003`**, a mesma da `risk.0003`, e nao a `0004_unaccent` que o
`makemigrations` escolheu por ser a ultima: as FKs so precisam de `silver.asset` e
`bronze.collection_run`. Com a `0004_unaccent`, o `migrate assets 0003` de
`tests/assets/test_unaccent.py` desfaria esta migration, e o `migrate assets` da volta nao a
reaplicaria: as tres tabelas sumiriam do banco de teste para o resto da suite (medido na T2).

**Esta migration nao importa o motor**: a `web`, que nao o tem, precisa conseguir rodar
`migrate`.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0003_yahoo_chart_price_corporate_event"),
        ("risk", "0003_model_snapshot"),
    ]

    operations = [
        migrations.CreateModel(
            name="LabRun",
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
                ("calculated_at", models.DateTimeField()),
                ("finished_at", models.DateTimeField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ok", "Ok"),
                            ("partial", "Partial"),
                            ("failed", "Failed"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "origin",
                    models.CharField(
                        choices=[("risk_close", "Risk Close"), ("command", "Command")],
                        max_length=16,
                    ),
                ),
                ("engine_version", models.CharField(max_length=32)),
                ("seed", models.IntegerField()),
                ("train_window_days", models.IntegerField()),
                ("library_versions", models.JSONField()),
                ("library_versions_hash", models.CharField(max_length=64)),
                ("first_price_date", models.DateField()),
                ("decade_end", models.DateField()),
                ("as_of_date", models.DateField()),
                ("price_count", models.IntegerField()),
                ("train_count", models.IntegerField()),
                ("test_count", models.IntegerField()),
                ("year_count", models.IntegerField()),
                ("price_fingerprint", models.CharField(max_length=64)),
                ("requested_models", models.JSONField()),
                ("error", models.TextField(default="")),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lab_runs",
                        to="assets.asset",
                    ),
                ),
                (
                    "price_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lab_runs",
                        to="assets.collectionrun",
                    ),
                ),
            ],
            options={
                "db_table": 'gold"."lab_run',
                "base_manager_name": "objects",
            },
        ),
        migrations.CreateModel(
            name="LabResult",
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
                ("model_category", models.CharField(max_length=16)),
                ("alpha", models.DecimalField(decimal_places=4, max_digits=6)),
                ("hyperparameters", models.JSONField()),
                ("test_count", models.IntegerField(null=True)),
                ("violations", models.IntegerField(null=True)),
                (
                    "expected_violations",
                    models.DecimalField(decimal_places=6, max_digits=18, null=True),
                ),
                ("kupiec_passed", models.BooleanField(null=True)),
                (
                    "kupiec_p_value",
                    models.DecimalField(decimal_places=10, max_digits=18, null=True),
                ),
                ("christoffersen_passed", models.BooleanField(null=True)),
                (
                    "christoffersen_p_value",
                    models.DecimalField(decimal_places=10, max_digits=18, null=True),
                ),
                ("dq_passed", models.BooleanField(null=True)),
                (
                    "dq_p_value",
                    models.DecimalField(decimal_places=10, max_digits=18, null=True),
                ),
                ("adequate", models.BooleanField(null=True)),
                ("error", models.TextField(default="")),
                ("reused_snapshots", models.IntegerField(null=True)),
                ("trained_snapshots", models.IntegerField(null=True)),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="results",
                        to="risk.labrun",
                    ),
                ),
            ],
            options={
                "db_table": 'gold"."lab_result',
                "base_manager_name": "objects",
            },
        ),
        migrations.CreateModel(
            name="LabYear",
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
                ("index", models.IntegerField()),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("test_count", models.IntegerField()),
                ("violations", models.IntegerField()),
                (
                    "expected_violations",
                    models.DecimalField(decimal_places=6, max_digits=18),
                ),
                ("kupiec_passed", models.BooleanField(null=True)),
                (
                    "kupiec_p_value",
                    models.DecimalField(decimal_places=10, max_digits=18, null=True),
                ),
                ("christoffersen_passed", models.BooleanField(null=True)),
                (
                    "christoffersen_p_value",
                    models.DecimalField(decimal_places=10, max_digits=18, null=True),
                ),
                ("adequate", models.BooleanField(null=True)),
                (
                    "result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="years",
                        to="risk.labresult",
                    ),
                ),
            ],
            options={
                "db_table": 'gold"."lab_year',
                "base_manager_name": "objects",
            },
        ),
        migrations.AddIndex(
            model_name="labrun",
            index=models.Index(
                fields=["asset", "-calculated_at"], name="lab_run_asset_recent"
            ),
        ),
        migrations.AddConstraint(
            model_name="labrun",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "ok")),
                fields=(
                    "asset",
                    "engine_version",
                    "seed",
                    "train_window_days",
                    "first_price_date",
                    "decade_end",
                    "library_versions_hash",
                ),
                name="lab_run_identity_ok",
            ),
        ),
        migrations.AddConstraint(
            model_name="labresult",
            constraint=models.UniqueConstraint(
                fields=("run", "model_name", "alpha"), name="lab_result_run_model_alpha"
            ),
        ),
        migrations.AddConstraint(
            model_name="labyear",
            constraint=models.UniqueConstraint(
                fields=("result", "index"), name="lab_year_result_index"
            ),
        ),
        migrations.RunSQL(
            sql="""
                CREATE FUNCTION gold.lab_so_cresce() RETURNS trigger
                LANGUAGE plpgsql AS $$
                BEGIN
                    RAISE EXCEPTION 'lab so cresce';
                END;
                $$;
                CREATE TRIGGER lab_run_so_cresce
                    BEFORE UPDATE OR DELETE ON gold.lab_run
                    FOR EACH ROW EXECUTE FUNCTION gold.lab_so_cresce();
                CREATE TRIGGER lab_result_so_cresce
                    BEFORE UPDATE OR DELETE ON gold.lab_result
                    FOR EACH ROW EXECUTE FUNCTION gold.lab_so_cresce();
                CREATE TRIGGER lab_year_so_cresce
                    BEFORE UPDATE OR DELETE ON gold.lab_year
                    FOR EACH ROW EXECUTE FUNCTION gold.lab_so_cresce();
            """,
            reverse_sql="""
                DROP TRIGGER lab_year_so_cresce ON gold.lab_year;
                DROP TRIGGER lab_result_so_cresce ON gold.lab_result;
                DROP TRIGGER lab_run_so_cresce ON gold.lab_run;
                DROP FUNCTION gold.lab_so_cresce();
            """,
        ),
    ]
