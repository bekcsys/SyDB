from django.db import migrations, models


def copy_power_box_firmware_files(apps, schema_editor):
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    Device = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")
    for box in PowerBox.objects.all().iterator():
        Device.objects.filter(power_box_id=box.pk).update(
            instruction=box.firmware_instruction,
            instruction_name=box.firmware_instruction_name,
            instruction_2=box.firmware_instruction_2,
            instruction_2_name=box.firmware_instruction_2_name,
        )


def restore_power_box_firmware_files(apps, schema_editor):
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    Device = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")
    for box in PowerBox.objects.all().iterator():
        device = (
            Device.objects.filter(power_box_id=box.pk)
            .order_by("power_box_firmware_device_id")
            .first()
        )
        if device is None:
            continue
        PowerBox.objects.filter(pk=box.pk).update(
            firmware_instruction=device.instruction,
            firmware_instruction_name=device.instruction_name,
            firmware_instruction_2=device.instruction_2,
            firmware_instruction_2_name=device.instruction_2_name,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0036_split_firmware_devices"),
    ]

    operations = [
        migrations.AddField(
            model_name="powerboxfirmwaredevice",
            name="instruction",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerboxfirmwaredevice",
            name="instruction_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="powerboxfirmwaredevice",
            name="instruction_2",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerboxfirmwaredevice",
            name="instruction_2_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(copy_power_box_firmware_files, restore_power_box_firmware_files),
        migrations.RemoveField(
            model_name="powerbox",
            name="firmware_instruction",
        ),
        migrations.RemoveField(
            model_name="powerbox",
            name="firmware_instruction_name",
        ),
        migrations.RemoveField(
            model_name="powerbox",
            name="firmware_instruction_2",
        ),
        migrations.RemoveField(
            model_name="powerbox",
            name="firmware_instruction_2_name",
        ),
    ]
