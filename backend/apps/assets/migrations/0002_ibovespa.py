from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.utils import timezone


def cria_ibovespa(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    Asset = apps.get_model("assets", "Asset")
    now = timezone.now()
    Asset.objects.get_or_create(
        ticker="IBOV",
        defaults={
            "kind": "index",
            "name": "Índice Bovespa",
            "trading_name": "IBOVESPA",
            "status": "active",
            "provider_symbol": "^BVSP",
            "created_at": now,
            "updated_at": now,
        },
    )


def remove_ibovespa(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    Asset = apps.get_model("assets", "Asset")
    Asset.objects.filter(ticker="IBOV").delete()


class Migration(migrations.Migration):
    dependencies = [("assets", "0001_bronze_e_silver_asset")]

    operations = [migrations.RunPython(cria_ibovespa, remove_ibovespa)]
