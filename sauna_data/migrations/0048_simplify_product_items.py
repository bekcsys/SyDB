from pathlib import Path

from django.conf import settings
from django.db import migrations, models


def _form_filename(uploads) -> str:
    if not isinstance(uploads, dict):
        return ""
    entry = uploads.get("form")
    if not isinstance(entry, dict):
        return ""
    files = entry.get("files")
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict):
                name = item.get("stored_name") or item.get("file_name") or ""
                if name:
                    return name
    return entry.get("stored_name") or entry.get("file_name") or ""


def fold_qc_onto_items(apps, schema_editor):
    Item = apps.get_model("sauna_data", "ProductItem")
    Record = apps.get_model("sauna_data", "QcRecord")
    media_root = Path(settings.MEDIA_ROOT)
    for item in Item.objects.all():
        record = Record.objects.filter(product_item_id=item.pk).first()
        if record is None:
            item.save()
            continue
        item.qc_status = record.qc_status or "ASSIGNED"
        item.note = record.notes or ""
        if record.qc_tester_id:
            tester = record.qc_tester
            item.qc_tester_name = tester.name if tester is not None else ""
        filename = _form_filename(record.qc_uploads)
        if filename:
            path = media_root / f"unit-{item.pk}" / "form" / filename
            if path.is_file():
                item.qc_form = path.read_bytes()
                item.qc_form_name = filename
            else:
                item.qc_form_name = filename
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ("sauna_data", "0047_fold_firmware_into_parents"),
    ]

    operations = [
        migrations.AddField(
            model_name="productitem",
            name="qc_tester_name",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="QC tester name"),
        ),
        migrations.AddField(
            model_name="productitem",
            name="qc_status",
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
                verbose_name="QC status",
            ),
        ),
        migrations.AddField(
            model_name="productitem",
            name="qc_form",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="productitem",
            name="qc_form_name",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="QC form"),
        ),
        migrations.AddField(
            model_name="productitem",
            name="note",
            field=models.TextField(blank=True, default="", verbose_name="Note"),
        ),
        migrations.RunPython(fold_qc_onto_items, migrations.RunPython.noop),
        migrations.RemoveField(model_name="productitem", name="revised_serial_no"),
        migrations.RemoveField(model_name="productitem", name="product"),
        migrations.RemoveField(model_name="productitem", name="item_no"),
        migrations.RemoveField(model_name="productitem", name="product_name"),
        migrations.RemoveField(model_name="productitem", name="order_no"),
        migrations.RemoveField(model_name="productitem", name="po_date"),
        migrations.RemoveField(model_name="productitem", name="proforma"),
        migrations.RemoveField(model_name="productitem", name="date_received"),
        migrations.RemoveField(model_name="productitem", name="container_batch"),
        migrations.RemoveField(model_name="productitem", name="shipped_to"),
        migrations.RemoveField(model_name="productitem", name="created_at"),
        migrations.RemoveField(model_name="productitem", name="updated_at"),
        migrations.AddConstraint(
            model_name="productitem",
            constraint=models.CheckConstraint(
                condition=models.Q(qc_status__in=["ASSIGNED", "TESTING", "QC_PASSED", "QC_FAILED", "ON_HOLD"]),
                name="product_items_qc_status_valid",
            ),
        ),
        migrations.AddIndex(
            model_name="productitem",
            index=models.Index(fields=["qc_status"], name="idx_product_items_qc_status"),
        ),
        migrations.DeleteModel(name="QcRecord"),
        migrations.DeleteModel(name="QcTester"),
    ]
