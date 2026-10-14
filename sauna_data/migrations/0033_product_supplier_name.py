from django.db import migrations, models


def copy_supplier_names(apps, schema_editor):
    Product = apps.get_model("sauna_data", "Product")
    for product in Product.objects.select_related("supplier"):
        product.supplier_name = product.supplier.name if product.supplier_id else ""
        product.save(update_fields=["supplier_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0032_control_panel_remove_supplier"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="supplier_name",
            field=models.CharField(default="", max_length=64),
        ),
        migrations.RunPython(copy_supplier_names, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="product",
            name="supplier",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="supplier_name",
            new_name="supplier",
        ),
        migrations.AlterField(
            model_name="product",
            name="supplier",
            field=models.CharField(max_length=64),
        ),
        migrations.DeleteModel(
            name="Supplier",
        ),
    ]
