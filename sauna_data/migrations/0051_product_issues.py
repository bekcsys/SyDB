import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0050_product_item_product_nullable"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductIssue",
            fields=[
                ("product_issue_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("NOT_STARTED", "Not Started"),
                            ("IN_PROGRESS", "In Progress"),
                            ("SOLVED", "Solved"),
                        ],
                        default="NOT_STARTED",
                        max_length=16,
                    ),
                ),
                ("documentation", models.BinaryField(blank=True, editable=False, null=True)),
                ("documentation_name", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="issues",
                        to="sauna_data.product",
                    ),
                ),
            ],
            options={
                "db_table": "product_issues",
                "ordering": ("-date", "-product_issue_id"),
            },
        ),
        migrations.AddConstraint(
            model_name="productissue",
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=["NOT_STARTED", "IN_PROGRESS", "SOLVED"]),
                name="product_issues_status_valid",
            ),
        ),
        migrations.AddIndex(
            model_name="productissue",
            index=models.Index(fields=["product", "status"], name="idx_product_issues_status"),
        ),
        migrations.AddIndex(
            model_name="productissue",
            index=models.Index(fields=["-date"], name="idx_product_issues_date"),
        ),
    ]
