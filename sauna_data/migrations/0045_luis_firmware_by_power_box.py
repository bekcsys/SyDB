from django.db import migrations

from sauna_data.power_boxes import link_luis_acd2


def assign_luis_firmware(apps, schema_editor):
    link_luis_acd2(
        apps.get_model("sauna_data", "PowerBox"),
        apps.get_model("sauna_data", "PowerBoxFirmwareDevice"),
        apps.get_model("sauna_data", "PowerBoxFirmwareDeviceAssignment"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0044_unify_smmak_and_link_luis_acd2"),
    ]

    operations = [
        migrations.RunPython(assign_luis_firmware, migrations.RunPython.noop),
    ]
