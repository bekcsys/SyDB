from django.db import migrations, models

from sauna_data.power_boxes import assign_smmak_power_boxes


def assign_smmak(apps, schema_editor):
    assign_smmak_power_boxes(
        apps.get_model("sauna_data", "PowerBox"),
        apps.get_model("sauna_data", "Product"),
    )


def move_smmak_units_back(apps, schema_editor):
    PowerBox = apps.get_model("sauna_data", "PowerBox")
    Product = apps.get_model("sauna_data", "Product")
    v10 = PowerBox.objects.filter(name="SmMak_v1.0").first()
    if v10 is None:
        return
    Product.objects.filter(
        item_no__in=(
            "310103-01C",
            "310103-02C",
            "310104-02",
            "310103-03C",
            "310103-04C",
            "310103-06C",
        )
    ).update(power_box_id=v10.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0041_product_item_no_not_unique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="powerbox",
            name="name",
            field=models.CharField(
                help_text=(
                    "SmartMak 110 V units use SmMak_v1.0 "
                    "(item numbers 310103-01C, 310103-02C, 310104-02). "
                    "SmartMak 220 V units use SmMak_v1.1 "
                    "(item numbers 310103-03C, 310103-04C, 310103-06C)."
                ),
                max_length=64,
                unique=True,
            ),
        ),
        migrations.RunPython(assign_smmak, move_smmak_units_back),
    ]
