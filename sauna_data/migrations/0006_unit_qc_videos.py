from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0005_unit_qc_report_pictures"),
    ]

    operations = [
        migrations.AddField(
            model_name="physicalunit",
            name="qc_videos",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
