from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from sauna_data.models import Product, ProductItem

UI_SRC = Path(__file__).resolve().parents[1] / "frontend" / "src"


def ui_source(name: str) -> str:
    return (UI_SRC / name).read_text()


class QcDatabaseTests(TestCase):
    def setUp(self) -> None:
        self.product = Product.objects.create(
            item_no="310211-06-EVR-Li",
            product_name="CS.6-EVR1",
            voltage=220,
            wattage=5264,
            supplier="Global",
        )
        self.unit = ProductItem.objects.create(
            serial_no="73204-3010",
            product=self.product,
            qc_status=ProductItem.Status.TESTING,
            qc_tester_name="McCoy",
        )
        viewer = get_user_model().objects.create_user("saunakb-viewer", password="viewer-pass")
        self.client.force_login(viewer)

    def test_sauna_pages_require_a_separate_login(self) -> None:
        self.client.logout()
        home = self.client.get("/")
        self.assertEqual(home.status_code, 302)
        self.assertIn("/login/", home.url)
        blocked = self.client.get("/api/products/")
        self.assertEqual(blocked.status_code, 401)
        picture = self.client.get(f"/products/{self.product.pk}/picture/")
        self.assertEqual(picture.status_code, 302)
        page = self.client.get("/login/")
        self.assertContains(page, "SaunaKB")
        self.assertContains(page, 'href="/admin/"')
        self.assertContains(page, ">Admin<")
        signed_in = self.client.post(
            "/login/",
            {"username": "saunakb-viewer", "password": "viewer-pass"},
        )
        self.assertEqual(signed_in.status_code, 302)
        self.assertEqual(signed_in.url, "/")
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        self.assertIn("/admin/login/", self.client.get("/admin/").url)

    def test_duplicate_item_no_is_a_separate_product(self) -> None:
        from sauna_data.models import PowerBox

        wang, _created = PowerBox.objects.get_or_create(name="CS-Wang")
        luis, _created = PowerBox.objects.get_or_create(name="CS-Luis")
        other = Product.objects.create(
            item_no=self.product.item_no,
            product_name=self.product.product_name,
            voltage=220,
            wattage=5264,
            supplier="Global",
            power_box=luis,
        )
        self.product.power_box = wang
        self.product.save(update_fields=["power_box"])
        self.assertNotEqual(other.product_id, self.product.product_id)
        self.assertEqual(other.power_box, luis)
        self.assertEqual(other.power_box.control_panel.name, "CP-Luis")
        self.assertEqual(self.product.power_box.control_panel.name, "CP-wang")
        item = ProductItem.objects.create(serial_no="73204-3012", product=other)
        second = ProductItem.objects.create(serial_no="73204-3013", product=other)
        self.assertEqual(item.product_id, other.product_id)
        self.assertEqual(second.product_id, other.product_id)
        self.assertNotEqual(item.serial_no, second.serial_no)
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_constraint WHERE conname = 'products_item_no_key'")
            self.assertIsNone(cursor.fetchone())

    def test_duplicate_serial_rejected(self) -> None:
        with self.assertRaises(IntegrityError):
            ProductItem.objects.create(serial_no="73204-3010", product=self.product)

    def test_voltage_not_positive_rejected(self) -> None:
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                item_no="bad-voltage",
                product_name="Bad",
                voltage=0,
                wattage=1000,
                supplier="Global",
            )

    def test_wattage_not_positive_rejected(self) -> None:
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                item_no="bad-wattage",
                product_name="Bad",
                voltage=110,
                wattage=0,
                supplier="Global",
            )

    def test_invalid_unit_status_rejected(self) -> None:
        self.unit.qc_status = "NOT_A_STATUS"
        with self.assertRaises(IntegrityError):
            self.unit.save(update_fields=["qc_status"])

    def test_product_item_order_number_is_optional(self) -> None:
        warehouse = ProductItem.objects.create(serial_no="73204-9999", product=self.product)
        self.assertEqual(warehouse.product_id, self.product.product_id)
        self.assertEqual(warehouse.qc_tester_name, "")
        self.assertEqual(warehouse.note, "")
        self.assertEqual(warehouse.qc_form_name, "")
        self.assertFalse(hasattr(warehouse, "order_no"))
        self.assertEqual(warehouse.qc_status, ProductItem.Status.ASSIGNED)

    def test_qc_status_and_note_save_on_the_item(self) -> None:
        from sauna_data.forms import PhysicalUnitQcForm

        form = PhysicalUnitQcForm(
            {
                "product": self.product.pk,
                "qc_tester_name": "Tyron",
                "qc_status": ProductItem.Status.QC_PASSED,
                "note": "ready",
            },
            instance=self.unit,
        )
        self.assertTrue(form.is_valid())
        unit = form.save()
        self.assertEqual(unit.qc_tester_name, "Tyron")
        self.assertEqual(unit.qc_status, ProductItem.Status.QC_PASSED)
        self.assertEqual(unit.note, "ready")

    def test_picture_uploads_are_renamed_in_sequence(self) -> None:
        from sauna_data.qc_uploads import next_slot_filename

        first = next_slot_filename("front", [], "porch.JPG")
        second = next_slot_filename("front", [first], "door.png")
        self.assertEqual(first, "front_1.jpg")
        self.assertEqual(second, "front_2.png")
        third = next_slot_filename("video", [], "clip.MOV")
        fourth = next_slot_filename("video", [third], "clip2.mp4")
        self.assertEqual(third, "video_1.mov")
        self.assertEqual(fourth, "video_2.mp4")
        from datetime import datetime
        from zoneinfo import ZoneInfo

        stamp = datetime(2026, 9, 28, 16, 20, 5, tzinfo=ZoneInfo("America/Chicago"))
        self.assertEqual(
            next_slot_filename(
                "form",
                [],
                "report.PDF",
                serial="73204-3010",
                uploaded_at=stamp,
            ),
            "73204-3010_2026-09-28_162005.pdf",
        )

    def test_form_upload_uses_serial_and_upload_time(self) -> None:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        from sauna_data.qc_uploads import next_slot_filename

        stamp = datetime(2026, 9, 28, 16, 20, 5, tzinfo=ZoneInfo("America/Chicago"))
        self.assertEqual(
            next_slot_filename(
                "form",
                [],
                "report.PDF",
                serial="73204-3010",
                uploaded_at=stamp,
            ),
            "73204-3010_2026-09-28_162005.pdf",
        )

    def test_picture_sides_allow_at_most_five_files(self) -> None:
        from sauna_data.qc_uploads import slot_max_files

        self.assertEqual(slot_max_files("front"), 5)
        self.assertEqual(slot_max_files("inside_ceiling"), 5)
        self.assertEqual(slot_max_files("form"), 1)
        self.assertIsNone(slot_max_files("video"))

    def test_product_delete_is_protected_by_its_items(self) -> None:
        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_unit_deletes_without_a_test_run_table(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.test_runs')")
            self.assertIsNone(cursor.fetchone()[0])
        self.assertFalse(hasattr(self.unit, "test_runs"))
        item_id = self.unit.product_item_id
        self.unit.delete()
        self.assertFalse(ProductItem.objects.filter(pk=item_id).exists())
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.qc_records')")
            self.assertIsNone(cursor.fetchone()[0])

    def test_qc_passed_query(self) -> None:
        passed = ProductItem.objects.create(
            serial_no="73204-3011",
            product=self.product,
            qc_status=ProductItem.Status.QC_PASSED,
        )
        serials = list(
            ProductItem.objects.filter(qc_status=ProductItem.Status.QC_PASSED).values_list(
                "serial_no", flat=True
            )
        )
        self.assertEqual(serials, [passed.serial_no])

    def test_high_use_indexes_exist(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename IN ('products', 'product_items')
                """
            )
            defs = " ".join(row[0] for row in cursor.fetchall()).lower()
        for fragment in (
            "serial_no",
            "qc_status",
        ):
            self.assertIn(fragment, defs)
        self.assertNotIn("products_item_no", defs)

    def test_product_list_displays_supplier_and_cords(self) -> None:
        self.assertFalse(hasattr(self.product, "supplier_id"))
        self.assertEqual(self.product.supplier, "Global")
        self.assertEqual(self.product.public_supplier_label(), "G")
        self.assertEqual(Product(supplier="SmartMak").public_supplier_label(), "S")
        self.assertEqual(Product(supplier="Royal").public_supplier_label(), "R")
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.suppliers')")
            self.assertIsNone(cursor.fetchone()[0])
        self.assertEqual(self.product.number_of_cords, 1)
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        catalog = self.client.get("/api/products/").json()
        supplier_labels = [item["label"] for item in catalog["filters"]["suppliers"]]
        self.assertIn("G", supplier_labels)
        self.assertNotIn("Global", supplier_labels)
        self.assertNotIn("SmartMak", supplier_labels)
        self.assertNotIn("Royal", supplier_labels)
        self.assertNotIn(">Global<", content)
        self.assertNotIn(">SmartMak<", content)
        self.assertNotIn(">Royal<", content)
        Product.objects.create(
            item_no="smartmak-anon",
            product_name="SmartMak unit",
            voltage=220,
            wattage=1000,
            supplier="SmartMak",
        )
        filtered = self.client.get("/api/products/?supplier=smartmak").json()
        filtered_names = [row["name"] for row in filtered["products"]]
        self.assertIn("SmartMak unit", filtered_names)
        self.assertIn("S", [row["supplier_label"] for row in filtered["products"]])
        self.assertNotIn(self.product.product_name, filtered_names)
        self.assertIn(">Products</a>", content)
        self.assertIn(">Power boxes</a>", content)
        self.assertIn(">Control panels</a>", content)
        self.assertIn(">Firmware instructions</a>", content)
        self.assertIn(">QC &amp; CS</a>", content)
        self.assertNotIn("wusa-logo.png", content)
        self.assertNotIn(">Quality control (QC)</a>", content)
        self.assertNotIn(">Customer service</a>", content)
        self.assertNotIn("<summary>Power boxes</summary>", content)
        self.assertNotIn("<summary>Power box firmware devices</summary>", content)
        self.assertNotIn("<summary>Control panel firmware devices</summary>", content)
        from sauna_data.models import PowerBox

        box = PowerBox.objects.get(name="CS-Li")
        box.picture = b"png-bytes"
        box.picture_name = "picture_1.png"
        box.save(update_fields=["picture", "picture_name"])
        self.product.power_box = box
        self.product.save(update_fields=["power_box"])
        with_file = self.client.get("/api/power-boxes/")
        self.assertEqual(with_file.status_code, 200)
        power_boxes = with_file.json()["power_boxes"]
        li_box = next(row for row in power_boxes if row["name"] == "CS-Li")
        self.assertEqual(li_box["pictures"][0]["name"], "picture_1.png")
        self.assertEqual(li_box["pictures"][0]["url"], f"/products/files/power-box/{box.pk}/picture/")
        self.assertIn("firmware_info", li_box)
        self.assertIn("(None)", [row["firmware_display"] for row in power_boxes])
        self.assertNotIn("Firmware update devices", with_file.content.decode())
        power_ui = ui_source("PowerBoxesPage.jsx")
        self.assertIn('target="_blank"', power_ui)
        self.assertIn(">Applicable products<", power_ui)
        self.assertIn("aria-label={file.name}", power_ui)
        self.assertIn(
            {"name": "CS.6-EVR1", "url": f"/products/{self.product.product_id}/"},
            li_box["products"],
        )
        from sauna_data.models import ControlPanel

        panel = ControlPanel.objects.get(name="CP-Li")
        panel.picture_name = "picture.png"
        panel.documentation_1_name = "150F re-calibration.pdf"
        panel.save(update_fields=["picture_name", "documentation_1_name"])
        panels_page = self.client.get("/api/control-panels/")
        panels = panels_page.json()["control_panels"]
        cp_li = next(row for row in panels if row["name"] == "CP-Li")
        panel_ui = ui_source("ControlPanelsPage.jsx")
        self.assertIn('title="Control panels"', panel_ui)
        self.assertIn(">Firmware instruction<", panel_ui)
        self.assertIn(">CP instruction<", panel_ui)
        self.assertIn(">Firmware device<", panel_ui)
        self.assertNotIn(">Picture<", panel_ui)
        self.assertNotIn("Firmware update instruction", panel_ui)
        self.assertIn('target="_blank"', panel_ui)
        self.assertEqual(cp_li["picture"][0]["url"], f"/products/files/control-panel/{panel.pk}/picture/")
        self.assertEqual(cp_li["firmware_instruction_name"], "150F re-calibration.pdf")
        self.assertIn("(None)", [row["firmware_device_display"] for row in panels] + [row["panel_instruction_name"] for row in panels])
        downloaded = self.client.get(f"/products/files/power-box/{box.pk}/picture/")
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.content, b"png-bytes")
        self.assertNotIn('name="supplier_id"', content)
        self.assertNotIn('name="number_of_cords"', content)
        self.assertEqual(
            self.client.post(f"/products/{self.product.product_id}/supplier/").status_code,
            404,
        )
        self.assertEqual(
            self.client.post(f"/products/{self.product.product_id}/cords/").status_code,
            404,
        )
        get_user_model().objects.create_superuser("catalog-admin", "admin@example.com", "pass")
        self.client.login(username="catalog-admin", password="pass")
        admin_page = self.client.get(f"/admin/sauna_data/product/{self.product.pk}/change/")
        self.assertEqual(admin_page.status_code, 200)
        admin_html = admin_page.content.decode()
        self.assertIn('name="supplier"', admin_html)
        self.assertIn("<select", admin_html)
        self.assertIn('name="number_of_cords"', admin_html)
        self.assertIn("Product id", admin_html)
        product_list = self.client.get("/admin/sauna_data/product/")
        product_html = product_list.content.decode()
        self.assertLess(product_html.index("column-product_row_id"), product_html.index("column-item_no"))
        self.assertIn(">ID</a>", product_html)
        self.assertIn("By item no", product_html)
        self.assertIn("By product name", product_html)
        self.assertIn('name="item_no"', product_html)
        self.assertIn('name="product_name"', product_html)
        self.assertIn('type="checkbox"', product_html)
        from urllib.parse import urlencode

        query = urlencode([
            ("item_no", self.product.item_no),
            ("item_no", "smartmak-anon"),
        ])
        filtered = self.client.get(f"/admin/sauna_data/product/?{query}")
        filtered_html = filtered.content.decode()
        result_rows = filtered_html.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        self.assertIn(self.product.product_name, result_rows)
        self.assertIn("SmartMak unit", result_rows)
        single = self.client.get(f"/admin/sauna_data/product/?item_no={self.product.item_no}")
        single_rows = single.content.decode().split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        self.assertIn(self.product.product_name, single_rows)
        self.assertNotIn("SmartMak unit", single_rows)
        self.assertEqual(self.client.get("/admin/sauna_data/supplier/").status_code, 404)
        self.assertEqual(self.client.get("/admin/sauna_data/order/").status_code, 404)
        self.assertEqual(self.client.get("/admin/sauna_data/testrun/").status_code, 404)
        self.assertEqual(self.client.get("/orders/").status_code, 404)
        self.assertEqual(self.client.get("/tests/").status_code, 404)

    def test_product_page_filters_supplier_box_and_family(self) -> None:
        from sauna_data.models import PowerBox

        wang = PowerBox.objects.get(name="CS-Wang")
        luis = PowerBox.objects.get(name="CS-Luis")
        li = PowerBox.objects.get(name="CS-Li")
        Product.objects.create(
            item_no="pro5-filter",
            product_name="Pro5.1",
            voltage=220,
            wattage=1000,
            supplier="Global",
            power_box=wang,
        )
        Product.objects.create(
            item_no="pro10-filter",
            product_name="PRO 10.1",
            voltage=220,
            wattage=1000,
            supplier="SmartMak",
            power_box=wang,
        )
        Product.objects.create(
            item_no="cs-filter",
            product_name="CS.2 (Luis)",
            voltage=220,
            wattage=1000,
            supplier="Global",
            power_box=luis,
        )
        Product.objects.create(
            item_no="room-filter",
            product_name="Redfit Room",
            voltage=220,
            wattage=1000,
            supplier="Royal",
            power_box=li,
        )
        Product.objects.create(
            item_no="igym-filter",
            product_name="Redfit iGym (Luis)",
            voltage=220,
            wattage=1000,
            supplier="Global",
            power_box=luis,
        )
        page = self.client.get("/api/products/")
        filters = page.json()["filters"]
        labels = [item["label"] for item in filters["suppliers"] + filters["boxes"] + filters["families"]]
        self.assertEqual(
            labels,
            ["G", "R", "S", "Luis", "Wang", "Li", "Pro5", "CS", "RedFit Room"],
        )
        self.assertNotIn("EVR", labels)

        def names(response):
            return [row["name"] for row in response.json()["products"]]

        wang_page = self.client.get("/api/products/?box=wang")
        self.assertIn("Pro5.1", names(wang_page))
        self.assertNotIn("CS.2 (Luis)", names(wang_page))
        self.assertNotIn("Redfit Room", names(wang_page))
        li_page = self.client.get("/api/products/?box=li")
        self.assertIn("Redfit Room", names(li_page))
        self.assertNotIn("CS.2 (Luis)", names(li_page))
        self.assertNotIn("Redfit iGym (Luis)", names(li_page))
        pro5 = self.client.get("/api/products/?family=pro5")
        self.assertIn("Pro5.1", names(pro5))
        self.assertNotIn("PRO 10.1", names(pro5))
        self.assertNotIn("CS.2 (Luis)", names(pro5))
        cs = self.client.get("/api/products/?family=cs")
        self.assertIn("CS.2 (Luis)", names(cs))
        self.assertIn(self.product.product_name, names(cs))
        self.assertNotIn("Pro5.1", names(cs))
        self.assertNotIn("Redfit Room", names(cs))
        room = self.client.get("/api/products/?family=redfit")
        self.assertIn("Redfit Room", names(room))
        self.assertNotIn("Redfit iGym (Luis)", names(room))

    def test_customer_service_is_view_only(self) -> None:
        listing = self.client.get("/customer-service/")
        self.assertEqual(listing.status_code, 200)
        self.assertNotContains(listing, "upload_slot")
        records = self.client.get("/api/units/").json()["units"]
        self.assertIn(self.unit.serial_no, [row["serial_no"] for row in records])
        self.assertIn("McCoy", [row["qc_tester_name"] for row in records])
        detail_url = f"/customer-service/{self.unit.product_item_id}/"
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, 200)
        html = detail.content.decode()
        self.assertIn(self.unit.serial_no, html)
        record = self.client.get(f"/api/units/{self.unit.product_item_id}/").json()
        self.assertEqual(record["qc_tester_name"], "McCoy")
        self.assertNotIn("upload_slot", html)
        self.assertNotIn("save_status", html)
        self.assertNotIn("<form", html)
        note = self.unit.note
        response = self.client.post(detail_url, {"note": "changed by service", "action": "save_status"})
        self.assertEqual(response.status_code, 405)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.note, note)

    def test_each_product_has_one_power_box_and_one_control_panel(self) -> None:
        from sauna_data.forms import ProductNameField
        from sauna_data.models import PowerBox
        from sauna_data.power_boxes import (
            POWER_BOX_NAMES,
            associated_product_label,
            power_box_name_for,
        )

        self.assertEqual(
            power_box_name_for("CS.2 (wang)", "310211-02-wang", "Global"),
            "CS-Wang",
        )
        self.assertEqual(
            power_box_name_for("Pro5.1", "310203-01-wang", "Global"),
            "CS-Pro5-Wang",
        )
        self.assertEqual(
            power_box_name_for("CS.6-EVR1 (Li power box)", "310211-06-EVR-Li", "Global"),
            "CS-Li",
        )
        self.assertEqual(
            power_box_name_for("CS.2 (Luis with App)", "310211-02-Luis", "Global"),
            "CS-Luis",
        )
        self.assertEqual(power_box_name_for("Pro18.2", "310303-02", "Royal"), "Royal-PowerBox")
        self.assertEqual(
            power_box_name_for("PRO 10.1", "310103-01C", "SmartMak"),
            "SmMak_v1.0",
        )
        self.assertEqual(
            power_box_name_for("PRO 10.3", "310103-03C", "SmartMak"),
            "SmMak_v1.0",
        )
        self.assertEqual(
            power_box_name_for("RedFuzion Rejuve Wooden Door", "310104-02-WD", "SmartMak"),
            "SmMak_v1.0",
        )
        self.assertEqual(
            associated_product_label("CS.6-EVR1 (Li power box)"),
            "CS.6-EVR1",
        )
        self.assertEqual(
            associated_product_label("Redfit Room (Li power box)"),
            "Redfit Room",
        )
        self.assertEqual(
            associated_product_label("PRO 10.1 (with floor heater)"),
            "PRO 10.1 (with floor heater)",
        )
        original_name = self.product.product_name
        box, _created = PowerBox.objects.get_or_create(name="CS-Li")
        self.product.power_box = box
        self.product.save(update_fields=["power_box"])
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_name, original_name)
        self.assertEqual(self.product.power_box, box)
        self.assertFalse(Product.objects.filter(product_name__in=POWER_BOX_NAMES).exists())
        label = ProductNameField(queryset=Product.objects.all()).label_from_instance(self.product)
        self.assertEqual(label, "CS.6-EVR1")
        self.assertNotIn("310211-06-EVR-Li", label)
        from sauna_data.control_panels import control_panel_name_for

        self.assertEqual(control_panel_name_for("CS-Wang-2"), "CP-wang")
        self.assertEqual(control_panel_name_for("CS-Pro5-Wang"), "CP-wang")
        self.assertEqual(control_panel_name_for("RFR-Wang-1"), "CP-RFR")
        self.assertEqual(control_panel_name_for("CS-Li"), "CP-Li")
        self.assertEqual(control_panel_name_for("CS-Luis"), "CP-Luis")
        self.assertIsNone(control_panel_name_for("Royal-PowerBox"))
        self.assertEqual(box.control_panel.name, "CP-Li")
        self.assertEqual(PowerBox.objects.get(name="CS-Wang").control_panel.name, "CP-wang")
        self.assertEqual(PowerBox.objects.get(name="CS-Luis").control_panel.name, "CP-Luis")
        self.assertIsNone(PowerBox.objects.get(name="SmMak_v1.0").control_panel)
        listing = self.client.get("/products/")
        products_ui = ui_source("ProductsPage.jsx")
        self.assertIn('label="Product ID"', products_ui)
        self.assertIn('label="Sup"', products_ui)
        self.assertIn('label="Power box"', products_ui)
        self.assertIn(">Control Panel</th>", products_ui)
        self.assertNotContains(listing, "Powerbox picture")
        self.assertNotContains(listing, "Control panel pictures")
        self.assertNotContains(listing, "CP_firmware devices")
        self.assertNotContains(listing, ">Power box firmware devices</th>")
        self.assertNotContains(listing, "Power box type")
        catalog = self.client.get("/api/products/").json()
        row = next(item for item in catalog["products"] if item["id"] == self.product.product_id)
        self.assertEqual(row["power_box"]["name"], "CS-Li")
        self.assertNotIn(",", row["power_box"]["name"])
        detail = self.client.get(f"/api/products/{self.product.pk}/").json()
        detail_ui = ui_source("ProductDetailPage.jsx")
        self.assertIn(">Power box type<", detail_ui)
        self.assertEqual(detail["power_box"], "CS-Li")
        self.assertIn(">Control panel type<", detail_ui)
        self.assertEqual(detail["control_panel"], "CP-Li")
        self.assertNotIn(",", detail["control_panel"])

    def test_smmak_products_use_one_power_box(self) -> None:
        from sauna_data.models import PowerBox
        from sauna_data.power_boxes import SMMAK_V10, assign_smmak_power_boxes

        v10 = PowerBox.objects.get(name=SMMAK_V10)
        retired = PowerBox.objects.create(name="SmMak_v1.1", control_panel=v10.control_panel)
        units = (
            "310103-01C",
            "310103-02C",
            "310104-02",
            "310103-03C",
            "310103-04C",
            "310103-06C",
        )
        created = []
        for item_no in units:
            created.append(
                Product.objects.create(
                    item_no=item_no,
                    product_name=item_no,
                    voltage=220,
                    wattage=1000,
                    supplier="SmartMak",
                    power_box=retired,
                )
            )
        assign_smmak_power_boxes(PowerBox, Product)
        self.assertFalse(PowerBox.objects.filter(name="SmMak_v1.1").exists())
        for product in created:
            product.refresh_from_db()
            self.assertEqual(product.power_box, v10)

    def test_luis_power_boxes_use_matching_firmware_devices(self) -> None:
        from sauna_data.models import PowerBox
        from sauna_data.qc_support import product_page_catalog

        first = PowerBox.objects.create(
            name="Luis_v1.0",
            firmware_info="ACD 2",
            firmware_document_name="ACD - instruction document.pdf",
            firmware_video_name="ACD - instruction video.mp4",
        )
        second = PowerBox.objects.create(name="Luis_v1.1", firmware_info="ACD 3")
        catalog = product_page_catalog()
        info_for = {row["name"]: row["firmware_info"] for row in catalog["power_boxes"]}
        self.assertEqual(info_for["Luis_v1.0"], "ACD 2")
        self.assertEqual(info_for["Luis_v1.1"], "ACD 3")
        page = self.client.get("/api/power-boxes/")
        rows = {row["name"]: row for row in page.json()["power_boxes"]}
        v10_row = rows["Luis_v1.0"]
        v11_row = rows["Luis_v1.1"]
        self.assertEqual(v10_row["firmware_info"], "ACD 2")
        self.assertNotIn("ACD 3", v10_row["firmware_info"])
        firmware_names = [item["name"] for item in v10_row["firmware_files"]]
        self.assertEqual(
            firmware_names,
            ["ACD - instruction document.pdf", "ACD - instruction video.mp4"],
        )
        self.assertFalse(v10_row["firmware_files"][0]["video"])
        self.assertTrue(v10_row["firmware_files"][1]["video"])
        power_ui = ui_source("PowerBoxesPage.jsx")
        self.assertIn("aria-label={file.name}", power_ui)
        self.assertIn('target="_blank"', power_ui)
        self.assertIn("file.video ? <VideoIcon /> : <DocIcon />", power_ui)
        self.assertEqual(v11_row["firmware_info"], "ACD 3")
        self.assertNotIn("ACD 2", v11_row["firmware_info"])
        self.assertEqual(v11_row["firmware_files"], [])

    def test_firmware_devices_are_split_by_parent(self) -> None:
        from django.contrib.auth import get_user_model

        from sauna_data.models import ControlPanel, PowerBox

        luis = PowerBox.objects.get(name="CS-Luis")
        self.assertEqual(luis.firmware_info, "ACD 2, ACD 3")
        self.assertEqual(ControlPanel.objects.get(name="CP-Li").firmware_device, "E-PGM+")
        self.assertEqual(
            ControlPanel.objects.get(name="CP-wang").firmware_device,
            "Wang CP Unlock Device",
        )
        get_user_model().objects.create_superuser("firmware-admin", "firmware@example.com", "pass")
        self.client.login(username="firmware-admin", password="pass")
        self.assertEqual(self.client.get("/admin/sauna_data/powerboxfirmwaredevice/").status_code, 404)
        self.assertEqual(self.client.get("/admin/sauna_data/controlpanelfirmwaredevice/").status_code, 404)
        luis.picture = b"png-bytes"
        luis.picture_name = "picture_1.png"
        luis.save(update_fields=["picture", "picture_name"])
        panel = luis.control_panel
        panel.picture = b"panel-bytes"
        panel.picture_name = "picture.png"
        panel.save(update_fields=["picture", "picture_name"])
        self.product.power_box = luis
        self.product.save(update_fields=["power_box"])
        product_list = self.client.get("/admin/sauna_data/product/")
        product_html = product_list.content.decode()
        self.assertLess(product_html.index("column-product_name"), product_html.index("column-linked_power_box"))
        self.assertLess(product_html.index("column-linked_power_box"), product_html.index("column-linked_control_panel"))
        self.assertIn(">Power box<", product_html)
        self.assertIn(">Control panel<", product_html)
        self.assertNotIn(">CP firmware<", product_html)
        self.assertNotIn(">Box firmware<", product_html)
        self.assertIn(f"/products/files/power-box/{luis.pk}/picture/", product_html)
        self.assertIn(f"/products/files/control-panel/{panel.pk}/picture/", product_html)
        self.assertIn(">CS-Luis</a>", product_html)
        self.assertIn(">CP-Luis</a>", product_html)

    def test_plug_type_follows_voltage_and_label_watt_is_detail_only(self) -> None:
        self.assertEqual(self.product.plug_type, Product.PlugType.L6_20P)
        low_voltage = Product.objects.create(
            item_no="110-plug",
            product_name="Low voltage",
            voltage=110,
            wattage=1000,
            supplier="Global",
        )
        self.assertEqual(low_voltage.plug_type, Product.PlugType.NEMA_5_20P)
        listing = self.client.get("/api/products/")
        self.assertIn('label="Product name"', ui_source("ProductsPage.jsx"))
        self.assertNotContains(listing, "Plug type")
        self.assertNotContains(listing, "Voltage")
        self.assertNotContains(listing, "Wattage")
        self.assertNotContains(listing, "Watt on label")
        detail = self.client.get(f"/api/products/{self.product.pk}/")
        self.assertIn(">Watt on label<", ui_source("ProductDetailPage.jsx"))
        self.assertContains(detail, "L6-20P")
        self.assertIsNone(detail.json()["watt_on_label"])
        get_user_model().objects.create_superuser("plug-admin", "plug@example.com", "pass")
        self.client.login(username="plug-admin", password="pass")
        admin_page = self.client.get(f"/admin/sauna_data/product/{self.product.pk}/change/")
        admin_html = admin_page.content.decode()
        self.assertIn('name="plug_type"', admin_html)
        self.assertIn("<select", admin_html)
        self.assertIn("NEMA 5-20P", admin_html)
        self.assertIn("L6-20P", admin_html)
        self.assertIn('name="watt_on_label"', admin_html)
        self.assertIn("field-wattage field-watt_on_label", admin_html)
        self.assertIn('name="picture_upload"', admin_html)
        self.assertIn('className="spec-layout"', ui_source("ProductDetailPage.jsx"))
        self.assertIn(">Known issues<", ui_source("UnitPage.jsx"))
        self.assertIn('title="Common product issues and solutions"', ui_source("UnitsPage.jsx"))
        self.assertIn('title="QC info"', ui_source("UnitsPage.jsx"))
        self.assertIn("useState(false)", ui_source("UnitsPage.jsx"))
        self.assertNotIn("Search product items", ui_source("UnitsPage.jsx"))

    def test_control_panel_has_no_supplier(self) -> None:
        from sauna_data.models import ControlPanel

        panel = ControlPanel.objects.get(name="CP-wang")
        self.assertFalse(hasattr(panel, "supplier_id"))
        get_user_model().objects.create_superuser("panel-admin", "panel@example.com", "pass")
        self.client.login(username="panel-admin", password="pass")
        listing = self.client.get("/admin/sauna_data/controlpanel/")
        html = listing.content.decode()
        self.assertLess(html.index("column-name"), html.index("column-part_number"))
        self.assertLess(html.index("column-part_number"), html.index("column-written_note"))
        self.assertNotIn("column-supplier", html)
        self.assertNotContains(listing, 'name="supplier"')
        self.assertNotContains(listing, 'name="part_number"')
        edit = self.client.get(f"/admin/sauna_data/controlpanel/{panel.pk}/change/")
        edit_html = edit.content.decode()
        self.assertNotIn('name="supplier"', edit_html)
        self.assertIn('name="part_number"', edit_html)

    def test_power_box_part_number_is_empty_and_edited_on_change_page(self) -> None:
        from sauna_data.models import PowerBox

        box = PowerBox.objects.get(name="CS-Li")
        self.assertEqual(box.part_number, "")
        self.assertEqual(box.note, "")
        self.product.power_box = box
        self.product.save(update_fields=["power_box"])
        get_user_model().objects.create_superuser("box-admin", "box@example.com", "pass")
        self.client.login(username="box-admin", password="pass")
        listing = self.client.get("/admin/sauna_data/powerbox/")
        html = listing.content.decode()
        self.assertLess(html.index("column-power_box_type"), html.index("column-part_no"))
        self.assertLess(html.index("column-part_no"), html.index("column-linked_control_panel"))
        self.assertLess(html.index("column-linked_control_panel"), html.index("column-written_note"))
        self.assertIn(">Power Box Type<", html)
        self.assertNotIn("column-supply_voltage", html)
        self.assertNotIn(">Voltage<", html)
        self.assertIn(">Part No.<", html)
        self.assertIn(">Note<", html)
        self.assertIn("(None)", html)
        self.assertNotContains(listing, 'name="part_number"')
        self.assertNotContains(listing, 'name="note"')
        edit = self.client.get(f"/admin/sauna_data/powerbox/{box.pk}/change/")
        self.assertContains(edit, 'name="part_number"')
        self.assertContains(edit, 'name="note"')

    def test_power_box_pictures_and_firmware_pdfs_are_stored_in_the_database(self) -> None:
        from django.core.files.uploadedfile import SimpleUploadedFile

        from sauna_data.models import PowerBox

        box = PowerBox.objects.get(name="CS-Li")
        self.assertIsNone(box.picture)
        self.assertFalse(hasattr(box, "firmware_instruction"))
        get_user_model().objects.create_superuser("box-file-admin", "box-file@example.com", "pass")
        self.client.login(username="box-file-admin", password="pass")
        listing = self.client.get("/admin/sauna_data/powerbox/")
        html = listing.content.decode()
        self.assertLess(html.index("column-linked_control_panel"), html.index("column-picture_files"))
        self.assertIn(">Power box pictures<", html)
        panel = box.control_panel
        panel.picture_name = "picture.png"
        panel.save(update_fields=["picture_name"])
        linked = self.client.get("/admin/sauna_data/powerbox/")
        self.assertContains(
            linked,
            f'/admin/sauna_data/controlpanel/{panel.pk}/file/picture/',
        )
        self.assertContains(linked, f">{panel.name}</a>")
        self.assertNotIn("column-firmware_files", html)
        self.assertNotContains(listing, 'name="picture_upload"')
        self.assertNotContains(listing, 'name="firmware_upload"')
        change_url = f"/admin/sauna_data/powerbox/{box.pk}/change/"
        edit = self.client.get(change_url)
        self.assertContains(edit, 'name="picture_upload"')
        self.assertContains(edit, 'name="firmware_info"')
        self.assertContains(edit, 'name="firmware_document_upload"')
        self.assertNotContains(edit, 'name="picture_upload_2"')
        saved = self.client.post(
            change_url,
            {
                "name": box.name,
                "part_number": "",
                "firmware_info": "ACD 2",
                "note": "",
                "control_panel": box.control_panel_id or "",
                "picture_upload": SimpleUploadedFile("a.png", b"pic-1", content_type="image/png"),
                "firmware_document_upload": SimpleUploadedFile("guide.pdf", b"%PDF-box", content_type="application/pdf"),
                "_save": "Save",
            },
        )
        self.assertEqual(saved.status_code, 302, saved.content.decode()[:500] if saved.status_code != 302 else "")
        box.refresh_from_db()
        self.assertEqual(bytes(box.picture), b"pic-1")
        self.assertEqual(box.picture_name, "picture.png")
        self.assertEqual(box.firmware_info, "ACD 2")
        self.assertEqual(bytes(box.firmware_document), b"%PDF-box")
        self.assertEqual(box.firmware_document_name, "guide.pdf")
        edit_again = self.client.get(change_url)
        self.assertContains(edit_again, 'name="picture_upload_clear"')
        deleted = self.client.post(
            change_url,
            {
                "name": box.name,
                "part_number": "",
                "firmware_info": "ACD 2",
                "note": "",
                "control_panel": box.control_panel_id or "",
                "picture_upload_clear": "1",
                "_save": "Save",
            },
        )
        self.assertEqual(deleted.status_code, 302)
        box.refresh_from_db()
        self.assertIsNone(box.picture)
        self.assertEqual(box.picture_name, "")
        self.assertEqual(bytes(box.firmware_document), b"%PDF-box")

    def test_control_panel_pictures_and_instruction_are_stored_in_the_database(self) -> None:
        from django.core.files.uploadedfile import SimpleUploadedFile

        from sauna_data.models import ControlPanel

        panel = ControlPanel.objects.get(name="CP-Li")
        self.assertIsNone(panel.picture)
        self.assertEqual(panel.documentation_1_name, "")
        get_user_model().objects.create_superuser("file-admin", "file@example.com", "pass")
        self.client.login(username="file-admin", password="pass")
        listing = self.client.get("/admin/sauna_data/controlpanel/")
        html = listing.content.decode()
        self.assertLess(html.index("column-written_note"), html.index("column-picture_file"))
        self.assertLess(html.index("column-picture_file"), html.index("column-documentation_files"))
        self.assertNotContains(listing, 'name="picture_upload"')
        self.assertNotContains(listing, 'name="documentation_upload"')
        change_url = f"/admin/sauna_data/controlpanel/{panel.pk}/change/"
        edit = self.client.get(change_url)
        self.assertContains(edit, 'name="picture_upload"')
        self.assertNotContains(edit, 'name="front_upload"')
        self.assertContains(edit, 'name="documentation_upload"')
        self.assertContains(edit, 'name="documentation_upload_2"')
        self.assertContains(edit, 'name="firmware_device"')
        self.assertNotContains(edit, 'name="instruction_upload_3"')
        picture = SimpleUploadedFile("collage.png", b"picture-bytes", content_type="image/png")
        instruction = SimpleUploadedFile("guide.pdf", b"%PDF-1.4", content_type="application/pdf")
        instruction_2 = SimpleUploadedFile("wiring.pdf", b"%PDF-2", content_type="application/pdf")
        saved = self.client.post(
            change_url,
            {
                "name": "CP-Luis (with App)",
                "part_number": "",
                "firmware_device": "E-PGM+",
                "note": "",
                "picture_upload": picture,
                "documentation_upload": instruction,
                "documentation_upload_2": instruction_2,
                "_save": "Save",
            },
        )
        self.assertEqual(saved.status_code, 302)
        panel.refresh_from_db()
        self.assertEqual(bytes(panel.picture), b"picture-bytes")
        self.assertEqual(panel.picture_name, "picture.png")
        self.assertFalse(hasattr(panel, "front_picture"))
        self.assertEqual(bytes(panel.documentation_1), b"%PDF-1.4")
        self.assertEqual(bytes(panel.documentation_2), b"%PDF-2")
        self.assertEqual(panel.documentation_1_name, "guide.pdf")
        self.assertEqual(panel.documentation_2_name, "wiring.pdf")
        self.assertEqual(panel.firmware_device, "E-PGM+")
        kept = self.client.post(
            change_url,
            {
                "name": "CP-Luis (with App)",
                "part_number": "",
                "firmware_device": "E-PGM+",
                "note": "kept",
                "_save": "Save",
            },
        )
        self.assertEqual(kept.status_code, 302)
        panel.refresh_from_db()
        self.assertEqual(panel.note, "kept")
        self.assertEqual(bytes(panel.picture), b"picture-bytes")
        self.assertEqual(panel.picture_name, "picture.png")
        self.assertEqual(bytes(panel.documentation_1), b"%PDF-1.4")
        self.assertEqual(bytes(panel.documentation_2), b"%PDF-2")
        downloaded = self.client.get(f"/admin/sauna_data/controlpanel/{panel.pk}/file/documentation/")
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.content, b"%PDF-1.4")
        self.assertEqual(downloaded["Content-Type"], "application/pdf")
        rejected = self.client.post(
            change_url,
            {
                "name": "CP-Luis (with App)",
                "part_number": "",
                "firmware_device": "E-PGM+",
                "note": "kept",
                "documentation_upload": SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain"),
                "_save": "Save",
            },
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertContains(rejected, "Instruction must be a PDF file.")
        panel.refresh_from_db()
        self.assertEqual(panel.documentation_1_name, "guide.pdf")
        edit_again = self.client.get(change_url)
        self.assertContains(edit_again, 'name="picture_upload_clear"')
        self.assertContains(edit_again, 'name="documentation_upload_2_clear"')
        deleted = self.client.post(
            change_url,
            {
                "name": "CP-Luis (with App)",
                "part_number": "",
                "firmware_device": "E-PGM+",
                "note": "kept",
                "picture_upload_clear": "1",
                "documentation_upload_2_clear": "1",
                "_save": "Save",
            },
        )
        self.assertEqual(deleted.status_code, 302)
        panel.refresh_from_db()
        self.assertIsNone(panel.picture)
        self.assertEqual(panel.picture_name, "")
        self.assertIsNone(panel.documentation_2)
        self.assertEqual(panel.documentation_2_name, "")
        self.assertEqual(panel.documentation_1_name, "guide.pdf")

    def test_qc_support_lists_related_panel_and_power_box_files(self) -> None:
        from sauna_data.models import ControlPanel, PowerBox

        unit_page = self.client.get(f"/units/{self.unit.pk}/")
        self.assertNotContains(unit_page, "Product details")
        self.assertNotContains(unit_page, "220 V")
        self.assertNotContains(unit_page, "L6-20P")
        self.assertNotContains(unit_page, "5264 W")
        self.assertNotContains(unit_page, "Firmware update instruction")
        self.assertNotContains(unit_page, "Control panel instruction")
        self.assertNotContains(unit_page, "Control panel picture")
        self.assertNotContains(unit_page, "Power box picture")
        page = self.client.get(f"/products/{self.product.pk}/")
        detail_ui = ui_source("ProductDetailPage.jsx")
        self.assertNotContains(page, "Order no")
        self.assertNotContains(page, "QC_Status")
        self.assertEqual(detail_ui.count("Firmware instruction"), 1)
        self.assertEqual(detail_ui.count("Control panel instruction"), 1)
        self.assertNotIn("Control panel info", detail_ui)
        self.assertNotIn("Power box info", detail_ui)
        self.assertIn("Control panel picture", detail_ui)
        self.assertIn("Power box picture", detail_ui)
        self.assertIn(">None<", detail_ui)
        self.assertNotContains(page, "Li-Device")
        box = PowerBox.objects.get(name="CS-Li")
        panel = box.control_panel
        panel.documentation_1 = b"%PDF-support"
        panel.documentation_1_name = "panel-guide.pdf"
        panel.picture = b"front-photo"
        panel.picture_name = "picture.png"
        panel.save(
            update_fields=[
                "documentation_1",
                "documentation_1_name",
                "picture",
                "picture_name",
            ]
        )
        box.picture = b"png-bytes"
        box.picture_name = "picture_1.png"
        box.firmware_document = b"%PDF-box"
        box.firmware_document_name = "box-firmware.pdf"
        box.firmware_video = b"update-video"
        box.firmware_video_name = "panel-update.mp4"
        box.save(
            update_fields=[
                "picture",
                "picture_name",
                "firmware_document",
                "firmware_document_name",
                "firmware_video",
                "firmware_video_name",
            ]
        )
        self.product.power_box = box
        self.product.save(update_fields=["power_box"])
        linked = self.client.get(f"/api/products/{self.product.pk}/")
        unit_linked = self.client.get(f"/units/{self.unit.pk}/")
        self.assertNotContains(unit_linked, "panel-guide.pdf")
        self.assertNotContains(unit_linked, "panel-update.mp4")
        self.assertNotContains(unit_linked, "box-firmware.pdf")
        linked_html = linked.content.decode()
        self.assertNotIn("Control panel firmware update", linked_html)
        self.assertNotIn("Power box firmware update instruction", linked_html)
        self.assertNotIn("Firmware update device", linked_html)
        self.assertNotIn("Li-Device", linked_html)
        self.assertNotIn("ACD2", linked_html)
        payload = linked.json()
        names = [item["name"] for item in payload["firmware_updates"]]
        names += [item["name"] for item in payload["panel_instructions"]]
        self.assertEqual(names, ["box-firmware.pdf", "panel-update.mp4", "panel-guide.pdf"])
        self.assertIn('className="qc-support-file-list"', detail_ui)
        self.assertIn("picture_1.png", linked_html)
        self.assertIn("qc-support-photo-wide", detail_ui)
        self.assertIn(
            f"/products/{self.product.pk}/support/control-panel/{panel.pk}/picture/",
            linked_html,
        )
        downloaded = self.client.get(
            f"/products/{self.product.pk}/support/control-panel/{panel.pk}/documentation/"
        )
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.content, b"%PDF-support")
        video = self.client.get(
            f"/products/{self.product.pk}/support/power-box/{box.pk}/firmware-video/"
        )
        self.assertEqual(video["Content-Type"], "video/mp4")
        other = ControlPanel.objects.get(name="CP-wang")
        other.documentation_1 = b"secret"
        other.documentation_1_name = "secret.pdf"
        other.save(update_fields=["documentation_1", "documentation_1_name"])
        hidden = self.client.get(
            f"/products/{self.product.pk}/support/control-panel/{other.pk}/documentation/"
        )
        self.assertEqual(hidden.status_code, 404)
        luis_box = PowerBox.objects.get(name="CS-Luis")
        self.product.power_box = luis_box
        self.product.save(update_fields=["power_box"])
        luis_page = self.client.get(f"/api/products/{self.product.pk}/")
        self.assertNotContains(luis_page, "panel-update.mp4")
        self.assertNotContains(luis_page, "panel-guide.pdf")
        self.assertNotContains(luis_page, "Luis-Devices(ACD2, ACD3)")
        self.assertNotContains(luis_page, "Li-Device")

    def test_open_issues_exclude_solved_and_link_to_the_section(self) -> None:
        from datetime import date

        from sauna_data.models import ProductIssue

        ProductIssue.objects.create(
            date=date(2026, 10, 10),
            status=ProductIssue.Status.SOLVED,
        ).products.add(self.product)
        ProductIssue.objects.create(
            date=date(2026, 10, 12),
            status=ProductIssue.Status.IN_PROGRESS,
        ).products.add(self.product)
        ProductIssue.objects.create(
            date=date(2026, 10, 14),
            status=ProductIssue.Status.NOT_STARTED,
        ).products.add(self.product)
        listing = self.client.get("/api/products/").json()
        row = next(item for item in listing["products"] if item["id"] == self.product.pk)
        self.assertEqual(row["known_issues"], 3)
        detail = self.client.get(f"/api/products/{self.product.pk}/").json()
        self.assertEqual(detail["known_issue_count"], 3)
        self.assertEqual(
            [issue["status"] for issue in detail["issues"]],
            ["NOT_STARTED", "IN_PROGRESS", "SOLVED"],
        )
        blocked = self.client.post(
            f"/api/products/{self.product.pk}/issues/",
            {"date": "2026-10-14", "status": "SOLVED"},
        )
        self.assertEqual(blocked.status_code, 404)
        self.assertEqual(self.client.get(f"/api/products/{self.product.pk}/").json()["known_issue_count"], 3)
        products_ui = ui_source("ProductsPage.jsx")
        self.assertIn('label="Known Issues"', products_ui)
        self.assertIn("#product-issues", products_ui)
        detail_ui = ui_source("ProductDetailPage.jsx")
        self.assertIn('title="SPEC"', detail_ui)
        self.assertIn('title="KNOWN ISSUES"', detail_ui)
        self.assertNotIn("Add issue", detail_ui)
        self.assertNotIn("ID {product.id}", detail_ui)

    def test_issue_admin_groups_products_by_family_and_item_prefix(self) -> None:
        from types import SimpleNamespace

        from sauna_data.product_issues import group_products

        groups = group_products(
            [
                SimpleNamespace(pk=1, item_no="310203-01", product_name="Pro5.1"),
                SimpleNamespace(pk=2, item_no="310203-06", product_name="Pro5.6"),
                SimpleNamespace(pk=3, item_no="310211-02", product_name="CS.2 (Luis)"),
            ]
        )
        self.assertEqual(groups[0]["prefix"], "310203")
        self.assertEqual(groups[0]["families"][0]["name"], "Pro5")
        self.assertEqual([row["id"] for row in groups[0]["families"][0]["products"]], [1, 2])
        Product.objects.create(
            item_no="310203-02",
            product_name="Pro5.2",
            voltage=110,
            wattage=1000,
            supplier="Global",
        )
        get_user_model().objects.create_superuser("issue-admin", "issue@example.com", "pass")
        self.client.login(username="issue-admin", password="pass")
        page = self.client.get("/admin/sauna_data/productissue/add/")
        html = page.content.decode()
        self.assertEqual(page.status_code, 200)
        self.assertNotIn('name="product"', html)
        self.assertIn('name="products"', html)
        self.assertIn("All Pro5 · 310203", html)
        self.assertIn("Pro5.2", html)

    def test_issue_admin_filters_supplier_power_box_and_shows_item_numbers(self) -> None:
        from datetime import date

        from sauna_data.models import PowerBox, ProductIssue

        global_box, _created = PowerBox.objects.get_or_create(name="Luis_v1.0")
        royal_box, _created = PowerBox.objects.get_or_create(name="Royal_v1.0")
        global_product = Product.objects.create(
            item_no="310203-01",
            product_name="Pro5.1",
            voltage=110,
            wattage=1000,
            supplier="Global",
            power_box=global_box,
        )
        royal_product = Product.objects.create(
            item_no="310303-02",
            product_name="WellPRO 18.2",
            voltage=220,
            wattage=1000,
            supplier="Royal",
            power_box=royal_box,
        )
        global_issue = ProductIssue.objects.create(
            date=date(2026, 10, 14),
            status=ProductIssue.Status.NOT_STARTED,
            note="Global latch",
        )
        global_issue.products.add(global_product)
        royal_issue = ProductIssue.objects.create(
            date=date(2026, 10, 13),
            status=ProductIssue.Status.NOT_STARTED,
            note="Royal hinge",
        )
        royal_issue.products.add(royal_product)
        get_user_model().objects.create_superuser("issue-filter", "filter@example.com", "pass")
        self.client.login(username="issue-filter", password="pass")
        listing = self.client.get("/admin/sauna_data/productissue/")
        self.assertContains(listing, "By supplier")
        self.assertContains(listing, "By power box type")
        self.assertContains(listing, 'name="supplier"')
        self.assertContains(listing, 'name="power_box"')
        self.assertContains(listing, "310203-01")
        self.assertContains(listing, "310303-02")
        filtered = self.client.get("/admin/sauna_data/productissue/?supplier=Global&power_box=Luis_v1.0")
        rows = filtered.content.decode().split("<tbody>", 1)[1].split("</tbody>", 1)[0]
        self.assertIn("Global latch", rows)
        self.assertIn("310203-01", rows)
        self.assertNotIn("Royal hinge", rows)

    def test_issue_note_and_pdf_documentation(self) -> None:
        from datetime import date

        from sauna_data.models import ProductIssue

        issue = ProductIssue.objects.create(
            date=date(2026, 10, 14),
            status=ProductIssue.Status.NOT_STARTED,
            note="Door will not latch",
        )
        issue.products.add(self.product)
        detail = self.client.get(f"/api/products/{self.product.pk}/").json()
        self.assertEqual(detail["issues"][0]["note"], "Door will not latch")
        self.assertIn(">Note<", ui_source("ProductDetailPage.jsx"))
        self.assertNotIn("Add issue", ui_source("ProductDetailPage.jsx"))
        blocked = self.client.post(
            f"/api/products/{self.product.pk}/issues/{issue.pk}/",
            {"date": "2026-10-14", "status": "SOLVED", "note": "Changed from the product page"},
        )
        self.assertEqual(blocked.status_code, 404)
        issue.refresh_from_db()
        self.assertEqual(issue.note, "Door will not latch")

        get_user_model().objects.create_superuser("issue-docs", "docs@example.com", "pass")
        self.client.login(username="issue-docs", password="pass")
        from sauna_data.models import ControlPanel, PowerBox

        panel = ControlPanel.objects.create(name="CP-issue-doc")
        panel.documentation_1 = b"%PDF-panel"
        panel.documentation_1_name = "panel-guide.pdf"
        panel.documentation_2 = b"%PDF-cp"
        panel.documentation_2_name = "cp-guide.pdf"
        panel.save()
        box = PowerBox.objects.create(name="Box-issue-doc")
        box.firmware_document = b"%PDF-box"
        box.firmware_document_name = "box-firmware.pdf"
        box.save()
        panel_ref = f"control-panel:{panel.pk}:documentation"
        box_ref = f"power-box:{box.pk}:firmware-document"
        change = f"/admin/sauna_data/productissue/{issue.pk}/change/"
        page = self.client.get(change)
        self.assertContains(page, 'name="doc_ref"')
        self.assertContains(page, 'name="support_doc_upload"')
        self.assertContains(page, "panel-guide.pdf")
        self.assertContains(page, "cp-guide.pdf")
        self.assertContains(page, "box-firmware.pdf")
        self.assertNotContains(page, 'name="documentation_upload"')
        from django.core.files.uploadedfile import SimpleUploadedFile

        saved = self.client.post(
            change,
            {
                "products": [str(self.product.pk)],
                "date": "2026-10-14",
                "status": "IN_PROGRESS",
                "note": "Latch sticks on the left side",
                "doc_ref": panel_ref,
                "support_doc_upload": SimpleUploadedFile(
                    "latch-notes.pdf", b"%PDF-support", content_type="application/pdf"
                ),
            },
        )
        self.assertEqual(saved.status_code, 302)
        issue.refresh_from_db()
        self.assertEqual(issue.note, "Latch sticks on the left side")
        self.assertEqual(issue.doc_ref, panel_ref)
        self.assertEqual(issue.support_doc_name, "latch-notes.pdf")
        self.assertEqual(bytes(issue.support_doc), b"%PDF-support")
        detail = self.client.get(f"/api/products/{self.product.pk}/").json()
        self.assertEqual(detail["issues"][0]["documentation_name"], "CP-issue-doc · panel-guide.pdf")
        downloaded = self.client.get(detail["issues"][0]["documentation_url"])
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.content, b"%PDF-panel")
        support = self.client.get(detail["issues"][0]["support_doc_url"])
        self.assertEqual(support.status_code, 200)
        self.assertEqual(support.content, b"%PDF-support")
        unit_payload = self.client.get(f"/api/units/{self.unit.pk}/").json()
        self.assertEqual(unit_payload["issues"][0]["support_doc_name"], "latch-notes.pdf")
        catalog = self.client.get("/api/units/").json()["issues"]
        listed = next(row for row in catalog if row["id"] == issue.pk)
        self.assertEqual(listed["impacted_products"], 1)
        self.assertEqual(listed["products"][0]["name"], self.product.product_name)
        self.assertEqual(listed["support_doc_name"], "latch-notes.pdf")
        listing = self.client.get("/admin/sauna_data/productissue/")
        self.assertContains(listing, "IssueID")
        self.assertContains(listing, ">Doc<")
        self.assertContains(listing, box_ref)
        kept = self.client.post(
            change,
            {
                "products": [str(self.product.pk)],
                "date": "2026-10-14",
                "status": "IN_PROGRESS",
                "note": "Still sticks",
                "doc_ref": panel_ref,
            },
        )
        self.assertEqual(kept.status_code, 302)
        issue.refresh_from_db()
        self.assertEqual(issue.note, "Still sticks")
        self.assertEqual(issue.doc_ref, panel_ref)
