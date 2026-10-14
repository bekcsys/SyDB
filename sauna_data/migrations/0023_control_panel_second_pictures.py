from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0022_control_panel_files"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="front_picture_2",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="front_picture_2_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="back_picture_2",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="back_picture_2_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
