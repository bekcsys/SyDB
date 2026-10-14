from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0024_rename_control_panel_pictures"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="instruction_2",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="instruction_2_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="instruction_3",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="instruction_3_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
