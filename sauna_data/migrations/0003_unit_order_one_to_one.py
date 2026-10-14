from datetime import date

from django.db import migrations, models
import django.db.models.deletion


def attach_units_one_to_one(apps, schema_editor):
    Order = apps.get_model("sauna_data", "Order")
    PhysicalUnit = apps.get_model("sauna_data", "PhysicalUnit")
    TestRun = apps.get_model("sauna_data", "TestRun")

    claimed = set()
    extras = []
    for unit in PhysicalUnit.objects.exclude(order_id=None).order_by("unit_id"):
        if unit.order_id in claimed:
            extras.append(unit)
        else:
            claimed.add(unit.order_id)
    for unit in extras:
        if TestRun.objects.filter(unit_id=unit.unit_id).exists():
            source = Order.objects.get(pk=unit.order_id)
            clone = Order.objects.create(
                order_no=source.order_no,
                product_id=source.product_id,
                item_no=source.item_no,
                customer_no=source.customer_no,
                order_date=source.order_date,
                sales_person=source.sales_person,
                quantity=1,
            )
            unit.order_id = clone.order_id
            unit.save(update_fields=["order_id"])
        else:
            unit.delete()

    for unit in PhysicalUnit.objects.filter(order_id=None):
        if TestRun.objects.filter(unit_id=unit.unit_id).exists():
            order_date = unit.date_assigned or unit.date_received or date(2026, 1, 1)
            order = Order.objects.create(
                order_no=unit.order_no or f"UNIT-{unit.unit_id}",
                product_id=unit.product_id,
                item_no=unit.item_no,
                customer_no="",
                order_date=order_date,
                sales_person="",
                quantity=1,
            )
            unit.order_id = order.order_id
            unit.order_no = order.order_no
            unit.save(update_fields=["order_id", "order_no"])
        else:
            unit.delete()


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("sauna_data", "0002_allow_duplicate_order_no"),
    ]

    operations = [
        migrations.RunPython(attach_units_one_to_one, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="physicalunit",
            name="unit_status",
            field=models.CharField(
                choices=[
                    ("IN_STOCK", "In stock"),
                    ("ASSIGNED", "Assigned"),
                    ("SETUP", "Setup"),
                    ("TESTING", "Testing"),
                    ("QC_PASSED", "QC passed"),
                    ("QC_FAILED", "QC failed"),
                    ("ON_HOLD", "On hold"),
                    ("READY_TO_SHIP", "Ready to ship"),
                    ("SHIPPED", "Shipped"),
                ],
                default="ASSIGNED",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="physicalunit",
            name="order",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="physical_unit",
                to="sauna_data.order",
            ),
        ),
    ]
