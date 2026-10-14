from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sauna_data", "0052_product_issue_products"),
    ]

    operations = [
        migrations.AddField(
            model_name="productissue",
            name="note",
            field=models.TextField(blank=True, default=""),
        ),
    ]
