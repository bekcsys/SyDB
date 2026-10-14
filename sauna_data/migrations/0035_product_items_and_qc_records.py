from django.db import migrations, models
import django.db.models.deletion


def copy_qc_rows(apps, schema_editor):
    Unit = apps.get_model("sauna_data", "PhysicalUnit")
    QcRecord = apps.get_model("sauna_data", "QcRecord")
    QcRecord.objects.bulk_create(
        [
            QcRecord(
                product_item_id=unit.pk,
                qc_status=unit.unit_status,
                date_assigned=unit.date_assigned,
                date_test_started=unit.date_test_started,
                date_test_completed=unit.date_test_completed,
                notes=unit.notes,
                qc_approved=unit.qc_approved,
                qc_tester_id=unit.qc_tester_id,
                qc_report_file_name=unit.qc_report_file_name,
                qc_report_s3_key=unit.qc_report_s3_key,
                qc_report_bucket=unit.qc_report_bucket,
                qc_report_stored_name=unit.qc_report_stored_name,
                qc_pictures=unit.qc_pictures,
                qc_videos=unit.qc_videos,
                qc_uploads=unit.qc_uploads,
                created_at=unit.created_at,
                updated_at=unit.updated_at,
            )
            for unit in Unit.objects.all()
        ]
    )


def blank_order_numbers_to_null(apps, schema_editor):
    Unit = apps.get_model("sauna_data", "PhysicalUnit")
    Unit.objects.filter(order_no="").update(order_no=None)


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0034_control_panel_single_picture"),
    ]

    operations = [
        migrations.CreateModel(
            name="QcRecord",
            fields=[
                ("qc_id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "qc_status",
                    models.CharField(
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
                ("date_assigned", models.DateField(blank=True, null=True)),
                ("date_test_started", models.DateField(blank=True, null=True)),
                ("date_test_completed", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("qc_approved", models.BooleanField(default=False)),
                ("qc_report_file_name", models.CharField(blank=True, default="", max_length=255)),
                ("qc_report_s3_key", models.CharField(blank=True, default="", max_length=512)),
                ("qc_report_bucket", models.CharField(blank=True, default="", max_length=255)),
                ("qc_report_stored_name", models.CharField(blank=True, default="", max_length=255)),
                ("qc_pictures", models.JSONField(blank=True, default=list)),
                ("qc_videos", models.JSONField(blank=True, default=list)),
                ("qc_uploads", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product_item",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="qc",
                        to="sauna_data.physicalunit",
                    ),
                ),
                (
                    "qc_tester",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="qc_records",
                        to="sauna_data.qctester",
                    ),
                ),
            ],
            options={
                "db_table": "qc_records",
            },
        ),
        migrations.AddConstraint(
            model_name="qcrecord",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    qc_status__in=["ASSIGNED", "TESTING", "QC_PASSED", "QC_FAILED", "ON_HOLD"]
                ),
                name="qc_records_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="qcrecord",
            constraint=models.CheckConstraint(
                condition=models.Q(date_test_completed__isnull=True)
                | models.Q(date_test_started__isnull=True)
                | models.Q(date_test_completed__date__gte=models.F("date_test_started")),
                name="qc_records_test_dates_ok",
            ),
        ),
        migrations.AddIndex(
            model_name="qcrecord",
            index=models.Index(fields=["qc_status"], name="idx_qc_records_status"),
        ),
        migrations.RunPython(copy_qc_rows, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="physicalunit",
            name="physical_units_status_valid",
        ),
        migrations.RemoveConstraint(
            model_name="physicalunit",
            name="physical_units_test_dates_ok",
        ),
        migrations.RemoveConstraint(
            model_name="physicalunit",
            name="physical_units_ship_date_ok",
        ),
        migrations.RemoveIndex(
            model_name="physicalunit",
            name="idx_physical_units_status",
        ),
        migrations.RemoveField(model_name="physicalunit", name="customer_no"),
        migrations.RemoveField(model_name="physicalunit", name="order_date"),
        migrations.RemoveField(model_name="physicalunit", name="unit_status"),
        migrations.RemoveField(model_name="physicalunit", name="date_assigned"),
        migrations.RemoveField(model_name="physicalunit", name="date_test_started"),
        migrations.RemoveField(model_name="physicalunit", name="date_test_completed"),
        migrations.RemoveField(model_name="physicalunit", name="ship_date"),
        migrations.RemoveField(model_name="physicalunit", name="location"),
        migrations.RemoveField(model_name="physicalunit", name="notes"),
        migrations.RemoveField(model_name="physicalunit", name="qc_approved"),
        migrations.RemoveField(model_name="physicalunit", name="qc_tester"),
        migrations.RemoveField(model_name="physicalunit", name="qc_report_file_name"),
        migrations.RemoveField(model_name="physicalunit", name="qc_report_s3_key"),
        migrations.RemoveField(model_name="physicalunit", name="qc_report_bucket"),
        migrations.RemoveField(model_name="physicalunit", name="qc_report_stored_name"),
        migrations.RemoveField(model_name="physicalunit", name="qc_pictures"),
        migrations.RemoveField(model_name="physicalunit", name="qc_videos"),
        migrations.RemoveField(model_name="physicalunit", name="qc_uploads"),
        migrations.AddField(
            model_name="physicalunit",
            name="container_batch",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AlterField(
            model_name="physicalunit",
            name="order_no",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.RunPython(blank_order_numbers_to_null, migrations.RunPython.noop),
        migrations.RenameField(
            model_name="physicalunit",
            old_name="unit_id",
            new_name="product_item_id",
        ),
        migrations.RenameField(
            model_name="physicalunit",
            old_name="item_serial_no",
            new_name="serial_no",
        ),
        migrations.RenameModel(
            old_name="PhysicalUnit",
            new_name="ProductItem",
        ),
        migrations.AlterModelTable(
            name="productitem",
            table="product_items",
        ),
        migrations.AlterField(
            model_name="productitem",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="product_items",
                to="sauna_data.product",
            ),
        ),
    ]
