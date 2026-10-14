from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0006_unit_qc_videos"),
    ]

    operations = [
        migrations.AddField(
            model_name="physicalunit",
            name="qc_uploads",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
