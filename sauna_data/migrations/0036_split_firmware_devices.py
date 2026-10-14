import re

import django.db.models.deletion
from django.db import migrations, models

_TOKEN = re.compile(r"[a-z0-9]+")
_SKIPPED_TOKENS = {"device", "update", "pdf", "file", "firmware"}


def _tokens(name: str) -> list[str]:
    return [
        token
        for token in _TOKEN.findall(name.lower())
        if len(token) >= 4 and token not in _SKIPPED_TOKENS
    ]


def _matching_boxes(device_name: str, boxes: list) -> list:
    tokens = _tokens(device_name)
    return [box for box in boxes if any(token in box.name.lower() for token in tokens)]


def _power_box_for_devices(devices: list, boxes: list) -> dict:
    assigned = {}
    grouped: dict[frozenset, list] = {}
    for device in devices:
        found = _matching_boxes(device.name, boxes)
        if len(found) == 1:
            assigned[device.pk] = found[0]
        elif len(found) > 1:
            grouped.setdefault(frozenset(box.pk for box in found), []).append(device)
        else:
            raise RuntimeError(f"No power box matches firmware device {device.name!r}.")
    boxes_by_id = {box.pk: box for box in boxes}
    for box_ids, group in grouped.items():
        ordered_boxes = sorted((boxes_by_id[box_id] for box_id in box_ids), key=lambda box: box.name)
        ordered_devices = sorted(group, key=lambda device: device.name)
        if len(ordered_devices) == len(ordered_boxes):
            pairs = zip(ordered_devices, ordered_boxes)
        else:
            pairs = ((device, ordered_boxes[0]) for device in ordered_devices)
        for device, box in pairs:
            assigned[device.pk] = box
    return assigned


def split_firmware_devices(apps, schema_editor):
    Device = apps.get_model("sauna_data", "FirmwareUpdateDevice")
    PowerDevice = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")
    PanelDevice = apps.get_model("sauna_data", "ControlPanelFirmwareDevice")
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    power_rows = list(Device.objects.filter(kind="POWER_BOX"))
    assigned = _power_box_for_devices(power_rows, list(PowerBox.objects.all()))
    PowerDevice.objects.bulk_create(
        [
            PowerDevice(
                name=device.name,
                power_box=assigned[device.pk],
                note=device.note,
                created_at=device.created_at,
                updated_at=device.updated_at,
            )
            for device in power_rows
        ]
    )
    PanelDevice.objects.bulk_create(
        [
            PanelDevice(
                name=device.name,
                control_panel_id=device.control_panel_id,
                note=device.note,
                created_at=device.created_at,
                updated_at=device.updated_at,
            )
            for device in Device.objects.filter(kind="CONTROL_PANEL")
        ]
    )


def merge_firmware_devices(apps, schema_editor):
    Device = apps.get_model("sauna_data", "FirmwareUpdateDevice")
    PowerDevice = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")
    PanelDevice = apps.get_model("sauna_data", "ControlPanelFirmwareDevice")
    Device.objects.bulk_create(
        [
            Device(
                name=device.name,
                kind="POWER_BOX",
                note=device.note,
                created_at=device.created_at,
                updated_at=device.updated_at,
            )
            for device in PowerDevice.objects.all()
        ]
    )
    Device.objects.bulk_create(
        [
            Device(
                name=device.name,
                kind="CONTROL_PANEL",
                control_panel_id=device.control_panel_id,
                note=device.note,
                created_at=device.created_at,
                updated_at=device.updated_at,
            )
            for device in PanelDevice.objects.all()
        ]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0035_product_items_and_qc_records"),
    ]

    operations = [
        migrations.CreateModel(
            name="PowerBoxFirmwareDevice",
            fields=[
                (
                    "power_box_firmware_device_id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=64, unique=True)),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "power_box",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="firmware_devices",
                        to="sauna_data.powerbox",
                    ),
                ),
            ],
            options={
                "verbose_name": "power box firmware device",
                "verbose_name_plural": "power box firmware devices",
                "db_table": "power_box_firmware_devices",
                "ordering": ("power_box_firmware_device_id",),
            },
        ),
        migrations.CreateModel(
            name="ControlPanelFirmwareDevice",
            fields=[
                (
                    "control_panel_firmware_device_id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=64, unique=True)),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "control_panel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="firmware_devices",
                        to="sauna_data.controlpanel",
                    ),
                ),
            ],
            options={
                "verbose_name": "control panel firmware device",
                "verbose_name_plural": "control panel firmware devices",
                "db_table": "control_panel_firmware_devices",
                "ordering": ("control_panel_firmware_device_id",),
            },
        ),
        migrations.RunPython(split_firmware_devices, merge_firmware_devices),
        migrations.DeleteModel(name="FirmwareUpdateDevice"),
    ]
