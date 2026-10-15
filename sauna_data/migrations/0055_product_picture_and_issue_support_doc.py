from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sauna_data", "0054_product_issue_doc_ref"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="picture",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="picture_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="productissue",
            name="support_doc",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="productissue",
            name="support_doc_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
