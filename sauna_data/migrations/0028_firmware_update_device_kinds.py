import django.db.models.deletion
from django.db import migrations, models

LEGACY_DEVICE_NAMES = (
    "Royal-Device(iMQ)",
    "Luis-Devices(ACD2, ACD3)",
    "Wang-Device1",
    "Wang-Device2",
    "Li-Device",
)
POWER_BOX_DEVICES = ("Luis-ACD2", "Luis-ACD3")
CONTROL_PANEL_DEVICES = (
    ("RFR_EVR1 140F to 150F re-calibration.pdf", "CP-Li"),
    ("wang CS-CP Unlock device.pdf", "CP-wang"),
)


def clear_firmware_update_devices(apps, schema_editor):
    apps.get_model("sauna_data", "FirmwareUpdateDevice").objects.all().delete()


def restore_legacy_firmware_update_devices(apps, schema_editor):
    Device = apps.get_model("sauna_data", "FirmwareUpdateDevice")
    Device.objects.bulk_create(Device(name=name) for name in LEGACY_DEVICE_NAMES)


def seed_firmware_update_devices(apps, schema_editor):
    Device = apps.get_model("sauna_data", "FirmwareUpdateDevice")
    ControlPanel = apps.get_model("sauna_data", "ControlPanel")
    panel_names = [panel_name for _, panel_name in CONTROL_PANEL_DEVICES]
    panels = {
        panel.name: panel
        for panel in ControlPanel.objects.filter(name__in=panel_names)
    }
    missing = [name for name in panel_names if name not in panels]
    if missing:
        raise RuntimeError(f"Control panels missing for firmware devices: {missing}")
    Device.objects.bulk_create(
        Device(name=name, kind="POWER_BOX") for name in POWER_BOX_DEVICES
    )
    Device.objects.bulk_create(
        Device(name=name, kind="CONTROL_PANEL", control_panel=panels[panel_name])
        for name, panel_name in CONTROL_PANEL_DEVICES
    )


def clear_seeded_firmware_update_devices(apps, schema_editor):
    names = list(POWER_BOX_DEVICES) + [name for name, _ in CONTROL_PANEL_DEVICES]
    apps.get_model("sauna_data", "FirmwareUpdateDevice").objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0027_control_panel_update"),
    ]

    operations = [
        migrations.RunPython(
            clear_firmware_update_devices,
            restore_legacy_firmware_update_devices,
        ),
        migrations.RemoveField(
            model_name="firmwareupdatedevice",
            name="supplier",
        ),
        migrations.AddField(
            model_name="firmwareupdatedevice",
            name="kind",
            field=models.CharField(
                choices=[("POWER_BOX", "Power box"), ("CONTROL_PANEL", "Control panel")],
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="firmwareupdatedevice",
            name="control_panel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="firmware_update_devices",
                to="sauna_data.controlpanel",
            ),
        ),
        migrations.AddConstraint(
            model_name="firmwareupdatedevice",
            constraint=models.CheckConstraint(
                condition=models.Q(kind__in=["POWER_BOX", "CONTROL_PANEL"]),
                name="firmware_update_devices_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="firmwareupdatedevice",
            constraint=models.CheckConstraint(
                condition=models.Q(kind="POWER_BOX", control_panel__isnull=True)
                | models.Q(kind="CONTROL_PANEL", control_panel__isnull=False),
                name="firmware_update_devices_kind_panel",
            ),
        ),
        migrations.RunPython(
            seed_firmware_update_devices,
            clear_seeded_firmware_update_devices,
        ),
    ]
