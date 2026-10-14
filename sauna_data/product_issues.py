import re
from collections import Counter


def item_prefix(item_no: str) -> str:
    return (item_no or "").split("-", 1)[0]


def name_family(product_name: str) -> str:
    base = re.sub(r"\s*\([^)]*\)", "", product_name or "")
    base = re.sub(r"\s+with\b.*$", "", base, flags=re.IGNORECASE)
    base = re.sub(r"[.\-]\d+\b", "", base)
    base = re.sub(r"\s+", " ", base).strip(" -")
    return base or (product_name or "").strip()


def group_products(products) -> list[dict]:
    rows = list(products)
    repeated = Counter((product.item_no, product.product_name) for product in rows)
    buckets: dict[str, dict[str, list[dict]]] = {}
    for product in rows:
        prefix = item_prefix(product.item_no)
        family = name_family(product.product_name)
        label = f"{product.item_no} {product.product_name}"
        if repeated[(product.item_no, product.product_name)] > 1:
            label = f"{label} (ID {product.pk})"
        buckets.setdefault(prefix, {}).setdefault(family, []).append(
            {"id": product.pk, "label": label}
        )
    groups = []
    for prefix in sorted(buckets):
        families = []
        for family in sorted(buckets[prefix]):
            families.append(
                {
                    "name": family,
                    "products": sorted(buckets[prefix][family], key=lambda row: row["label"]),
                }
            )
        groups.append({"prefix": prefix, "families": families})
    return groups
