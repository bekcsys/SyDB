from django.db import migrations, models
import django.db.models.deletion

from sauna_data.power_boxes import POWER_BOX_NAMES, power_box_name_for


def populate_power_boxes(apps, schema_editor):
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    Product = apps.get_model("sauna_data", "Product")
    Membership = apps.get_model("sauna_data", "PowerBoxProduct")
    boxes = {name: PowerBox.objects.create(name=name) for name in POWER_BOX_NAMES}
    for product in Product.objects.select_related("supplier"):
        supplier_name = product.supplier.name if product.supplier_id else ""
        box_name = power_box_name_for(product.product_name, product.item_no, supplier_name)
        if not box_name:
            continue
        Membership.objects.create(power_box=boxes[box_name], product=product)


def clear_power_boxes(apps, schema_editor):
    apps.get_model("sauna_data", "PowerBoxProduct").objects.all().delete()
    apps.get_model("sauna_data", "PowerBox").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0013_product_plug_type_and_watt_on_label"),
    ]

    operations = [
        migrations.CreateModel(
            name="PowerBox",
            fields=[
                ("power_box_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "power_boxes",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="PowerBoxProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "power_box",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="sauna_data.powerbox",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="power_box_memberships",
                        to="sauna_data.product",
                    ),
                ),
            ],
            options={
                "db_table": "power_box_products",
            },
        ),
        migrations.AddConstraint(
            model_name="powerboxproduct",
            constraint=models.UniqueConstraint(
                fields=("product",),
                name="power_box_products_one_box",
            ),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="products",
            field=models.ManyToManyField(
                related_name="power_boxes",
                through="sauna_data.PowerBoxProduct",
                to="sauna_data.product",
            ),
        ),
        migrations.RunPython(populate_power_boxes, clear_power_boxes),
    ]
