from django.db import migrations, models
import django.db.models.deletion


def seed_qc_testers(apps, schema_editor) -> None:
    QcTester = apps.get_model("sauna_data", "QcTester")
    for name in ("McCoy", "Tyron"):
        QcTester.objects.get_or_create(name=name, defaults={"is_active": True})


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0007_unit_qc_uploads"),
    ]

    operations = [
        migrations.CreateModel(
            name="QcTester",
            fields=[
                ("tester_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "qc_testers",
                "ordering": ("name",),
            },
        ),
        migrations.AddField(
            model_name="physicalunit",
            name="qc_approved",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="physicalunit",
            name="qc_tester",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="units",
                to="sauna_data.qctester",
            ),
        ),
        migrations.RunPython(seed_qc_testers, migrations.RunPython.noop),
    ]
