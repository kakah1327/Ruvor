from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def cria_organizacao_do_marco1(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Organization = apps.get_model("accounts", "Organization")
    Organization.objects.get_or_create(slug="ruvor", defaults={"name": "Ruvor"})


def remove_organizacao_do_marco1(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Organization = apps.get_model("accounts", "Organization")
    Organization.objects.filter(slug="ruvor").delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_esquemas_organization_user")]

    operations = [
        migrations.RunPython(cria_organizacao_do_marco1, remove_organizacao_do_marco1),
    ]
