from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from sauna_data.services.csv_import import scan_and_import_pending


class Command(BaseCommand):
    help = "Import all CSV files from data/import_pending/ into PostgreSQL."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--pending-dir",
            type=str,
            default="",
            help="Override import pending directory",
        )

    def handle(self, *args, **options) -> None:
        pending_dir = (
            Path(options["pending_dir"])
            if options["pending_dir"]
            else settings.IMPORT_PENDING_DIR
        )
        summaries = scan_and_import_pending(pending_dir)
        if not summaries:
            self.stdout.write(self.style.WARNING("No CSV files found in import_pending."))
            return

        for summary in summaries:
            self.stdout.write(f"File: {summary.file_name}")
            self.stdout.write(f"  Status: {summary.status}")
            if summary.test_run_id:
                self.stdout.write(f"  TestID: {summary.test_run_id}")
            self.stdout.write(f"  Rows imported: {summary.rows_imported}")
            self.stdout.write(f"  Sensors detected: {summary.sensors_detected}")
            if summary.max_temp_by_sensor:
                for label, temp in summary.max_temp_by_sensor.items():
                    self.stdout.write(f"  Max {label}: {temp} F")
            if summary.reading_time_min and summary.reading_time_max:
                self.stdout.write(
                    f"  Reading range: {summary.reading_time_min} -> {summary.reading_time_max}"
                )
            if summary.archive_path:
                self.stdout.write(f"  Archive: {summary.archive_path}")
            self.stdout.write(f"  Duration: {summary.duration_seconds:.2f}s")
            if summary.error_message:
                self.stdout.write(self.style.ERROR(f"  Error: {summary.error_message}"))
