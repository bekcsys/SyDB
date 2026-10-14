from django.db import migrations, models


def set_plug_types(apps, schema_editor):
    Product = apps.get_model("sauna_data", "Product")
    Product.objects.filter(voltage=110).update(plug_type="NEMA 5-20P")
    Product.objects.filter(voltage=220).update(plug_type="L6-20P")


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0012_product_number_of_cords"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="plug_type",
            field=models.CharField(
                blank=True,
                choices=[("NEMA 5-20P", "NEMA 5-20P"), ("L6-20P", "L6-20P")],
                default="",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="watt_on_label",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(set_plug_types, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(plug_type__in=["", "NEMA 5-20P", "L6-20P"]),
                name="products_plug_type_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(watt_on_label__isnull=True) | models.Q(watt_on_label__gt=0),
                name="products_watt_on_label_positive",
            ),
        ),
    ]
