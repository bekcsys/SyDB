from django.db import migrations, models

from sauna_data.power_boxes import assign_smmak_power_boxes, link_luis_acd2


def unify_smmak_and_link_luis_firmware(apps, schema_editor):
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    Product = apps.get_model("sauna_data", "Product")
    Device = apps.get_model("sauna_data", "PowerBoxFirmwareDevice")
    Assignment = apps.get_model("sauna_data", "PowerBoxFirmwareDeviceAssignment")
    assign_smmak_power_boxes(PowerBox, Product, Assignment)
    link_luis_acd2(PowerBox, Device, Assignment)


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0043_power_box_note"),
    ]

    operations = [
        migrations.AlterField(
            model_name="powerbox",
            name="name",
            field=models.CharField(
                help_text=(
                    "SmartMak units use SmMak_v1.0 "
                    "(item numbers 310103-01C, 310103-02C, 310104-02, "
                    "310103-03C, 310103-04C, 310103-06C)."
                ),
                max_length=64,
                unique=True,
            ),
        ),
        migrations.RunPython(unify_smmak_and_link_luis_firmware, migrations.RunPython.noop),
    ]
