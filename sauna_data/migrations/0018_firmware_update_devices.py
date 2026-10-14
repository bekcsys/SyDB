from django.db import migrations, models

FIRMWARE_UPDATE_DEVICE_NAMES = (
    "Royal-Device(iMQ)",
    "Luis-Devices(ACD2, ACD3)",
    "Wang-Device1",
    "Wang-Device2",
    "Li-Device",
)


def create_firmware_update_devices(apps, schema_editor):
    Device = apps.get_model("sauna_data", "FirmwareUpdateDevice")
    Device.objects.bulk_create(Device(name=name) for name in FIRMWARE_UPDATE_DEVICE_NAMES)


def delete_firmware_update_devices(apps, schema_editor):
    apps.get_model("sauna_data", "FirmwareUpdateDevice").objects.filter(
        name__in=FIRMWARE_UPDATE_DEVICE_NAMES
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0017_control_panel_note"),
    ]

    operations = [
        migrations.CreateModel(
            name="FirmwareUpdateDevice",
            fields=[
                ("firmware_update_device_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "firmware update device",
                "verbose_name_plural": "firmware update devices",
                "db_table": "firmware_update_devices",
                "ordering": ("firmware_update_device_id",),
            },
        ),
        migrations.RunPython(create_firmware_update_devices, delete_firmware_update_devices),
    ]
