import django.db.models.deletion
from django.db import migrations, models


def assign_product_power_boxes(apps, schema_editor):
    Product = apps.get_model("sauna_data", "Product")
    Membership = apps.get_model("sauna_data", "PowerBoxProduct")
    chosen = {}
    for membership in Membership.objects.order_by("id"):
        chosen.setdefault(membership.product_id, membership.power_box_id)
    for product_id, power_box_id in chosen.items():
        Product.objects.filter(pk=product_id).update(power_box_id=power_box_id)


def restore_power_box_links(apps, schema_editor):
    Product = apps.get_model("sauna_data", "Product")
    Membership = apps.get_model("sauna_data", "PowerBoxProduct")
    Membership.objects.bulk_create(
        Membership(product_id=product.pk, power_box_id=product.power_box_id)
        for product in Product.objects.exclude(power_box_id=None)
    )


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0028_firmware_update_device_kinds"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="power_box",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="sauna_data.powerbox",
            ),
        ),
        migrations.RunPython(assign_product_power_boxes, restore_power_box_links),
        migrations.RemoveField(
            model_name="powerbox",
            name="products",
        ),
        migrations.DeleteModel(
            name="PowerBoxProduct",
        ),
    ]
