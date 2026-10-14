from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0031_remove_test_runs"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="controlpanel",
            name="supplier",
        ),
    ]
