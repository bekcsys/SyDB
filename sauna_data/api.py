from django.db import IntegrityError, transaction
from django.db.models import Case, IntegerField, Prefetch, Value, When
from django.db.utils import DataError
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sauna_data.forms import PhysicalUnitQcForm
from sauna_data.models import Product, ProductIssue, ProductItem
from sauna_data.qc_support import product_page_catalog, qc_support_for_product, instruction_document
from sauna_data.views import (
    UNIT_SAVE_FAILED,
    _safe_filename,
    product_list_query,
    unit_list_query,
)


def _json(payload: dict, status: int = 200) -> JsonResponse:
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = "no-store"
    return response


def _pairs(items) -> list[dict[str, str]]:
    return [{"key": key, "label": label} for key, label in items]


def _equipment_ref(owner, kind: str) -> dict | None:
    if owner is None:
        return None
    picture_url = None
    if owner.picture_name:
        picture_url = reverse("catalog_file", args=[kind, owner.pk, "picture"])
    return {"name": owner.name, "picture_url": picture_url}


def _form_errors(form: PhysicalUnitQcForm) -> list[str]:
    errors = [str(error) for error in form.non_field_errors()]
    for field in form:
        errors.extend(f"{field.label}: {error}" for error in field.errors)
    return errors


def _file_label(files: list[dict]) -> str:
    if not files:
        return "(None)"
    return str(files[0]["name"])


@require_GET
def products_api(request: HttpRequest) -> JsonResponse:
    queryset, meta = product_list_query(request)
    products = []
    for product in queryset:
        box = product.power_box
        panel = box.control_panel if box is not None and box.control_panel_id else None
        products.append(
            {
                "id": product.product_id,
                "supplier_label": product.public_supplier_label(),
                "item_no": product.item_no,
                "name": product.product_name,
                "power_box": _equipment_ref(box, "power-box"),
                "control_panel": _equipment_ref(panel, "control-panel"),
                "known_issues": product.known_issue_count,
            }
        )
    return _json(
        {
            "q": meta["q"],
            "sort": meta["sort"],
            "dir": meta["dir"],
            "supplier": meta["supplier"],
            "box": meta["box"],
            "family": meta["family"],
            "filters": {
                "suppliers": _pairs(meta["suppliers"]),
                "boxes": _pairs(meta["boxes"]),
                "families": _pairs(meta["families"]),
            },
            "products": products,
        }
    )


def _issue_queryset(product: Product):
    solved_last = Case(
        When(status=ProductIssue.Status.SOLVED, then=Value(1)),
        default=Value(0),
        output_field=IntegerField(),
    )
    return (
        product.issues.defer("documentation", "support_doc")
        .annotate(solved_last=solved_last)
        .order_by("solved_last", "-date", "-product_issue_id")
    )


def _issue_row(issue: ProductIssue, product_id: int) -> dict:
    document_url, document_name = instruction_document(issue.doc_ref)
    if not document_url and issue.documentation_name:
        document_url = reverse("product_issue_file", args=[product_id, issue.product_issue_id])
        document_name = issue.documentation_name
    support_url = ""
    if issue.support_doc_name:
        support_url = reverse("product_issue_support_file", args=[product_id, issue.product_issue_id])
    return {
        "id": issue.product_issue_id,
        "date": issue.date.isoformat(),
        "status": issue.status,
        "status_label": issue.get_status_display(),
        "note": issue.note,
        "documentation_name": document_name,
        "documentation_url": document_url,
        "support_doc_name": issue.support_doc_name,
        "support_doc_url": support_url,
    }


def _unit_for_product(unit: ProductItem, product: Product) -> dict:
    form_url = ""
    if unit.qc_form_name:
        form_url = reverse("qc_form_file", args=[unit.product_item_id])
    return {
        "id": unit.product_item_id,
        "serial_no": unit.serial_no,
        "product_name": product.product_name,
        "item_no": product.item_no,
        "qc_status": unit.qc_status,
        "qc_status_label": unit.get_qc_status_display(),
        "note": unit.note,
        "qc_form_name": unit.qc_form_name,
        "qc_form_url": form_url,
        "url": reverse("physical_unit_detail", args=[unit.product_item_id]),
    }


def _panel_rows(product: Product) -> list[dict]:
    box = product.power_box
    panel = box.control_panel if box is not None and box.control_panel_id else None
    if panel is None:
        return []
    picture_url = ""
    if panel.picture_name:
        picture_url = reverse("catalog_file", args=["control-panel", panel.pk, "picture"])
    return [
        {
            "name": panel.name,
            "part_number": panel.part_number or "—",
            "firmware_device": panel.firmware_device or "—",
            "picture_url": picture_url,
        }
    ]


@require_GET
def product_detail_api(request: HttpRequest, product_id: int) -> JsonResponse:
    product = get_object_or_404(
        Product.objects.select_related("power_box", "power_box__control_panel").defer("picture"),
        pk=product_id,
    )
    support = qc_support_for_product(product)
    units = [
        _unit_for_product(unit, product)
        for unit in product.product_items.defer("qc_form").order_by("serial_no")
    ]
    issues = [_issue_row(issue, product.pk) for issue in _issue_queryset(product)]
    return _json(
        {
            "id": product.product_id,
            "name": product.product_name,
            "item_no": product.item_no,
            "voltage": product.voltage,
            "plug_type": product.get_plug_type_display() or "",
            "wattage": product.wattage,
            "watt_on_label": product.watt_on_label,
            "supplier": product.supplier,
            "supplier_label": product.public_supplier_label(),
            "cords": product.number_of_cords,
            "unit_count": len(units),
            "power_box": product.power_box_type_label(),
            "control_panel": product.control_panel_type_label(),
            "picture_url": (
                reverse("product_picture", args=[product.pk]) if product.picture_name else ""
            ),
            "firmware_updates": support["firmware_updates"],
            "panel_instructions": support["panel_instructions"],
            "panels": support["panels"],
            "boxes": support["boxes"],
            "panel_rows": _panel_rows(product),
            "units": units,
            "issues": issues,
            "known_issue_count": len(issues),
        }
    )


@require_GET
def power_boxes_api(request: HttpRequest) -> JsonResponse:
    rows = []
    for index, row in enumerate(product_page_catalog()["power_boxes"], start=1):
        rows.append(
            {
                **row,
                "index": index,
                "firmware_display": row["firmware_info"] or "(None)",
                "part_number_display": row["part_number"] or "—",
                "control_panel_display": row["control_panel"] or "—",
            }
        )
    return _json({"power_boxes": rows})


@require_GET
def control_panels_api(request: HttpRequest) -> JsonResponse:
    rows = []
    for index, row in enumerate(product_page_catalog()["control_panels"], start=1):
        rows.append(
            {
                **row,
                "index": index,
                "part_number_display": row["part_number"] or "—",
                "firmware_instruction_name": _file_label(row["documentation_1"]),
                "panel_instruction_name": _file_label(row["documentation_2"]),
                "firmware_device_display": row["firmware_device"] or "(None)",
            }
        )
    return _json({"control_panels": rows})


@require_GET
def firmware_api(request: HttpRequest) -> JsonResponse:
    rows = []
    for index, row in enumerate(product_page_catalog()["firmware_instructions"], start=1):
        document = row["document"]
        video = row["video"]
        rows.append(
            {
                **row,
                "index": index,
                "document_name": document["name"] if document else "(None)",
                "video_name": video["name"] if video else "(None)",
            }
        )
    return _json({"firmware_instructions": rows})


def _unit_row(unit: ProductItem) -> dict:
    form_url = ""
    if unit.qc_form_name:
        form_url = reverse("qc_form_file", args=[unit.product_item_id])
    return {
        "id": unit.product_item_id,
        "serial_no": unit.serial_no,
        "product_id": unit.product_id,
        "product_name": unit.product.product_name if unit.product_id else "",
        "qc_tester_name": unit.qc_tester_name,
        "qc_status": unit.qc_status,
        "qc_status_label": unit.get_qc_status_display(),
        "note": unit.note,
        "qc_form_name": unit.qc_form_name,
        "qc_form_url": form_url,
    }


def _catalog_issues() -> list[dict]:
    issues = ProductIssue.objects.defer("documentation", "support_doc").prefetch_related(
        Prefetch(
            "products",
            queryset=Product.objects.only("product_id", "product_name", "item_no").order_by(
                "product_name", "item_no"
            ),
        )
    )
    rows = []
    for issue in issues:
        products = list(issue.products.all())
        product_id = products[0].pk if products else 0
        row = _issue_row(issue, product_id)
        row["products"] = [
            {"id": product.pk, "name": product.product_name, "item_no": product.item_no}
            for product in products
        ]
        row["impacted_products"] = len(products)
        rows.append(row)
    rows.sort(key=lambda row: (row["impacted_products"], row["date"], row["id"]), reverse=True)
    return rows


@require_GET
def units_api(request: HttpRequest) -> JsonResponse:
    units, meta = unit_list_query(request)
    return _json(
        {
            "q": meta["q"],
            "sort": meta["sort"],
            "dir": meta["dir"],
            "pick": meta["pick"],
            "filters": _pairs(meta["filters"]),
            "units": [_unit_row(unit) for unit in units],
            "issues": _catalog_issues(),
        }
    )


def _product_issues(unit: ProductItem) -> list[dict]:
    if not unit.product_id:
        return []
    return [_issue_row(issue, unit.product_id) for issue in _issue_queryset(unit.product)]


def _unit_editor(unit: ProductItem) -> dict:
    products = [
        {"id": product.product_id, "name": product.product_name, "item_no": product.item_no}
        for product in Product.objects.only("product_id", "product_name", "item_no").order_by(
            "product_name", "item_no"
        )
    ]
    return {
        **_unit_row(unit),
        "products": products,
        "statuses": [
            {"value": value, "label": label} for value, label in ProductItem.Status.choices
        ],
        "issues": _product_issues(unit),
    }


@require_http_methods(["GET", "POST"])
def unit_detail_api(request: HttpRequest, unit_id: int) -> JsonResponse:
    unit = get_object_or_404(ProductItem.objects.select_related("product"), pk=unit_id)
    if request.method == "POST":
        form = PhysicalUnitQcForm(request.POST, instance=unit)
        if not form.is_valid():
            return _json({"ok": False, "errors": _form_errors(form)}, 400)
        try:
            with transaction.atomic():
                form.save()
        except (IntegrityError, DataError, ValueError):
            return _json({"ok": False, "errors": [UNIT_SAVE_FAILED]}, 400)
        unit.refresh_from_db()
        unit = ProductItem.objects.select_related("product").get(pk=unit.pk)
        return _json({"ok": True, "unit": _unit_row(unit), "issues": _product_issues(unit)})
    return _json(_unit_editor(unit))


@require_POST
def unit_form_api(request: HttpRequest, unit_id: int) -> JsonResponse:
    unit = get_object_or_404(ProductItem, pk=unit_id)
    if request.POST.get("action") == "delete_form":
        unit.qc_form = None
        unit.qc_form_name = ""
        unit.save(update_fields=["qc_form", "qc_form_name"])
        return _json({"ok": True, "qc_form_name": "", "qc_form_url": ""})
    uploaded = request.FILES.get("qc_form")
    if uploaded is None:
        return _json({"ok": False, "errors": ["Choose a QC form to upload."]}, 400)
    unit.qc_form = uploaded.read()
    unit.qc_form_name = _safe_filename(getattr(uploaded, "name", ""))
    unit.save(update_fields=["qc_form", "qc_form_name"])
    return _json(
        {
            "ok": True,
            "qc_form_name": unit.qc_form_name,
            "qc_form_url": reverse("qc_form_file", args=[unit.product_item_id]),
        }
    )
