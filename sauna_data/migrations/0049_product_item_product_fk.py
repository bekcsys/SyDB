import django.db.models.deletion
from django.db import migrations, models


def link_known_items(apps, schema_editor):
    Item = apps.get_model("sauna_data", "ProductItem")
    Product = apps.get_model("sauna_data", "Product")
    matches = list(Product.objects.filter(product_name__istartswith="CS.6-EVR1").order_by("product_id"))
    if len(matches) == 1:
        Item.objects.filter(serial_no="73204-3010", product_id__isnull=True).update(product_id=matches[0].pk)


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0048_simplify_product_items"),
    ]

    operations = [
        migrations.AddField(
            model_name="productitem",
            name="product",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="product_items",
                to="sauna_data.product",
            ),
        ),
        migrations.RunPython(link_known_items, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="productitem",
                    name="product",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="product_items",
                        to="sauna_data.product",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM product_items WHERE product_id IS NULL) THEN
                            ALTER TABLE product_items ALTER COLUMN product_id SET NOT NULL;
                        END IF;
                    END $$;
                    """,
                    reverse_sql="ALTER TABLE product_items ALTER COLUMN product_id DROP NOT NULL;",
                ),
            ],
        ),
    ]
