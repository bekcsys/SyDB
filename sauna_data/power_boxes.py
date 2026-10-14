import re

_POWER_BOX_NOTE = re.compile(
    r"\s*\((?:li power box|wang power box|wang|luis with app)\)\s*$",
    re.IGNORECASE,
)

SMMAK_V10 = "SmMak_v1.0"
SMMAK_ITEM_NOS = (
    "310103-01C",
    "310103-02C",
    "310104-02",
    "310103-03C",
    "310103-04C",
    "310103-06C",
)
LUIS_FIRMWARE = (
    ("Luis_v1.0", "Luis-ACD2"),
    ("Luis_v1.1", "Luis-ACD3"),
)

POWER_BOX_NAMES = (
    "CS-Wang",
    "CS-Pro5-Wang",
    "CS-Li",
    "CS-Luis",
    "Royal-PowerBox",
    SMMAK_V10,
)


def _item_matches(item_no: str, item_numbers: tuple[str, ...]) -> bool:
    item = (item_no or "").casefold()
    for code in item_numbers:
        normalized = code.casefold()
        if item == normalized or item.startswith(normalized + "-"):
            return True
    return False


def smmak_power_box_name(item_no: str) -> str | None:
    if _item_matches(item_no, SMMAK_ITEM_NOS):
        return SMMAK_V10
    return None


def assign_smmak_power_boxes(power_box_model, product_model, assignment_model=None) -> None:
    v10 = power_box_model.objects.filter(name=SMMAK_V10).first()
    if v10 is None:
        legacy = power_box_model.objects.filter(
            name__in=("SmartMak-PowerBox", "SmMak-v1", "SmMak_v1")
        ).first()
        if legacy is not None:
            legacy.name = SMMAK_V10
            legacy.save(update_fields=["name"])
            v10 = legacy
        else:
            v10 = power_box_model.objects.create(name=SMMAK_V10)
    retired = power_box_model.objects.filter(name="SmMak_v1.1").first()
    if retired is not None and retired.pk != v10.pk:
        product_model.objects.filter(power_box_id=retired.pk).update(power_box_id=v10.pk)
        if assignment_model is not None:
            for link in assignment_model.objects.filter(power_box_id=retired.pk):
                assignment_model.objects.get_or_create(
                    power_box_firmware_device_id=link.power_box_firmware_device_id,
                    power_box_id=v10.pk,
                )
            assignment_model.objects.filter(power_box_id=retired.pk).delete()
        retired.delete()
    product_model.objects.filter(item_no__in=SMMAK_ITEM_NOS).update(power_box_id=v10.pk)


def link_luis_acd2(power_box_model, device_model, assignment_model) -> None:
    for box_name, device_name in LUIS_FIRMWARE:
        box = power_box_model.objects.filter(name=box_name).first()
        device = device_model.objects.filter(name=device_name).first()
        if box is None or device is None:
            continue
        assignment_model.objects.filter(power_box_id=box.pk).exclude(
            power_box_firmware_device_id=device.pk
        ).delete()
        assignment_model.objects.get_or_create(
            power_box_firmware_device_id=device.pk,
            power_box_id=box.pk,
        )


def power_box_name_for(product_name: str, item_no: str, supplier_name: str) -> str | None:
    name = (product_name or "").casefold()
    item = (item_no or "").casefold()
    supplier = (supplier_name or "").casefold()
    compact = "".join(name.split())
    smmak_box = smmak_power_box_name(item_no)
    if smmak_box:
        return smmak_box
    if "pro10" in compact or "redfuzion" in compact or "rejuve" in name:
        return SMMAK_V10
    if supplier == "royal" or compact.startswith("pro18") or compact.startswith("pro22"):
        return "Royal-PowerBox"
    if compact.startswith("pro5"):
        return "CS-Pro5-Wang"
    if "li power" in name or "evr" in compact or "evr" in item:
        return "CS-Li"
    if "luis" in name or "luis" in item:
        return "CS-Luis"
    if "wang" in name or "wang" in item:
        return "CS-Wang"
    return None


def associated_product_label(product_name: str) -> str:
    return _POWER_BOX_NOTE.sub("", product_name or "").strip()
