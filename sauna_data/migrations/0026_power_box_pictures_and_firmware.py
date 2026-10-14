from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0025_control_panel_extra_pdfs"),
    ]

    operations = [
        migrations.AddField(
            model_name="powerbox",
            name="picture",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="picture_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="picture_2",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="picture_2_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="picture_3",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="picture_3_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_instruction",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_instruction_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_instruction_2",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_instruction_2_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
