from pathlib import Path
import mimetypes

from django.db import IntegrityError, transaction
from django.db.models import Count, Q, QuerySet
from django.db.utils import DataError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.http import content_disposition_header

from sauna_data.forms import PhysicalUnitQcForm
from sauna_data.models import Product, ProductIssue, ProductItem
from sauna_data.qc_support import catalog_file, support_file

UNIT_SAVE_FAILED = "This QC status could not be saved. Check your entries and try again."


@ensure_csrf_cookie
def render_app(request: HttpRequest, title: str) -> HttpResponse:
    return render(request, "sauna_data/app_shell.html", {"page_title": title})


def _search_term(request: HttpRequest) -> str:
    return (request.GET.get("q") or "").strip()


PRODUCT_SORT_FIELDS = {
    "id": "product_id",
    "item_no": "item_no",
    "product": "product_name",
    "voltage": "voltage",
    "plug": "plug_type",
    "wattage": "wattage",
    "supplier": "supplier",
    "cords": "number_of_cords",
    "power_box": "power_box__name",
    "known_issues": "known_issue_count",
}
POWER_BOX_FILTERS = (
    ("luis", "Luis"),
    ("wang", "Wang"),
    ("li", "Li"),
)
PRODUCT_FAMILY_FILTERS = (
    ("pro5", "Pro5"),
    ("cs", "CS"),
    ("redfit", "RedFit Room"),
)
SUPPLIER_LABEL_ORDER = {"G": 0, "R": 1, "S": 2}


def supplier_choices() -> list[str]:
    return list(
        Product.objects.exclude(supplier="")
        .order_by("supplier")
        .values_list("supplier", flat=True)
        .distinct()
    )


def _supplier_filters(choices: list[str]) -> tuple[tuple[str, str], ...]:
    labeled = []
    for name in choices:
        label = Product(supplier=name).public_supplier_label()
        if label in SUPPLIER_LABEL_ORDER:
            labeled.append((name.casefold(), label))
    return tuple(sorted(labeled, key=lambda item: SUPPLIER_LABEL_ORDER[item[1]]))


def _power_box_type_filter(box: str) -> Q:
    if box == "li":
        return Q(power_box__name__iregex=r"(^|[^a-z0-9])li([^a-z0-9]|$)")
    return Q(power_box__name__icontains=box)


def _product_family_filter(family: str) -> Q:
    if family == "pro5":
        return Q(product_name__iregex=r"pro\s*5")
    if family == "cs":
        return Q(product_name__istartswith="CS")
    return Q(product_name__icontains="redfit room")


def product_list_query(request: HttpRequest) -> tuple[QuerySet[Product], dict]:
    choices = supplier_choices()
    supplier_names = {name.casefold(): name for name in choices}
    supplier_filters = _supplier_filters(choices)
    queryset: QuerySet[Product] = Product.objects.select_related(
        "power_box", "power_box__control_panel"
    ).defer(
        "power_box__picture",
        "power_box__firmware_document",
        "power_box__firmware_video",
        "power_box__control_panel__picture",
        "power_box__control_panel__documentation_1",
        "power_box__control_panel__documentation_2",
    ).annotate(
        known_issue_count=Count("issues", distinct=True)
    )
    query = _search_term(request)
    if query:
        filters = (
            Q(item_no__icontains=query)
            | Q(product_name__icontains=query)
            | Q(supplier__icontains=query)
        )
        if query.isdigit():
            filters |= Q(product_id=int(query))
        queryset = queryset.filter(filters)
    box_keys = {key for key, _label in POWER_BOX_FILTERS}
    family_keys = {key for key, _label in PRODUCT_FAMILY_FILTERS}
    box = (request.GET.get("box") or "").strip().lower()
    if box not in box_keys:
        box = ""
    family = (request.GET.get("family") or "").strip().lower()
    if family not in family_keys:
        family = ""
    supplier = (request.GET.get("supplier") or "").strip().casefold()
    supplier_name = supplier_names.get(supplier, "")
    if family:
        box = ""
        supplier = ""
        supplier_name = ""
        queryset = queryset.filter(_product_family_filter(family))
    elif box:
        supplier = ""
        supplier_name = ""
        queryset = queryset.filter(_power_box_type_filter(box))
    elif supplier_name:
        queryset = queryset.filter(supplier__iexact=supplier_name)
    else:
        supplier = ""
    sort = request.GET.get("sort") or "id"
    if sort not in PRODUCT_SORT_FIELDS:
        sort = "id"
    direction = request.GET.get("dir") or "asc"
    if direction not in {"asc", "desc"}:
        direction = "asc"
    sort_field = PRODUCT_SORT_FIELDS[sort]
    if direction == "desc":
        sort_field = f"-{sort_field}"
    queryset = queryset.order_by(sort_field, "product_id")
    return queryset, {
        "q": query,
        "sort": sort,
        "dir": direction,
        "supplier": supplier,
        "suppliers": supplier_filters,
        "box": box,
        "boxes": POWER_BOX_FILTERS,
        "family": family,
        "families": PRODUCT_FAMILY_FILTERS,
    }


def product_list(request: HttpRequest) -> HttpResponse:
    return render_app(request, "Products")


def catalog_section(request: HttpRequest, section: str) -> HttpResponse:
    titles = {
        "power_boxes": "Power boxes",
        "control_panels": "Control panels",
        "firmware_instructions": "Firmware instructions",
    }
    return render_app(request, titles[section])


def product_detail(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product.objects.only("product_id", "product_name"), pk=product_id)
    return render_app(request, product.product_name)


TRACKER_SHORTCUT_FILTERS = (
    ("mccoy", "McCoy"),
    ("tyron", "Tyron"),
    ("luis", "Luis"),
    ("li", "Li"),
    ("wang", "Wang"),
)
TRACKER_SORT_FIELDS = {
    "qc_person": "qc_tester_name",
    "serial": "serial_no",
    "qc_status": "qc_status",
    "note": "note",
}


def unit_list_query(request: HttpRequest) -> tuple[QuerySet[ProductItem], dict]:
    queryset: QuerySet[ProductItem] = ProductItem.objects.select_related("product").defer("qc_form")
    query = _search_term(request)
    if query:
        queryset = queryset.filter(
            Q(serial_no__icontains=query)
            | Q(product__item_no__icontains=query)
            | Q(product__product_name__icontains=query)
            | Q(qc_tester_name__icontains=query)
            | Q(qc_status__icontains=query)
            | Q(note__icontains=query)
        )
    pick = (request.GET.get("pick") or "").strip().lower()
    if pick not in {key for key, _label in TRACKER_SHORTCUT_FILTERS}:
        pick = ""
    if pick:
        queryset = queryset.filter(qc_tester_name__icontains=pick)
    sort = request.GET.get("sort") or "serial"
    direction = request.GET.get("dir") or "asc"
    if direction not in {"asc", "desc"}:
        direction = "asc"
    if sort not in TRACKER_SORT_FIELDS:
        sort = "serial"
    sort_field = TRACKER_SORT_FIELDS[sort]
    if direction == "desc":
        sort_field = f"-{sort_field}"
    units = queryset.order_by(sort_field, "product_item_id")
    return units, {
        "q": query,
        "sort": sort,
        "dir": direction,
        "pick": pick,
        "filters": TRACKER_SHORTCUT_FILTERS,
    }


def physical_unit_list(request: HttpRequest) -> HttpResponse:
    return render_app(request, "QC & CS")


def _safe_filename(name: str) -> str:
    cleaned = Path(name or "").name.replace("\x00", "").strip()
    return cleaned or "upload"


def physical_unit_detail(request: HttpRequest, unit_id: int) -> HttpResponse:
    unit = get_object_or_404(ProductItem, pk=unit_id)
    form = PhysicalUnitQcForm(instance=unit)
    if request.method == "POST":
        action = request.POST.get("action", "save_status")
        if action == "upload_form":
            uploaded = request.FILES.get("qc_form")
            if uploaded is not None:
                unit.qc_form = uploaded.read()
                unit.qc_form_name = _safe_filename(getattr(uploaded, "name", ""))
                unit.save(update_fields=["qc_form", "qc_form_name"])
            return redirect("physical_unit_detail", unit_id=unit.product_item_id)
        if action == "delete_form":
            unit.qc_form = None
            unit.qc_form_name = ""
            unit.save(update_fields=["qc_form", "qc_form_name"])
            return redirect("physical_unit_detail", unit_id=unit.product_item_id)
        form = PhysicalUnitQcForm(request.POST, instance=unit)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                return redirect("physical_unit_list")
            except (IntegrityError, DataError, ValueError):
                form.add_error(None, UNIT_SAVE_FAILED)
        return render(
            request,
            "sauna_data/physical_unit_detail.html",
            {"unit": unit, "form": form},
        )
    return render_app(request, f"Serial {unit.serial_no}")


def customer_service_list(request: HttpRequest) -> HttpResponse:
    return physical_unit_list(request)


def customer_service_detail(request: HttpRequest, unit_id: int) -> HttpResponse:
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    unit = get_object_or_404(ProductItem.objects.only("product_item_id", "serial_no"), pk=unit_id)
    return render_app(request, f"Serial {unit.serial_no}")


def catalog_support_file(request: HttpRequest, kind: str, owner_id: int, slot: str) -> HttpResponse:
    content, filename, content_type = catalog_file(kind, owner_id, slot)
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = content_disposition_header(False, filename)
    return response


def qc_support_file(request: HttpRequest, product_id: int, kind: str, owner_id: int, slot: str) -> HttpResponse:
    get_object_or_404(Product.objects.only("product_id"), pk=product_id)
    content, filename, content_type = support_file(product_id, kind, owner_id, slot)
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = content_disposition_header(False, filename)
    return response


def qc_form_file(request: HttpRequest, unit_id: int) -> HttpResponse:
    unit = get_object_or_404(ProductItem.objects.only("product_item_id", "qc_form", "qc_form_name"), pk=unit_id)
    if not unit.qc_form or not unit.qc_form_name:
        raise Http404()
    response = HttpResponse(bytes(unit.qc_form), content_type="application/pdf")
    response["Content-Disposition"] = content_disposition_header(False, unit.qc_form_name)
    return response


def product_issue_file(request: HttpRequest, product_id: int, issue_id: int) -> HttpResponse:
    issue = get_object_or_404(ProductIssue, pk=issue_id, products__pk=product_id)
    if not issue.documentation or not issue.documentation_name:
        raise Http404()
    content_type = mimetypes.guess_type(issue.documentation_name)[0] or "application/octet-stream"
    response = HttpResponse(bytes(issue.documentation), content_type=content_type)
    response["Content-Disposition"] = content_disposition_header(False, issue.documentation_name)
    return response
