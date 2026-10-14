from django.db import migrations, models


def copy_product_links(apps, schema_editor):
    Issue = apps.get_model("sauna_data", "ProductIssue")
    Through = Issue.products.through
    Through.objects.bulk_create(
        [
            Through(productissue_id=issue.pk, product_id=issue.product_id)
            for issue in Issue.objects.exclude(product_id=None)
        ]
    )


def restore_product_links(apps, schema_editor):
    Issue = apps.get_model("sauna_data", "ProductIssue")
    for issue in Issue.objects.all():
        product_id = issue.products.order_by("product_id").values_list("pk", flat=True).first()
        if product_id is None:
            continue
        issue.product_id = product_id
        issue.save(update_fields=["product_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0051_product_issues"),
    ]

    operations = [
        migrations.AddField(
            model_name="productissue",
            name="products",
            field=models.ManyToManyField(
                db_table="product_issue_products",
                related_name="issue_memberships",
                to="sauna_data.product",
            ),
        ),
        migrations.RunPython(copy_product_links, restore_product_links),
        migrations.RemoveIndex(
            model_name="productissue",
            name="idx_product_issues_status",
        ),
        migrations.RemoveField(
            model_name="productissue",
            name="product",
        ),
        migrations.AlterField(
            model_name="productissue",
            name="products",
            field=models.ManyToManyField(
                db_table="product_issue_products",
                related_name="issues",
                to="sauna_data.product",
            ),
        ),
    ]
