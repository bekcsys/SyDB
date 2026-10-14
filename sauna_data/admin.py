import re
from pathlib import Path

from django import forms
from django.contrib import admin
from django.db.models import Prefetch
from django.http import Http404, HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.http import content_disposition_header

from sauna_data.models import (
    ControlPanel,
    ProductItem,
    PowerBox,
    Product,
)
from sauna_data.power_boxes import associated_product_label


class EditableModelAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        return request.user.is_active and (
            request.user.is_superuser or super().has_view_permission(request, obj)
        )

    def has_add_permission(self, request):
        return request.user.is_active and (
            request.user.is_superuser or super().has_add_permission(request)
        )

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and (
            request.user.is_superuser or super().has_change_permission(request, obj)
        )

    def has_delete_permission(self, request, obj=None):
        return request.user.is_active and (
            request.user.is_superuser or super().has_delete_permission(request, obj)
        )


_PICTURE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_CONTROL_PANEL_FILE_LIMIT = 8 * 1024 * 1024
_CONTROL_PANEL_FILE_SLOTS = {
    "picture": ("picture", "picture_name"),
    "documentation": ("documentation_1", "documentation_1_name"),
    "documentation-2": ("documentation_2", "documentation_2_name"),
}
_CONTROL_PANEL_PICTURE = ("picture", "picture_name", "picture_upload")
_CONTROL_PANEL_PDFS = (
    ("documentation_1", "documentation_1_name", "documentation_upload"),
    ("documentation_2", "documentation_2_name", "documentation_upload_2"),
)
_UPLOAD_FIELDS = {
    "picture": "picture_upload",
    "documentation": "documentation_upload",
    "documentation-2": "documentation_upload_2",
}
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


def control_panel_picture_filename(side: str, index: int, suffix: str) -> str:
    return f"{side}_{index}{suffix.lower()}"


def _stored_upload_name(uploaded) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", Path(uploaded.name).name).strip(" .")
    return (cleaned or "upload")[:255]


def _file_help(url: str, filename: str, upload_field: str):
    return format_html(
        'Current file: <a href="{}">{}</a> '
        '<label><input type="checkbox" name="{}" value="1"> Delete</label>',
        url,
        filename,
        f"{upload_field}_clear",
    )


def _clear_requested(form: forms.BaseForm, upload_field: str) -> bool:
    return form.data.get(f"{upload_field}_clear") == "1"


def _clean_limited_upload(uploaded, suffixes: set[str], type_message: str, max_bytes: int = _CONTROL_PANEL_FILE_LIMIT):
    if not uploaded:
        return uploaded
    if uploaded.size > max_bytes:
        raise forms.ValidationError(f"File must be {max_bytes // (1024 * 1024)} MB or smaller.")
    if Path(uploaded.name).suffix.lower() not in suffixes:
        raise forms.ValidationError(type_message)
    return uploaded


class ControlPanelAdminForm(forms.ModelForm):
    picture_upload = forms.FileField(
        required=False,
        label="Picture",
        widget=forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.webp,.gif"}),
    )
    documentation_upload = forms.FileField(
        required=False,
        label="Documentation 1",
        widget=forms.FileInput(attrs={"accept": ".pdf,application/pdf"}),
    )
    documentation_upload_2 = forms.FileField(
        required=False,
        label="Documentation 2",
        widget=forms.FileInput(attrs={"accept": ".pdf,application/pdf"}),
    )

    class Meta:
        model = ControlPanel
        fields = ("name", "part_number", "firmware_device", "note")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        panel = self.instance
        if not panel.pk:
            return
        for slot, (_content, name_field) in _CONTROL_PANEL_FILE_SLOTS.items():
            filename = getattr(panel, name_field)
            if not filename:
                continue
            url = reverse("admin:sauna_data_controlpanel_file", args=[panel.pk, slot])
            self.fields[_UPLOAD_FIELDS[slot]].help_text = _file_help(
                url,
                filename,
                _UPLOAD_FIELDS[slot],
            )

    def clean_picture_upload(self):
        return self._clean_picture("picture_upload", "Picture")

    def _clean_picture(self, field_name: str, label: str):
        return _clean_limited_upload(
            self.cleaned_data.get(field_name),
            _PICTURE_SUFFIXES,
            f"{label} picture must be a JPG, PNG, WEBP, or GIF file.",
        )

    def clean_documentation_upload(self):
        return self._clean_pdf("documentation_upload")

    def clean_documentation_upload_2(self):
        return self._clean_pdf("documentation_upload_2")

    def _clean_pdf(self, field_name: str):
        return _clean_limited_upload(
            self.cleaned_data.get(field_name),
            {".pdf"},
            "Instruction must be a PDF file.",
        )

    def save(self, commit=True):
        panel = super().save(commit=False)
        content_field, name_field, upload_field = _CONTROL_PANEL_PICTURE
        if _clear_requested(self, upload_field):
            setattr(panel, content_field, None)
            setattr(panel, name_field, "")
        else:
            uploaded = self.cleaned_data.get(upload_field)
            if uploaded:
                suffix = Path(uploaded.name).suffix.lower()
                setattr(panel, content_field, uploaded.read())
                setattr(panel, name_field, f"picture{suffix}")
        for content_field, name_field, upload_field in _CONTROL_PANEL_PDFS:
            if _clear_requested(self, upload_field):
                setattr(panel, content_field, None)
                setattr(panel, name_field, "")
                continue
            uploaded = self.cleaned_data.get(upload_field)
            if not uploaded:
                continue
            setattr(panel, content_field, uploaded.read())
            setattr(panel, name_field, _stored_upload_name(uploaded))
        if commit:
            panel.save()
        return panel


@admin.register(ControlPanel)
class ControlPanelAdmin(EditableModelAdmin):
    form = ControlPanelAdminForm
    list_display = (
        "name",
        "part_number",
        "firmware_device",
        "written_note",
        "picture_file",
        "documentation_files",
    )
    search_fields = ("name", "part_number", "firmware_device", "note")
    ordering = ("name",)
    fields = (
        "name",
        "part_number",
        "firmware_device",
        "note",
        "picture_upload",
        "documentation_upload",
        "documentation_upload_2",
        "control_panel_id",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("control_panel_id", "created_at", "updated_at")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .defer(
                "picture",
                "documentation_1",
                "documentation_2",
            )
        )

    def get_urls(self):
        custom = [
            path(
                "<path:object_id>/file/<str:slot>/",
                self.admin_site.admin_view(self.serve_file),
                name="sauna_data_controlpanel_file",
            ),
        ]
        return custom + super().get_urls()

    def serve_file(self, request, object_id, slot):
        fields = _CONTROL_PANEL_FILE_SLOTS.get(slot)
        panel = self.get_object(request, object_id)
        if fields is None or panel is None:
            raise Http404
        content_field, name_field = fields
        stored = (
            ControlPanel.objects.filter(pk=panel.pk)
            .values_list(content_field, name_field)
            .first()
        )
        if stored is None:
            raise Http404
        content, filename = stored
        if not content or not filename:
            raise Http404
        response = HttpResponse(bytes(content), content_type=_CONTENT_TYPES.get(
            Path(filename).suffix.lower(),
            "application/octet-stream",
        ))
        response["Content-Disposition"] = content_disposition_header(False, filename)
        return response

    @admin.display(description="Note")
    def written_note(self, obj: ControlPanel) -> str:
        return obj.note

    def _picture_links(self, obj: ControlPanel, slots: tuple[str, ...]):
        links = []
        for slot in slots:
            filename = getattr(obj, _CONTROL_PANEL_FILE_SLOTS[slot][1])
            if not filename:
                continue
            url = reverse("admin:sauna_data_controlpanel_file", args=[obj.pk, slot])
            links.append((url, filename))
        if not links:
            return "—"
        return format_html_join(format_html("<br>"), '<a href="{}">{}</a>', links)

    @admin.display(description="Picture")
    def picture_file(self, obj: ControlPanel):
        return self._picture_links(obj, ("picture",))

    @admin.display(description="Documentation")
    def documentation_files(self, obj: ControlPanel):
        return self._picture_links(obj, ("documentation", "documentation-2"))



_FIRMWARE_FILE_LIMIT = 80 * 1024 * 1024
_POWER_BOX_FILE_SLOTS = {
    "picture": ("picture", "picture_name"),
    "firmware-document": ("firmware_document", "firmware_document_name"),
    "firmware-video": ("firmware_video", "firmware_video_name"),
}
_POWER_BOX_UPLOAD_FIELDS = {
    "picture": "picture_upload",
    "firmware-document": "firmware_document_upload",
    "firmware-video": "firmware_video_upload",
}


class PowerBoxAdminForm(forms.ModelForm):
    picture_upload = forms.FileField(
        required=False,
        label="Picture",
        widget=forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.webp,.gif"}),
    )
    firmware_document_upload = forms.FileField(
        required=False,
        label="Firmware document",
        widget=forms.FileInput(attrs={"accept": ".pdf,application/pdf"}),
    )
    firmware_video_upload = forms.FileField(
        required=False,
        label="Firmware video",
        widget=forms.FileInput(attrs={"accept": ".mp4,.mov,.m4v,.webm,video/*"}),
    )

    class Meta:
        model = PowerBox
        fields = ("name", "part_number", "firmware_info", "note", "control_panel")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        box = self.instance
        if not box.pk:
            return
        for slot, (_content, name_field) in _POWER_BOX_FILE_SLOTS.items():
            filename = getattr(box, name_field)
            if not filename:
                continue
            url = reverse("admin:sauna_data_powerbox_file", args=[box.pk, slot])
            self.fields[_POWER_BOX_UPLOAD_FIELDS[slot]].help_text = _file_help(
                url,
                filename,
                _POWER_BOX_UPLOAD_FIELDS[slot],
            )

    def clean_picture_upload(self):
        return self._clean_picture("picture_upload", "Picture")

    def clean_firmware_document_upload(self):
        return _clean_limited_upload(
            self.cleaned_data.get("firmware_document_upload"),
            {".pdf"},
            "Firmware document must be a PDF file.",
            _FIRMWARE_FILE_LIMIT,
        )

    def clean_firmware_video_upload(self):
        return _clean_limited_upload(
            self.cleaned_data.get("firmware_video_upload"),
            {".mp4", ".mov", ".m4v", ".webm"},
            "Firmware video must be an MP4, MOV, M4V, or WEBM file.",
            _FIRMWARE_FILE_LIMIT,
        )

    def _clean_picture(self, field_name: str, label: str):
        return _clean_limited_upload(
            self.cleaned_data.get(field_name),
            _PICTURE_SUFFIXES,
            f"{label} must be a JPG, PNG, WEBP, or GIF file.",
        )

    def save(self, commit=True):
        box = super().save(commit=False)
        content_field, name_field, upload_field = ("picture", "picture_name", "picture_upload")
        if _clear_requested(self, upload_field):
            setattr(box, content_field, None)
            setattr(box, name_field, "")
        else:
            uploaded = self.cleaned_data.get(upload_field)
            if uploaded:
                suffix = Path(uploaded.name).suffix.lower()
                setattr(box, content_field, uploaded.read())
                setattr(box, name_field, f"picture{suffix}")
        for content_field, name_field, upload_field in (
            ("firmware_document", "firmware_document_name", "firmware_document_upload"),
            ("firmware_video", "firmware_video_name", "firmware_video_upload"),
        ):
            if _clear_requested(self, upload_field):
                setattr(box, content_field, None)
                setattr(box, name_field, "")
                continue
            uploaded = self.cleaned_data.get(upload_field)
            if uploaded:
                setattr(box, content_field, uploaded.read())
                setattr(box, name_field, _stored_upload_name(uploaded))
        if commit:
            box.save()
        return box


@admin.register(PowerBox)
class PowerBoxAdmin(EditableModelAdmin):
    form = PowerBoxAdminForm
    list_display = (
        "power_box_type",
        "part_no",
        "linked_control_panel",
        "written_note",
        "picture_files",
        "firmware_info_label",
        "linked_product_count",
        "associated_product_names",
    )
    search_fields = (
        "name",
        "part_number",
        "note",
        "products__item_no",
        "products__product_name",
    )
    ordering = ("name",)
    fields = (
        "name",
        "part_number",
        "firmware_info",
        "note",
        "control_panel",
        "picture_upload",
        "firmware_document_upload",
        "firmware_video_upload",
        "power_box_id",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("power_box_id", "created_at", "updated_at")
    autocomplete_fields = ("control_panel",)

    class Media:
        css = {"all": ("sauna_data/powerbox_admin.css",)}

    @admin.display(description="Power Box Type", ordering="name")
    def power_box_type(self, obj: PowerBox) -> str:
        return obj.name

    @admin.display(description="Part No.", ordering="part_number")
    def part_no(self, obj: PowerBox) -> str:
        return obj.part_number

    @admin.display(description="Note")
    def written_note(self, obj: PowerBox) -> str:
        return obj.note

    @admin.display(description="Control panel", ordering="control_panel__name")
    def linked_control_panel(self, obj: PowerBox):
        panel = obj.control_panel
        if panel is None:
            return "—"
        if not panel.picture_name:
            return panel.name
        url = reverse("admin:sauna_data_controlpanel_file", args=[panel.pk, "picture"])
        return format_html('<a href="{}">{}</a>', url, panel.name)

    def get_queryset(self, request):
        products = Product.objects.order_by("product_name")
        return (
            super()
            .get_queryset(request)
            .select_related("control_panel")
            .defer(
                "picture",
                "firmware_document",
                "firmware_video",
                "control_panel__picture",
                "control_panel__documentation_1",
                "control_panel__documentation_2",
            )
            .prefetch_related(Prefetch("products", queryset=products))
        )

    def get_urls(self):
        custom = [
            path(
                "<path:object_id>/file/<str:slot>/",
                self.admin_site.admin_view(self.serve_file),
                name="sauna_data_powerbox_file",
            ),
        ]
        return custom + super().get_urls()

    def serve_file(self, request, object_id, slot):
        fields = _POWER_BOX_FILE_SLOTS.get(slot)
        box = self.get_object(request, object_id)
        if fields is None or box is None:
            raise Http404
        content_field, name_field = fields
        stored = PowerBox.objects.filter(pk=box.pk).values_list(content_field, name_field).first()
        if stored is None:
            raise Http404
        content, filename = stored
        if not content or not filename:
            raise Http404
        response = HttpResponse(
            bytes(content),
            content_type=_CONTENT_TYPES.get(Path(filename).suffix.lower(), "application/octet-stream"),
        )
        response["Content-Disposition"] = content_disposition_header(False, filename)
        return response

    def _file_links(self, obj: PowerBox, slots: tuple[str, ...]):
        links = []
        for slot in slots:
            filename = getattr(obj, _POWER_BOX_FILE_SLOTS[slot][1])
            if not filename:
                continue
            url = reverse("admin:sauna_data_powerbox_file", args=[obj.pk, slot])
            links.append((url, filename))
        if not links:
            return "—"
        return format_html_join(format_html("<br>"), '<a href="{}">{}</a>', links)

    @admin.display(description="Power box pictures")
    def picture_files(self, obj: PowerBox):
        return self._file_links(obj, ("picture",))

    @admin.display(description="Firmware info", ordering="firmware_info")
    def firmware_info_label(self, obj: PowerBox) -> str:
        return obj.firmware_info or "(None)"

    @admin.display(description="Products")
    def linked_product_count(self, obj: PowerBox) -> int:
        return obj.products.count()

    @admin.display(description="Associated product names")
    def associated_product_names(self, obj: PowerBox) -> str:
        return ", ".join(
            associated_product_label(product.product_name) for product in obj.products.all()
        )


class MultiCheckboxFilter(admin.FieldListFilter):
    template = "admin/multi_checkbox_filter.html"

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.request = request
        self.selected_values = request.GET.getlist(field_path)
        self.option_values = list(
            model.objects.order_by(field_path).values_list(field_path, flat=True).distinct()
        )
        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.field_path]

    def has_output(self):
        return bool(self.option_values)

    def choices(self, changelist):
        return ()

    def queryset(self, request, queryset):
        if not self.selected_values:
            return queryset
        return queryset.filter(**{f"{self.field_path}__in": self.selected_values})

    @property
    def preserved_params(self):
        return [
            (key, self.request.GET.getlist(key))
            for key in self.request.GET
            if key != self.field_path
        ]

    @property
    def clear_query_string(self):
        params = self.request.GET.copy()
        params.pop(self.field_path, None)
        encoded = params.urlencode()
        return f"?{encoded}" if encoded else "?"


@admin.register(Product)
class ProductAdmin(EditableModelAdmin):
    list_display = (
        "product_row_id",
        "item_no",
        "product_name",
        "linked_power_box",
        "linked_control_panel",
        "voltage",
        "plug_type",
        "wattage",
        "supplier",
        "cords",
    )
    list_display_links = ("item_no",)
    list_filter = (
        ("item_no", MultiCheckboxFilter),
        ("product_name", MultiCheckboxFilter),
        "supplier",
    )
    search_fields = ("product_id", "item_no", "product_name", "supplier")
    ordering = ("product_id",)
    readonly_fields = ("product_id", "created_at", "updated_at")

    class Media:
        css = {"all": ("sauna_data/product_admin.css",)}

    @admin.display(description="ID", ordering="product_id")
    def product_row_id(self, obj: Product) -> int:
        return obj.pk

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("power_box__control_panel")
            .defer(
                "power_box__picture",
                "power_box__firmware_document",
                "power_box__firmware_video",
                "power_box__control_panel__picture",
                "power_box__control_panel__documentation_1",
                "power_box__control_panel__documentation_2",
            )
        )

    @admin.display(description="Cords", ordering="number_of_cords")
    def cords(self, obj: Product) -> int:
        return obj.number_of_cords

    @admin.display(description="Power box", ordering="power_box__name")
    def linked_power_box(self, obj: Product):
        box = obj.power_box
        if box is None:
            return "—"
        if not box.picture_name:
            return box.name
        url = reverse("catalog_file", args=["power-box", box.pk, "picture"])
        return format_html('<a href="{}">{}</a>', url, box.name)

    @admin.display(description="Control panel", ordering="power_box__control_panel__name")
    def linked_control_panel(self, obj: Product):
        box = obj.power_box
        panel = None if box is None else box.control_panel
        if panel is None:
            return "—"
        if not panel.picture_name:
            return panel.name
        url = reverse("catalog_file", args=["control-panel", panel.pk, "picture"])
        return format_html('<a href="{}">{}</a>', url, panel.name)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "product_id",
                    "item_no",
                    "product_name",
                    "voltage",
                    "plug_type",
                    ("wattage", "watt_on_label"),
                    "supplier",
                    "number_of_cords",
                    "power_box",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(ProductItem)
class ProductItemAdmin(EditableModelAdmin):
    list_display = (
        "product_item_id",
        "serial_no",
        "product",
        "qc_tester_name",
        "qc_status",
        "qc_form_name",
        "note",
    )
    list_display_links = ("serial_no",)
    list_filter = ("qc_status",)
    search_fields = (
        "serial_no",
        "product__item_no",
        "product__product_name",
        "qc_tester_name",
        "note",
        "qc_form_name",
    )
    ordering = ("serial_no",)
    autocomplete_fields = ("product",)
    readonly_fields = ("product_item_id",)
    fields = (
        "product_item_id",
        "product",
        "serial_no",
        "qc_tester_name",
        "qc_status",
        "qc_form_name",
        "note",
    )


_ADMIN_MODEL_ORDER = (
    "Product",
    "PowerBox",
    "ControlPanel",
    "ProductItem",
)


def _admin_name_list(names: list[str]):
    unique = []
    seen = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        unique.append(name)
    if not unique:
        return "—"
    return format_html_join(format_html("<br>"), "{}", ((name,) for name in unique))


def _ordered_app_list(request, app_label=None):
    app_list = admin.AdminSite.get_app_list(admin.site, request, app_label)
    order = {name: index for index, name in enumerate(_ADMIN_MODEL_ORDER)}
    for app in app_list:
        if app["app_label"] != "sauna_data":
            continue
        app["models"].sort(key=lambda model: order.get(model["object_name"], len(order)))
    return app_list


admin.site.get_app_list = _ordered_app_list
