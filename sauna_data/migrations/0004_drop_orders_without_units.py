from django.db import migrations


def delete_orders_without_units(apps, schema_editor):
    Order = apps.get_model("sauna_data", "Order")
    PhysicalUnit = apps.get_model("sauna_data", "PhysicalUnit")
    linked = PhysicalUnit.objects.exclude(order_id=None).values_list("order_id", flat=True)
    Order.objects.exclude(pk__in=linked).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0003_unit_order_one_to_one"),
    ]

    operations = [
        migrations.RunPython(delete_orders_without_units, migrations.RunPython.noop),
    ]
