#!/usr/bin/env python3
"""Scan data/import_pending/ and import product test CSV files into PostgreSQL."""

import argparse
import os
import sys
from pathlib import Path

WEBAPP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEBAPP_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings

from sauna_data.services.csv_import import ImportMetadata, scan_and_import_pending


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pending-dir",
        type=Path,
        default=settings.IMPORT_PENDING_DIR,
        help="Directory containing CSV files to import",
    )
    parser.add_argument("--model-name", type=str, default="")
    parser.add_argument("--serial-number", type=str, default="")
    parser.add_argument("--tester-name", type=str, default="")
    args = parser.parse_args()

    metadata = None
    if args.model_name and args.serial_number:
        metadata = ImportMetadata(
            model_name=args.model_name,
            serial_number=args.serial_number,
            tester_name=args.tester_name,
        )

    summaries = scan_and_import_pending(args.pending_dir, metadata=metadata)
    if not summaries:
        print("No CSV files found.")
        return 0

    exit_code = 0
    for summary in summaries:
        print(f"\n=== {summary.file_name} ===")
        print(f"status: {summary.status}")
        if summary.test_run_id:
            print(f"TestID: {summary.test_run_id}")
        print(f"rows_imported: {summary.rows_imported}")
        print(f"sensors_detected: {summary.sensors_detected}")
        for label, temp in summary.max_temp_by_sensor.items():
            print(f"max_temp[{label}]: {temp} F")
        if summary.archive_path:
            print(f"archive_path: {summary.archive_path}")
        print(f"duration_seconds: {summary.duration_seconds:.2f}")
        if summary.error_message:
            print(f"error: {summary.error_message}")
            exit_code = 1
        if summary.status == "failed":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
