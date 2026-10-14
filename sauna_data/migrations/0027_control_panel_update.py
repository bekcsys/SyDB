from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0026_power_box_pictures_and_firmware"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="panel_update",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="panel_update_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="panel_update_2",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="panel_update_2_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
