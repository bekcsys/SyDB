from django.db import migrations, models


def copy_order_fields_onto_units(apps, schema_editor):
    Unit = apps.get_model("sauna_data", "PhysicalUnit")
    for unit in Unit.objects.select_related("order"):
        order = unit.order
        if order is None:
            continue
        unit.customer_no = order.customer_no
        unit.order_date = order.order_date
        if not unit.order_no:
            unit.order_no = order.order_no
        unit.save(update_fields=["customer_no", "order_date", "order_no"])


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0029_product_power_box"),
    ]

    operations = [
        migrations.AddField(
            model_name="physicalunit",
            name="customer_no",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="physicalunit",
            name="order_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(copy_order_fields_onto_units, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="testrun",
            name="order",
        ),
        migrations.RemoveField(
            model_name="physicalunit",
            name="order",
        ),
        migrations.DeleteModel(
            name="Order",
        ),
    ]
