from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0042_smmak_power_box_by_voltage"),
    ]

    operations = [
        migrations.AddField(
            model_name="powerbox",
            name="note",
            field=models.TextField(blank=True, default=""),
        ),
    ]
