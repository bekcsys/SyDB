from __future__ import annotations

from django.db import models


class Product(models.Model):
    class PlugType(models.TextChoices):
        NEMA_5_20P = "NEMA 5-20P", "NEMA 5-20P"
        L6_20P = "L6-20P", "L6-20P"

    PLUG_BY_VOLTAGE = {
        110: PlugType.NEMA_5_20P,
        220: PlugType.L6_20P,
    }

    product_id = models.BigAutoField(primary_key=True)
    item_no = models.CharField(
        max_length=64,
        help_text="Not unique. product_id identifies the product. Each product has one power box.",
    )
    product_name = models.CharField(max_length=128)
    voltage = models.PositiveIntegerField()
    wattage = models.PositiveIntegerField()
    supplier = models.CharField(max_length=64)
    number_of_cords = models.PositiveIntegerField(default=1)
    plug_type = models.CharField(
        max_length=32,
        choices=PlugType.choices,
        blank=True,
        default="",
    )
    watt_on_label = models.PositiveIntegerField(null=True, blank=True)
    power_box = models.ForeignKey(
        "PowerBox",
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(voltage__gt=0),
                name="products_voltage_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(wattage__gt=0),
                name="products_wattage_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(number_of_cords__gte=1),
                name="products_number_of_cords_min_1",
            ),
            models.CheckConstraint(
                condition=models.Q(plug_type__in=["", "NEMA 5-20P", "L6-20P"]),
                name="products_plug_type_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(watt_on_label__isnull=True) | models.Q(watt_on_label__gt=0),
                name="products_watt_on_label_positive",
            ),
        ]

    def save(self, *args, **kwargs) -> None:
        mapped = self.PLUG_BY_VOLTAGE.get(self.voltage)
        if mapped:
            self.plug_type = mapped
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"plug_type"}
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.item_no} / {self.product_name}"

    def public_supplier_label(self) -> str:
        key = "".join(self.supplier.casefold().split())
        return {"global": "G", "smartmak": "S", "royal": "R"}.get(key, self.supplier)

    def power_box_type_label(self) -> str:
        if self.power_box_id is None:
            return ""
        return self.power_box.name

    def control_panel_type_label(self) -> str:
        box = self.power_box
        if box is None or box.control_panel_id is None:
            return ""
        return box.control_panel.name


class ControlPanel(models.Model):
    control_panel_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64, unique=True)
    part_number = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Part number",
    )
    picture = models.BinaryField(null=True, blank=True, editable=False)
    picture_name = models.CharField(max_length=255, blank=True, default="")
    documentation_1 = models.BinaryField(null=True, blank=True, editable=False)
    documentation_1_name = models.CharField(max_length=255, blank=True, default="")
    documentation_2 = models.BinaryField(null=True, blank=True, editable=False)
    documentation_2_name = models.CharField(max_length=255, blank=True, default="")
    firmware_device = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="Firmware device",
    )
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "control_panels"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class PowerBox(models.Model):
    power_box_id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=64,
        unique=True,
        help_text=(
            "SmartMak units use SmMak_v1.0 "
            "(item numbers 310103-01C, 310103-02C, 310104-02, "
            "310103-03C, 310103-04C, 310103-06C)."
        ),
    )
    part_number = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Part number",
    )
    note = models.TextField(blank=True, default="")
    control_panel = models.ForeignKey(
        ControlPanel,
        on_delete=models.PROTECT,
        related_name="power_boxes",
        null=True,
        blank=True,
    )
    picture = models.BinaryField(null=True, blank=True, editable=False)
    picture_name = models.CharField(max_length=255, blank=True, default="")
    firmware_info = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="Firmware info",
    )
    firmware_document = models.BinaryField(null=True, blank=True, editable=False)
    firmware_document_name = models.CharField(max_length=255, blank=True, default="")
    firmware_video = models.BinaryField(null=True, blank=True, editable=False)
    firmware_video_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "power_boxes"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class ProductItem(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Assigned"
        TESTING = "TESTING", "Testing"
        QC_PASSED = "QC_PASSED", "QC passed"
        QC_FAILED = "QC_FAILED", "QC failed"
        ON_HOLD = "ON_HOLD", "On hold"

    product_item_id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="product_items",
        null=True,
    )
    serial_no = models.CharField(max_length=64, unique=True)
    qc_tester_name = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="QC tester name",
    )
    qc_status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ASSIGNED,
        verbose_name="QC status",
    )
    qc_form = models.BinaryField(null=True, blank=True, editable=False)
    qc_form_name = models.CharField(max_length=255, blank=True, default="", verbose_name="QC form")
    note = models.TextField(blank=True, default="", verbose_name="Note")

    class Meta:
        db_table = "product_items"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    qc_status__in=[
                        "ASSIGNED",
                        "TESTING",
                        "QC_PASSED",
                        "QC_FAILED",
                        "ON_HOLD",
                    ]
                ),
                name="product_items_qc_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["qc_status"], name="idx_product_items_qc_status"),
        ]

    def __str__(self) -> str:
        return self.serial_no
