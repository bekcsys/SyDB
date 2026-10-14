import django.db.models.deletion
from django.db import migrations, models


def assign_control_panel_suppliers(apps, schema_editor):
    ControlPanel = apps.get_model("sauna_data", "ControlPanel")
    PowerBoxProduct = apps.get_model("sauna_data", "PowerBoxProduct")
    for panel in ControlPanel.objects.all():
        supplier_ids = {
            supplier_id
            for supplier_id in PowerBoxProduct.objects.filter(
                power_box__control_panel=panel
            ).values_list("product__supplier_id", flat=True)
            if supplier_id is not None
        }
        if len(supplier_ids) == 1:
            panel.supplier_id = supplier_ids.pop()
            panel.save(update_fields=["supplier"])


def clear_control_panel_suppliers(apps, schema_editor):
    apps.get_model("sauna_data", "ControlPanel").objects.update(supplier=None)


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0018_firmware_update_devices"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="supplier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="control_panels",
                to="sauna_data.supplier",
            ),
        ),
        migrations.RunPython(assign_control_panel_suppliers, clear_control_panel_suppliers),
    ]
