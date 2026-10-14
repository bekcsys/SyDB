from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0038_power_box_firmware_device_boxes"),
    ]

    operations = [
        migrations.AddField(
            model_name="productitem",
            name="po_date",
            field=models.DateField(blank=True, null=True, verbose_name="PO Date"),
        ),
        migrations.AddField(
            model_name="productitem",
            name="proforma",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="Proforma"),
        ),
    ]
