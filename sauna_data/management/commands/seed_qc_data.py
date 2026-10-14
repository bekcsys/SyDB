from django.core.management.base import BaseCommand

from sauna_data.models import Product, ProductItem

SEED_PRODUCTS = (
    ("310203-01-wang", "Pro5.1", 110, 1840, "Global"),
    ("310203-02-wang", "Pro5.2", 110, 1940, "Global"),
    ("310203-03-wang", "Pro5.3", 220, 2390, "Global"),
    ("310203-04-wang", "Pro5.4", 220, 2440, "Global"),
    ("310203-06-wang", "Pro5.6", 220, 3940, "Global"),
    ("310211-02-wang", "CS.2", 220, 2956, "Global"),
    ("310211-04-wang", "CS.4", 220, 3840, "Global"),
    ("310211-06-wang", "CS.6", 220, 6064, "Global"),
    ("310211-08-wang", "CS.8", 220, 7664, "Global"),
    ("310211-02-Luis", "CS.2", 220, 2956, "Global"),
    ("310211-04-Luis", "CS.4", 220, 3840, "Global"),
    ("310211-06-Luis", "CS.6", 220, 6064, "Global"),
    ("310211-08-Luis", "CS.8", 220, 7664, "Global"),
    ("310211-06-EVR-Li", "CS.6-EVR1", 220, 5264, "Global"),
    ("310211-08-EVR-Li", "CS.8-EVR1", 220, 6864, "Global"),
    ("310207-01GC-wang", "Redfit Room", 220, 6823, "Global"),
    ("310207-01GC-Li", "Redfit Room", 220, 6823, "Global"),
    ("310208-C-Luis", "Redfit iGym", 220, 5584, "Global"),
    ("310208-C-wang", "Redfit iGym", 220, 5584, "Global"),
)


class Command(BaseCommand):
    help = "Load version-1 QC catalog, sample unit, and fail/pass test history."

    def handle(self, *args, **options) -> None:
        products_by_item = {}
        for item_no, product_name, voltage, wattage, supplier in SEED_PRODUCTS:
            product, _ = Product.objects.update_or_create(
                item_no=item_no,
                defaults={
                    "product_name": product_name,
                    "voltage": voltage,
                    "wattage": wattage,
                    "supplier": supplier,
                },
            )
            products_by_item[item_no] = product

        evr = products_by_item["310211-06-EVR-Li"]
        ProductItem.objects.update_or_create(
            serial_no="73204-3010",
            defaults={
                "product": evr,
                "qc_status": ProductItem.Status.TESTING,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Product.objects.count()} products, "
                f"{ProductItem.objects.count()} product items."
            )
        )
