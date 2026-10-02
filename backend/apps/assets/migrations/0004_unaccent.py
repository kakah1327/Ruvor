from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("assets", "0003_yahoo_chart_price_corporate_event")]

    operations = [UnaccentExtension()]
