from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0040_product_item_shipped_to_and_revised_serial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="item_no",
            field=models.CharField(
                help_text="Not unique. product_id identifies the product. Each product has one power box.",
                max_length=64,
            ),
        ),
    ]
