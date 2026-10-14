import csv
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from time import perf_counter
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from sauna_data.models import (
    ImportLog,
    ProductModel,
    ProductUnit,
    Sensor,
    SensorReading,
    TestRun,
)

REQUIRED_CSV_COLUMNS = [
    "timestamp",
    "elapsed_time_in_Min",
    "Timer_in_Min",
    "sensor_id",
    "sensor_label",
    "temperature_c",
    "temperature_f",
]

FILENAME_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{3,4}(?:AM|PM))_(?P<model>.+)_(?P<serial>.+)\.csv$",
    re.IGNORECASE,
)


@dataclass
class ImportMetadata:
    model_name: str
    serial_number: str
    test_date: datetime | None = None
    tester_name: str = ""
    supply_voltage: Decimal | None = None
    total_amp_draw_start: Decimal | None = None
    run_duration_min: int = 90
    target_temperature_f: Decimal = Decimal("150")
    test_location: str = ""
    notes: str = ""


@dataclass
class ImportSummary:
    file_name: str
    status: str
    test_run_id: int | None = None
    rows_imported: int = 0
    sensors_detected: int = 0
    max_temp_by_sensor: dict[str, float] = field(default_factory=dict)
    reading_time_min: datetime | None = None
    reading_time_max: datetime | None = None
    archive_path: str = ""
    duration_seconds: float = 0.0
    error_message: str = ""
    skipped_duplicate: bool = False


def parse_filename_metadata(file_name: str) -> tuple[str, str, datetime | None]:
    match = FILENAME_PATTERN.match(file_name)
    if not match:
        return "", "", None
    date_part = match.group("date")
    time_part = match.group("time").upper()
    model_name = match.group("model")
    serial_number = match.group("serial")
    try:
        test_date = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %I%M%p")
        if timezone.is_aware(test_date):
            return model_name, serial_number, test_date
        return model_name, serial_number, timezone.make_aware(test_date)
    except ValueError:
        return model_name, serial_number, None


def load_metadata_sidecar(csv_path: Path) -> dict[str, Any]:
    sidecar = csv_path.with_suffix(".meta.json")
    if not sidecar.exists():
        return {}
    import json

    with sidecar.open(encoding="utf-8") as handle:
        return json.load(handle)


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def build_metadata(csv_path: Path, overrides: ImportMetadata | None = None) -> ImportMetadata:
    file_name = csv_path.name
    model_from_name, serial_from_name, test_date_from_name = parse_filename_metadata(
        file_name
    )
    sidecar = load_metadata_sidecar(csv_path)

    model_name = (
        (overrides.model_name if overrides else "")
        or sidecar.get("model_name", "")
        or model_from_name
    )
    serial_number = (
        (overrides.serial_number if overrides else "")
        or sidecar.get("serial_number", "")
        or serial_from_name
    )
    if not model_name or not serial_number:
        raise ValueError(
            "model_name and serial_number are required. "
            "Provide via import form, .meta.json sidecar, or filename pattern "
            "YYYY-MM-DD_HHMMAM_ModelName_Serial.csv"
        )

    test_date_raw = sidecar.get("test_date")
    test_date = overrides.test_date if overrides and overrides.test_date else test_date_from_name
    if test_date_raw and not test_date:
        test_date = datetime.fromisoformat(str(test_date_raw))
        if timezone.is_naive(test_date):
            test_date = timezone.make_aware(test_date)

    return ImportMetadata(
        model_name=model_name,
        serial_number=serial_number,
        test_date=test_date,
        tester_name=(
            (overrides.tester_name if overrides else "")
            or sidecar.get("tester_name", "")
            or getattr(settings, "DEFAULT_TESTER_NAME", "")
        ),
        supply_voltage=_decimal_or_none(
            str(
                (overrides.supply_voltage if overrides and overrides.supply_voltage else None)
                or sidecar.get("supply_voltage")
                or ""
            )
        ),
        total_amp_draw_start=_decimal_or_none(
            str(
                (
                    overrides.total_amp_draw_start
                    if overrides and overrides.total_amp_draw_start
                    else None
                )
                or sidecar.get("total_amp_draw_start")
                or ""
            )
        ),
        run_duration_min=int(
            (overrides.run_duration_min if overrides else None)
            or sidecar.get("run_duration_min", settings.DEFAULT_RUN_DURATION_MIN)
        ),
        target_temperature_f=_decimal_or_none(
            str(
                (overrides.target_temperature_f if overrides else None)
                or sidecar.get("target_temperature_f", settings.DEFAULT_TARGET_TEMPERATURE_F)
            )
        )
        or Decimal(str(settings.DEFAULT_TARGET_TEMPERATURE_F)),
        test_location=(
            (overrides.test_location if overrides else "")
            or sidecar.get("test_location", "")
        ),
        notes=(overrides.notes if overrides else "") or sidecar.get("notes", ""),
    )


def validate_csv_structure(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV file has no header row")
        missing = [col for col in REQUIRED_CSV_COLUMNS if col not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("CSV file contains no data rows")
    return rows


def _parse_reading_time(value: str) -> datetime:
    parsed = datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


def _archive_path(dest_dir: Path, file_name: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / file_name
    if not target.exists():
        return target
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    return dest_dir / f"{stem}_{stamp}{suffix}"


def duplicate_already_imported(file_name: str) -> bool:
    return ImportLog.objects.filter(file_name=file_name, status=ImportLog.STATUS_SUCCESS).exists()


def _import_csv_rows(
    csv_path: Path,
    meta: ImportMetadata,
    rows: list[dict[str, str]],
) -> tuple[TestRun, list[SensorReading], dict[str, float], datetime | None, datetime | None, dict[str, Sensor]]:
    with transaction.atomic():
        product_model, _ = ProductModel.objects.get_or_create(model_name=meta.model_name)
        product_unit, _ = ProductUnit.objects.get_or_create(
            serial_number=meta.serial_number,
            defaults={"model": product_model},
        )
        if product_unit.model_id != product_model.model_id:
            product_unit.model = product_model
            product_unit.save(update_fields=["model"])

        first_timestamp = _parse_reading_time(rows[0]["timestamp"])
        test_date = meta.test_date or first_timestamp

        test_run = TestRun.objects.create(
            unit=product_unit,
            test_date=test_date,
            tester_name=meta.tester_name,
            supply_voltage=meta.supply_voltage,
            total_amp_draw_start=meta.total_amp_draw_start,
            run_duration_min=meta.run_duration_min,
            target_temperature_f=meta.target_temperature_f,
            test_location=meta.test_location,
            notes=meta.notes,
        )

        sensor_cache: dict[str, Sensor] = {}
        readings: list[SensorReading] = []
        max_temp: dict[str, float] = {}
        reading_min: datetime | None = None
        reading_max: datetime | None = None

        for row in rows:
            serial = row["sensor_id"].strip()
            label = row["sensor_label"].strip()
            if serial not in sensor_cache:
                sensor_obj, _ = Sensor.objects.get_or_create(
                    sensor_serial=serial,
                    defaults={"sensor_label": label},
                )
                if label and sensor_obj.sensor_label != label:
                    sensor_obj.sensor_label = label
                    sensor_obj.save(update_fields=["sensor_label"])
                sensor_cache[serial] = sensor_obj

            reading_time = _parse_reading_time(row["timestamp"])
            if reading_min is None or reading_time < reading_min:
                reading_min = reading_time
            if reading_max is None or reading_time > reading_max:
                reading_max = reading_time

            temp_f = float(row["temperature_f"])
            label_key = label or serial
            max_temp[label_key] = max(max_temp.get(label_key, temp_f), temp_f)

            readings.append(
                SensorReading(
                    test_run=test_run,
                    sensor=sensor_cache[serial],
                    reading_time=reading_time,
                    elapsed_time_min=int(row["elapsed_time_in_Min"]),
                    timer_remaining_min=int(row["Timer_in_Min"]),
                    temperature_c=Decimal(str(row["temperature_c"])),
                    temperature_f=Decimal(str(row["temperature_f"])),
                )
            )

        SensorReading.objects.bulk_create(readings, batch_size=2000)
        return test_run, readings, max_temp, reading_min, reading_max, sensor_cache


def import_csv_file(
    csv_path: Path,
    *,
    metadata: ImportMetadata | None = None,
    archive_on_success: bool = True,
    archive_on_failure: bool = True,
) -> ImportSummary:
    started = perf_counter()
    file_name = csv_path.name
    summary = ImportSummary(file_name=file_name, status=ImportLog.STATUS_PENDING)

    if duplicate_already_imported(file_name):
        ImportLog.objects.create(
            file_name=file_name,
            original_file_path=str(csv_path),
            status=ImportLog.STATUS_SKIPPED,
            error_message="File already imported successfully; duplicate skipped.",
            completed_at=timezone.now(),
        )
        summary.status = ImportLog.STATUS_SKIPPED
        summary.skipped_duplicate = True
        summary.error_message = "Duplicate import skipped."
        summary.duration_seconds = perf_counter() - started
        return summary

    log_entry = ImportLog.objects.create(
        file_name=file_name,
        original_file_path=str(csv_path),
        status=ImportLog.STATUS_PENDING,
    )

    try:
        meta = build_metadata(csv_path, metadata)
        rows = validate_csv_structure(csv_path)
        test_run, readings, max_temp, reading_min, reading_max, sensor_cache = _import_csv_rows(
            csv_path, meta, rows
        )

        archive_dest = ""
        if archive_on_success:
            archived = _archive_path(settings.ARCHIVE_MIGRATED_DIR, file_name)
            shutil.move(str(csv_path), archived)
            archive_dest = str(archived)

        log_entry.test_run = test_run
        log_entry.status = ImportLog.STATUS_SUCCESS
        log_entry.rows_imported = len(readings)
        log_entry.sensors_detected = len(sensor_cache)
        log_entry.archived_file_path = archive_dest
        log_entry.completed_at = timezone.now()
        log_entry.save()

        summary.status = ImportLog.STATUS_SUCCESS
        summary.test_run_id = test_run.test_run_id
        summary.rows_imported = len(readings)
        summary.sensors_detected = len(sensor_cache)
        summary.max_temp_by_sensor = max_temp
        summary.reading_time_min = reading_min
        summary.reading_time_max = reading_max
        summary.archive_path = archive_dest
    except Exception as exc:
        log_entry.status = ImportLog.STATUS_FAILED
        log_entry.error_message = str(exc)
        log_entry.completed_at = timezone.now()
        log_entry.save()

        if archive_on_failure and csv_path.exists():
            failed_path = _archive_path(settings.ARCHIVE_FAILED_DIR, file_name)
            shutil.move(str(csv_path), failed_path)
            log_entry.archived_file_path = str(failed_path)
            log_entry.save(update_fields=["archived_file_path"])
            summary.archive_path = str(failed_path)

        summary.status = ImportLog.STATUS_FAILED
        summary.error_message = str(exc)
    finally:
        summary.duration_seconds = perf_counter() - started

    return summary


def scan_and_import_pending(
    pending_dir: Path | None = None,
    metadata: ImportMetadata | None = None,
) -> list[ImportSummary]:
    directory = pending_dir or settings.IMPORT_PENDING_DIR
    directory.mkdir(parents=True, exist_ok=True)
    summaries: list[ImportSummary] = []
    for csv_path in sorted(directory.glob("*.csv")):
        summaries.append(import_csv_file(csv_path, metadata=metadata))
    return summaries
