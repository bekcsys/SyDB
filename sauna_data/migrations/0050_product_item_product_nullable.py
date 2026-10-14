import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0049_product_item_product_fk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productitem",
            name="product",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="product_items",
                to="sauna_data.product",
            ),
        ),
    ]
