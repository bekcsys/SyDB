from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0039_product_item_po_date_and_proforma"),
    ]

    operations = [
        migrations.AddField(
            model_name="productitem",
            name="revised_serial_no",
            field=models.CharField(
                blank=True,
                max_length=64,
                null=True,
                verbose_name="Revised Serial Number",
            ),
        ),
        migrations.AddField(
            model_name="productitem",
            name="shipped_to",
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name="Shipped to"),
        ),
    ]
