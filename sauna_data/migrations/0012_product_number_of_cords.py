from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0011_supplier_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="number_of_cords",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(number_of_cords__gte=1),
                name="products_number_of_cords_min_1",
            ),
        ),
    ]
