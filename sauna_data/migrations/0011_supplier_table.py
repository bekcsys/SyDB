from django.db import migrations, models
import django.db.models.deletion


DEFAULT_SUPPLIERS = ("Global", "Royal", "SmartMak")


def link_suppliers(apps, schema_editor):
    Supplier = apps.get_model("sauna_data", "Supplier")
    Product = apps.get_model("sauna_data", "Product")
    by_name = {}
    for name in DEFAULT_SUPPLIERS:
        supplier = Supplier.objects.create(name=name)
        by_name[name.casefold()] = supplier
    fallback = by_name["global"]
    for product in Product.objects.all():
        raw = (product.supplier or "").strip()
        supplier = by_name.get(raw.casefold())
        if supplier is None and raw:
            supplier = Supplier.objects.create(name=raw)
            by_name[raw.casefold()] = supplier
        product.supplier_ref_id = (supplier or fallback).pk
        product.save(update_fields=["supplier_ref"])


def unlink_suppliers(apps, schema_editor):
    Supplier = apps.get_model("sauna_data", "Supplier")
    Product = apps.get_model("sauna_data", "Product")
    names = {row.pk: row.name for row in Supplier.objects.all()}
    for product in Product.objects.all():
        product.supplier = names.get(product.supplier_ref_id, "")
        product.save(update_fields=["supplier"])


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0010_test_completed_timestamp"),
    ]

    operations = [
        migrations.CreateModel(
            name="Supplier",
            fields=[
                ("supplier_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "suppliers",
                "ordering": ("name",),
            },
        ),
        migrations.AddField(
            model_name="product",
            name="supplier_ref",
            field=models.ForeignKey(
                blank=True,
                db_column="supplier_id",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="sauna_data.supplier",
            ),
        ),
        migrations.RunPython(link_suppliers, unlink_suppliers),
        migrations.AlterField(
            model_name="product",
            name="supplier_ref",
            field=models.ForeignKey(
                db_column="supplier_id",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="sauna_data.supplier",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="supplier",
            field=models.CharField(default="", max_length=64),
        ),
        migrations.RemoveField(
            model_name="product",
            name="supplier",
        ),
        migrations.RenameField(
            model_name="product",
            old_name="supplier_ref",
            new_name="supplier",
        ),
    ]
