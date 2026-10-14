from django.db.models import Prefetch
from django.http import Http404
from django.urls import reverse

from sauna_data.models import (
    ControlPanel,
    PowerBox,
    Product,
)
from sauna_data.power_boxes import associated_product_label

_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
}
_PANEL_SLOTS = {
    "picture": ("picture", "picture_name"),
    "documentation": ("documentation_1", "documentation_1_name"),
    "documentation-2": ("documentation_2", "documentation_2_name"),
}
_BOX_SLOTS = {
    "picture": ("picture", "picture_name"),
    "firmware-document": ("firmware_document", "firmware_document_name"),
    "firmware-video": ("firmware_video", "firmware_video_name"),
}
_PANEL_DOCS = ("documentation", "documentation-2")
_BOX_FIRMWARE_FILES = ("firmware-document", "firmware-video")


def _files(owner, slots: tuple[str, ...], product_id: int, kind: str, owner_id: int) -> list[dict[str, str]]:
    slot_map = {
        "control-panel": _PANEL_SLOTS,
        "power-box": _BOX_SLOTS,
    }[kind]
    files = []
    for slot in slots:
        filename = getattr(owner, slot_map[slot][1])
        if not filename:
            continue
        files.append(
            {
                "name": filename,
                "url": reverse(
                    "qc_support_file",
                    args=[product_id, kind, owner_id, slot],
                ),
            }
        )
    return files


def qc_support_for_product(product: Product) -> dict:
    boxes = list(
        PowerBox.objects.filter(pk=product.power_box_id)
        .select_related("control_panel")
        .defer(
            "picture",
            "firmware_document",
            "firmware_video",
            "control_panel__picture",
            "control_panel__documentation_1",
            "control_panel__documentation_2",
        )
        .order_by("name")
    )
    panels = []
    seen_panels: set[int] = set()
    for box in boxes:
        panel = box.control_panel
        if panel is None or panel.pk in seen_panels:
            continue
        seen_panels.add(panel.pk)
        panels.append(
            {
                "name": panel.name,
                "instructions": _files(panel, _PANEL_DOCS, product.pk, "control-panel", panel.pk),
                "pictures": _files(panel, ("picture",), product.pk, "control-panel", panel.pk),
            }
        )
    box_rows = [
        {
            "name": box.name,
            "pictures": _files(box, ("picture",), product.pk, "power-box", box.pk),
            "firmware": _files(box, _BOX_FIRMWARE_FILES, product.pk, "power-box", box.pk),
        }
        for box in boxes
    ]
    firmware_updates = [file for box in box_rows for file in box["firmware"]]
    panel_instructions = [file for panel in panels for file in panel["instructions"]]
    return {
        "panels": panels,
        "boxes": box_rows,
        "firmware_updates": firmware_updates,
        "panel_instructions": panel_instructions,
    }


_VIDEO_SUFFIXES = (".mp4", ".m4v", ".mov", ".webm")


def split_documents_and_videos(files: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    documents: list[dict[str, str]] = []
    videos: list[dict[str, str]] = []
    for file in files:
        if file["name"].lower().endswith(_VIDEO_SUFFIXES):
            videos.append(file)
        else:
            documents.append(file)
    return documents, videos


def catalog_links(owner, kind: str, slots: tuple[str, ...]) -> list[dict[str, str | bool]]:
    slot_map = {
        "control-panel": _PANEL_SLOTS,
        "power-box": _BOX_SLOTS,
    }[kind]
    files = []
    seen = set()
    for slot in slots:
        filename = getattr(owner, slot_map[slot][1])
        if not filename or filename in seen:
            continue
        seen.add(filename)
        files.append(
            {
                "name": filename,
                "url": reverse("catalog_file", args=[kind, owner.pk, slot]),
                "video": filename.lower().endswith(_VIDEO_SUFFIXES),
            }
        )
    return files


def _named_file(files: list[dict[str, str | bool]], video: bool) -> dict[str, str] | None:
    for file in files:
        if bool(file["video"]) is video:
            return {"name": str(file["name"]), "url": str(file["url"])}
    return None


def product_page_catalog() -> dict:
    boxes = (
        PowerBox.objects.select_related("control_panel")
        .defer(
            "picture",
            "firmware_document",
            "firmware_video",
            "control_panel__picture",
            "control_panel__documentation_1",
            "control_panel__documentation_2",
        )
        .prefetch_related(
            Prefetch(
                "products",
                queryset=Product.objects.only(
                    "product_id", "item_no", "product_name", "power_box_id"
                ).order_by("product_name", "item_no"),
            )
        )
        .order_by("name")
    )
    panels = ControlPanel.objects.defer(
        "picture",
        "documentation_1",
        "documentation_2",
    ).order_by("name")
    box_rows = []
    firmware_rows = []
    for box in boxes:
        firmware_files = catalog_links(box, "power-box", _BOX_FIRMWARE_FILES)
        box_rows.append(
            {
                "name": box.name,
                "part_number": box.part_number,
                "control_panel": box.control_panel.name if box.control_panel_id else "",
                "control_panel_picture": (
                    catalog_links(box.control_panel, "control-panel", ("picture",))
                    if box.control_panel_id
                    else []
                ),
                "pictures": catalog_links(box, "power-box", ("picture",)),
                "firmware_info": box.firmware_info,
                "firmware_files": firmware_files,
                "products": [
                    {
                        "name": associated_product_label(product.product_name) or product.item_no,
                        "url": reverse("product_detail", args=[product.product_id]),
                    }
                    for product in box.products.all()
                ],
            }
        )
        if box.firmware_info:
            firmware_rows.append(
                {
                    "name": box.firmware_info,
                    "target": _picture_target(box.name, box, "power-box"),
                    "document": _named_file(firmware_files, False),
                    "video": _named_file(firmware_files, True),
                }
            )
    panel_rows = []
    for panel in panels:
        docs = catalog_links(panel, "control-panel", _PANEL_DOCS)
        panel_rows.append(
            {
                "name": panel.name,
                "part_number": panel.part_number,
                "picture": catalog_links(panel, "control-panel", ("picture",)),
                "documentation_1": catalog_links(panel, "control-panel", ("documentation",)),
                "documentation_2": catalog_links(panel, "control-panel", ("documentation-2",)),
                "firmware_device": panel.firmware_device,
            }
        )
        if panel.firmware_device:
            firmware_rows.append(
                {
                    "name": panel.firmware_device,
                    "target": _picture_target(panel.name, panel, "control-panel"),
                    "document": _named_file(docs, False),
                    "video": _named_file(docs, True),
                }
            )
    firmware_rows.sort(key=lambda row: row["name"].casefold())
    return {
        "power_boxes": box_rows,
        "control_panels": panel_rows,
        "firmware_instructions": firmware_rows,
    }


def _picture_target(name: str, owner, kind: str) -> dict[str, str]:
    pictures = catalog_links(owner, kind, ("picture",))
    return {"name": name, "url": pictures[0]["url"] if pictures else ""}


def catalog_file(kind: str, owner_id: int, slot: str) -> tuple[bytes, str, str]:
    if kind == "control-panel":
        fields = _PANEL_SLOTS.get(slot)
        owner = ControlPanel.objects.filter(pk=owner_id)
    elif kind == "power-box":
        fields = _BOX_SLOTS.get(slot)
        owner = PowerBox.objects.filter(pk=owner_id)
    else:
        fields = None
        owner = None
    if fields is None or owner is None:
        raise Http404
    stored = owner.values_list(fields[0], fields[1]).first()
    if stored is None:
        raise Http404
    content, filename = stored
    if not content or not filename:
        raise Http404
    suffix = filename[filename.rfind("."):].lower() if "." in filename else ""
    return bytes(content), filename, _CONTENT_TYPES.get(suffix, "application/octet-stream")


def support_file(product_id: int, kind: str, owner_id: int, slot: str) -> tuple[bytes, str, str]:
    if kind == "control-panel":
        fields = _PANEL_SLOTS.get(slot)
        linked = ControlPanel.objects.filter(
            pk=owner_id,
            power_boxes__products=product_id,
        )
    elif kind == "power-box":
        fields = _BOX_SLOTS.get(slot)
        linked = PowerBox.objects.filter(pk=owner_id, products=product_id)
    else:
        fields = None
        linked = None
    if fields is None or linked is None:
        raise Http404
    stored = linked.values_list(fields[0], fields[1]).first()
    if stored is None:
        raise Http404
    content, filename = stored
    if not content or not filename:
        raise Http404
    suffix = filename[filename.rfind("."):].lower() if "." in filename else ""
    return bytes(content), filename, _CONTENT_TYPES.get(suffix, "application/octet-stream")
