from django.db import migrations, models


_DEVICE_LABELS = {
    "RFR_EVR1 140F to 150F re-calibration.pdf": "E-PGM+",
    "wang CS-CP Unlock device.pdf": "Wang CP Unlock Device",
    "Luis-ACD2": "ACD 2",
    "Luis-ACD3": "ACD 3",
    "Wang Unlocker": "Wang CP Unlock Device",
}
_VIDEO_SUFFIXES = (".mp4", ".mov", ".m4v", ".webm")


def _label(name: str) -> str:
    return _DEVICE_LABELS.get(name, name)


def _is_video(filename: str) -> bool:
    return filename.lower().endswith(_VIDEO_SUFFIXES)


def fold_firmware(apps, schema_editor):
    Panel = apps.get_model("sauna_data", "ControlPanel")
    PanelDevice = apps.get_model("sauna_data", "ControlPanelFirmwareDevice")
    Box = apps.get_model("sauna_data", "PowerBox")
    BoxDevice = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")

    for panel in Panel.objects.all():
        names = [
            _label(name)
            for name in PanelDevice.objects.filter(control_panel_id=panel.pk).values_list("name", flat=True)
        ]
        panel.firmware_device = ", ".join(names)
        extras = []
        for content_field, name_field in (
            ("instruction_3", "instruction_3_name"),
            ("panel_update", "panel_update_name"),
            ("panel_update_2", "panel_update_2_name"),
        ):
            filename = getattr(panel, name_field) or ""
            content = getattr(panel, content_field)
            if filename and content is not None:
                extras.append((bytes(content), filename))
        for content, filename in extras:
            stored = {getattr(panel, "documentation_1_name"), getattr(panel, "documentation_2_name")}
            if filename in stored:
                continue
            for content_field, name_field in (
                ("documentation_1", "documentation_1_name"),
                ("documentation_2", "documentation_2_name"),
            ):
                if not getattr(panel, name_field):
                    setattr(panel, content_field, content)
                    setattr(panel, name_field, filename)
                    break
        panel.save()

    for box in Box.objects.all():
        if not box.picture_name:
            for content_field, name_field in (
                ("picture_2", "picture_2_name"),
                ("picture_3", "picture_3_name"),
            ):
                filename = getattr(box, name_field) or ""
                content = getattr(box, content_field)
                if filename and content is not None:
                    box.picture = bytes(content)
                    box.picture_name = filename
                    break
        names = []
        for device in BoxDevice.objects.filter(power_boxes=box.pk).order_by("name"):
            names.append(_label(device.name))
            for content_field, name_field in (
                ("instruction", "instruction_name"),
                ("instruction_2", "instruction_2_name"),
            ):
                filename = getattr(device, name_field) or ""
                content = getattr(device, content_field)
                if not filename or content is None:
                    continue
                if _is_video(filename):
                    if not box.firmware_video_name:
                        box.firmware_video = bytes(content)
                        box.firmware_video_name = filename
                elif not box.firmware_document_name:
                    box.firmware_document = bytes(content)
                    box.firmware_document_name = filename
        box.firmware_info = ", ".join(names)
        box.save()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0045_luis_firmware_by_power_box"),
    ]

    operations = [
        migrations.AddField(
            model_name="controlpanel",
            name="firmware_device",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="Firmware device"),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_info",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="Firmware info"),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_document",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_document_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_video",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="powerbox",
            name="firmware_video_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RenameField(model_name="controlpanel", old_name="instruction", new_name="documentation_1"),
        migrations.RenameField(model_name="controlpanel", old_name="instruction_name", new_name="documentation_1_name"),
        migrations.RenameField(model_name="controlpanel", old_name="instruction_2", new_name="documentation_2"),
        migrations.RenameField(model_name="controlpanel", old_name="instruction_2_name", new_name="documentation_2_name"),
        migrations.RunPython(fold_firmware, migrations.RunPython.noop),
        migrations.RemoveField(model_name="controlpanel", name="instruction_3"),
        migrations.RemoveField(model_name="controlpanel", name="instruction_3_name"),
        migrations.RemoveField(model_name="controlpanel", name="panel_update"),
        migrations.RemoveField(model_name="controlpanel", name="panel_update_name"),
        migrations.RemoveField(model_name="controlpanel", name="panel_update_2"),
        migrations.RemoveField(model_name="controlpanel", name="panel_update_2_name"),
        migrations.RemoveField(model_name="powerbox", name="picture_2"),
        migrations.RemoveField(model_name="powerbox", name="picture_2_name"),
        migrations.RemoveField(model_name="powerbox", name="picture_3"),
        migrations.RemoveField(model_name="powerbox", name="picture_3_name"),
        migrations.DeleteModel(name="PowerBoxFirmwareDeviceAssignment"),
        migrations.DeleteModel(name="PowerBoxFirmwareDevice"),
        migrations.DeleteModel(name="ControlPanelFirmwareDevice"),
    ]
