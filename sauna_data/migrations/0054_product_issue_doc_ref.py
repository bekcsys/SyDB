from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sauna_data", "0053_product_issue_note"),
    ]

    operations = [
        migrations.AddField(
            model_name="productissue",
            name="doc_ref",
            field=models.CharField(blank=True, default="", max_length=80, verbose_name="Doc"),
        ),
    ]
