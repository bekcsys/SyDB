from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0021_part_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="front_picture",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="front_picture_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="back_picture",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="back_picture_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="instruction",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="controlpanel",
            name="instruction_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
