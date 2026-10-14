from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0030_remove_orders"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TestRun",
        ),
    ]
