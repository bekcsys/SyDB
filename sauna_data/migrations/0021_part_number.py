from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0020_firmware_update_device_supplier"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="part_number",
            field=models.CharField(
                blank=True,
                default="",
                max_length=64,
                verbose_name="Part number",
            ),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="part_number",
            field=models.CharField(
                blank=True,
                default="",
                max_length=64,
                verbose_name="Part number",
            ),
        ),
    ]
