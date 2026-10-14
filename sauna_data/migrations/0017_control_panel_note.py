from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0016_control_panels"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="note",
            field=models.TextField(blank=True, default=""),
        ),
    ]
