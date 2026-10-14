from django.db import migrations, models


QC_STATUSES = ["ASSIGNED", "TESTING", "QC_PASSED", "QC_FAILED", "ON_HOLD"]


def remap_unit_statuses(apps, schema_editor) -> None:
    PhysicalUnit = apps.get_model("sauna_data", "PhysicalUnit")
    PhysicalUnit.objects.filter(unit_status__in=["IN_STOCK", "SETUP"]).update(
        unit_status="ASSIGNED"
    )
    PhysicalUnit.objects.filter(unit_status__in=["READY_TO_SHIP", "SHIPPED"]).update(
        unit_status="QC_PASSED"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0008_qc_tester_and_approval"),
    ]

    operations = [
        migrations.RunPython(remap_unit_statuses, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="physicalunit",
            name="physical_units_status_valid",
        ),
        migrations.AlterField(
            model_name="physicalunit",
            name="unit_status",
            field=models.CharField(
                choices=[
                    ("ASSIGNED", "Assigned"),
                    ("TESTING", "Testing"),
                    ("QC_PASSED", "QC passed"),
                    ("QC_FAILED", "QC failed"),
                    ("ON_HOLD", "On hold"),
                ],
                default="ASSIGNED",
                max_length=32,
            ),
        ),
        migrations.AddConstraint(
            model_name="physicalunit",
            constraint=models.CheckConstraint(
                condition=models.Q(unit_status__in=QC_STATUSES),
                name="physical_units_status_valid",
            ),
        ),
    ]
