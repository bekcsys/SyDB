import re

import django.db.models.deletion
from django.db import migrations, models


def assign_firmware_device_suppliers(apps, schema_editor):
    Device = apps.get_model("sauna_data", "FirmwareUpdateDevice")
    Supplier = apps.get_model("sauna_data", "Supplier")
    suppliers = list(Supplier.objects.all())
    for device in Device.objects.all():
        tokens = {
            token.casefold()
            for token in re.split(r"[^A-Za-z0-9]+", device.name)
            if token
        }
        matches = [supplier for supplier in suppliers if supplier.name.casefold() in tokens]
        if len(matches) == 1:
            device.supplier = matches[0]
            device.save(update_fields=["supplier"])


def clear_firmware_device_suppliers(apps, schema_editor):
    apps.get_model("sauna_data", "FirmwareUpdateDevice").objects.update(supplier=None)


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0019_control_panel_supplier"),
    ]

    operations = [
        migrations.AddField(
            model_name="firmwareupdatedevice",
            name="supplier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="firmware_update_devices",
                to="sauna_data.supplier",
            ),
        ),
        migrations.RunPython(assign_firmware_device_suppliers, clear_firmware_device_suppliers),
    ]
