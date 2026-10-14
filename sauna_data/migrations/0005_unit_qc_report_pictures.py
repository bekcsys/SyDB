from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0004_drop_orders_without_units"),
    ]

    operations = [
        migrations.AddField(
            model_name="physicalunit",
            name="qc_pictures",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="physicalunit",
            name="qc_report_bucket",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="physicalunit",
            name="qc_report_file_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="physicalunit",
            name="qc_report_s3_key",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="physicalunit",
            name="qc_report_stored_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
