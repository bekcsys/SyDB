import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")
_UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")

QC_UPLOAD_SLOTS = (
    ("form", "Form", ".pdf,application/pdf"),
    ("video", "Video", "video/*"),
    ("front", "Front", "image/*"),
    ("back", "Back", "image/*"),
    ("left", "Left", "image/*"),
    ("right", "Right", "image/*"),
    ("top", "Top", "image/*"),
    ("inside_front", "Inside Front (door view)", "image/*"),
    ("inside_left", "Inside left", "image/*"),
    ("inside_right", "Inside right", "image/*"),
    ("inside_back", "Inside back (wall)", "image/*"),
    ("inside_floor", "Inside floor", "image/*"),
    ("inside_ceiling", "Inside ceiling", "image/*"),
)

QC_SLOT_KEYS = tuple(key for key, _label, _accept in QC_UPLOAD_SLOTS)


def slot_object_kind(slot: str) -> str:
    if slot == "form":
        return "report"
    if slot == "video":
        return "video"
    return "picture"


def slot_allows_multiple(slot: str) -> bool:
    return slot != "form"


def slot_max_files(slot: str) -> int | None:
    if slot_object_kind(slot) == "picture":
        return 5
    if slot == "form":
        return 1
    return None


def slot_file_items(entry: dict | None) -> list[dict]:
    if not isinstance(entry, dict):
        return []
    files = entry.get("files")
    if isinstance(files, list):
        return [item for item in files if isinstance(item, dict) and item.get("file_name")]
    if entry.get("file_name"):
        return [entry]
    return []


def slot_has_upload(entry: dict | None) -> bool:
    return bool(slot_file_items(entry))


def _serial_filename_part(serial: str) -> str:
    cleaned = _UNSAFE_FILENAME.sub("_", (serial or "").strip()).strip("._")
    return cleaned or "serial"


def next_slot_filename(
    slot: str,
    existing_names: list[str],
    original_name: str,
    *,
    serial: str = "",
    uploaded_at: datetime | None = None,
) -> str:
    suffix = Path(original_name or "").suffix.lower()
    if slot_allows_multiple(slot):
        taken = {name.lower() for name in existing_names}
        index = 1
        while True:
            name = f"{slot}_{index}{suffix}"
            if name.lower() not in taken:
                return name
            index += 1
    if slot == "form":
        moment = uploaded_at or datetime.now(CHICAGO)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=CHICAGO)
        moment = moment.astimezone(CHICAGO)
        serial_part = _serial_filename_part(serial)
        return f"{serial_part}_{moment:%Y-%m-%d_%H%M%S}{suffix or '.pdf'}"
    if slot == "video":
        return f"video{suffix or '.mp4'}"
    return f"{slot}{suffix}"


def qc_uploads_complete(uploads: dict | None) -> bool:
    stored = uploads or {}
    return all(
        slot_has_upload(stored.get(key) if isinstance(stored.get(key), dict) else None)
        for key in QC_SLOT_KEYS
    )
