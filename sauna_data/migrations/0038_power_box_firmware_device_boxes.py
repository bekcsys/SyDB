import django.db.models.deletion
from django.db import migrations, models


def link_firmware_devices(apps, schema_editor):
    Device = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    Assignment = apps.get_model("sauna_data", "PowerBoxFirmwareDeviceAssignment")
    for device in Device.objects.all():
        Assignment.objects.get_or_create(
            power_box_firmware_device_id=device.pk,
            power_box_id=device.power_box_id,
        )
    luis_box_ids = list(PowerBox.objects.filter(name__icontains="luis").values_list("pk", flat=True))
    luis_devices = Device.objects.filter(name__icontains="acd") | Device.objects.filter(name__icontains="luis")
    for device in luis_devices.distinct():
        for box_id in luis_box_ids:
            Assignment.objects.get_or_create(
                power_box_firmware_device_id=device.pk,
                power_box_id=box_id,
            )


def restore_single_power_box(apps, schema_editor):
    Device = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")
    Assignment = apps.get_model("sauna_data", "PowerBoxFirmwareDeviceAssignment")
    for device in Device.objects.all():
        link = (
            Assignment.objects.filter(power_box_firmware_device_id=device.pk)
            .order_by("power_box_id")
            .first()
        )
        if link is None:
            continue
        device.power_box_id = link.power_box_id
        device.save(update_fields=["power_box_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0037_power_box_firmware_device_files"),
    ]

    operations = [
        migrations.AlterField(
            model_name="powerboxfirmwaredevice",
            name="power_box",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="legacy_firmware_devices",
                to="sauna_data.powerbox",
            ),
        ),
        migrations.CreateModel(
            name="PowerBoxFirmwareDeviceAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("power_box", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="sauna_data.powerbox")),
                (
                    "power_box_firmware_device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sauna_data.powerboxfirmwaredevice",
                    ),
                ),
            ],
            options={
                "db_table": "power_box_firmware_device_boxes",
            },
        ),
        migrations.AddField(
            model_name="powerboxfirmwaredevice",
            name="power_boxes",
            field=models.ManyToManyField(
                related_name="firmware_devices",
                through="sauna_data.PowerBoxFirmwareDeviceAssignment",
                to="sauna_data.powerbox",
            ),
        ),
        migrations.AddConstraint(
            model_name="powerboxfirmwaredeviceassignment",
            constraint=models.UniqueConstraint(
                fields=("power_box_firmware_device", "power_box"),
                name="power_box_firmware_device_boxes_unique",
            ),
        ),
        migrations.RunPython(link_firmware_devices, restore_single_power_box),
        migrations.RemoveField(
            model_name="powerboxfirmwaredevice",
            name="power_box",
        ),
    ]
