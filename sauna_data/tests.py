from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from sauna_data.models import Product, ProductItem


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
        self.assertIn(">G</a>", content)
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
        filtered = self.client.get("/products/?supplier=smartmak")
        self.assertContains(filtered, "SmartMak unit")
        self.assertContains(filtered, ">S</a>")
        self.assertNotContains(filtered, self.product.product_name)
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
        with_file = self.client.get("/power-boxes/")
        self.assertContains(with_file, "picture_1.png")
        self.assertContains(with_file, f"/products/files/power-box/{box.pk}/picture/")
        self.assertContains(with_file, ">firmware info<")
        self.assertNotContains(with_file, "Firmware update devices")
        self.assertContains(with_file, 'target="_blank"')
        self.assertContains(with_file, "col-box-desktop")
        self.assertContains(with_file, "(None)")
        from sauna_data.models import ControlPanel

        panel = ControlPanel.objects.get(name="CP-Li")
        panel.picture_name = "picture.png"
        panel.documentation_1_name = "150F re-calibration.pdf"
        panel.save(update_fields=["picture_name", "documentation_1_name"])
        panels_page = self.client.get("/control-panels/")
        panels_section = panels_page.content.decode()
        self.assertIn(">Control panels<", panels_section)
        self.assertIn(">Firmware instruction<", panels_section)
        self.assertIn(">Control Panel instruction<", panels_section)
        self.assertIn(">Applicable products<", with_file.content.decode())
        self.assertIn(
            f'/products/{self.product.product_id}/">CS.6-EVR1</a>',
            with_file.content.decode(),
        )
        self.assertIn(">Firmware device<", panels_section)
        self.assertNotIn(">Picture<", panels_section)
        self.assertNotIn("Firmware update instruction", panels_section)
        self.assertIn(f'/products/files/control-panel/{panel.pk}/picture/" target="_blank"', panels_section)
        self.assertIn(">CP-Li</a>", panels_section)
        self.assertIn('target="_blank" rel="noopener noreferrer">150F re-calibration.pdf</a>', panels_section)
        self.assertIn("(None)", panels_section)
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
        page = self.client.get("/products/")
        content = page.content.decode()
        self.assertLess(content.index(">G</a>"), content.index(">R</a>"))
        self.assertLess(content.index(">R</a>"), content.index(">S</a>"))
        self.assertLess(content.index(">S</a>"), content.index(">Luis</a>"))
        self.assertLess(content.index(">Luis</a>"), content.index(">Wang</a>"))
        self.assertLess(content.index(">Wang</a>"), content.index(">Li</a>"))
        self.assertLess(content.index(">Li</a>"), content.index(">Pro5</a>"))
        self.assertLess(content.index(">Pro5</a>"), content.index(">CS</a>"))
        self.assertLess(content.index(">CS</a>"), content.index(">RedFit Room</a>"))
        self.assertNotIn(">EVR</a>", content)
        wang_page = self.client.get("/products/?box=wang")
        self.assertContains(wang_page, "Pro5.1")
        self.assertNotContains(wang_page, "CS.2 (Luis)")
        self.assertNotContains(wang_page, "Redfit Room")
        li_page = self.client.get("/products/?box=li")
        self.assertContains(li_page, "Redfit Room")
        self.assertNotContains(li_page, "CS.2 (Luis)")
        self.assertNotContains(li_page, "Redfit iGym (Luis)")
        pro5 = self.client.get("/products/?family=pro5")
        self.assertContains(pro5, "Pro5.1")
        self.assertNotContains(pro5, "PRO 10.1")
        self.assertNotContains(pro5, "CS.2 (Luis)")
        cs = self.client.get("/products/?family=cs")
        self.assertContains(cs, "CS.2 (Luis)")
        self.assertContains(cs, self.product.product_name)
        self.assertNotContains(cs, "Pro5.1")
        self.assertNotContains(cs, "Redfit Room")
        room = self.client.get("/products/?family=redfit")
        self.assertContains(room, "Redfit Room")
        self.assertNotContains(room, "Redfit iGym (Luis)")

    def test_customer_service_is_view_only(self) -> None:
        listing = self.client.get("/customer-service/")
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, self.unit.serial_no)
        self.assertContains(listing, "McCoy")
        self.assertNotContains(listing, "upload_slot")
        detail_url = f"/customer-service/{self.unit.product_item_id}/"
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, 200)
        html = detail.content.decode()
        self.assertIn(self.unit.serial_no, html)
        self.assertIn("McCoy", html)
        self.assertNotIn("upload_slot", html)
        self.assertNotIn("save_status", html)
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
        self.assertContains(listing, ">Product ID</a>")
        self.assertContains(listing, ">Sup</a>")
        self.assertContains(listing, ">Power box</a>")
        self.assertContains(listing, ">Control Panel</th>")
        self.assertNotContains(listing, "Powerbox picture")
        self.assertNotContains(listing, "Control panel pictures")
        self.assertNotContains(listing, "CP_firmware devices")
        self.assertNotContains(listing, ">Power box firmware devices</th>")
        self.assertNotContains(listing, "Power box type")
        self.assertContains(listing, "CS-Li")
        self.assertNotContains(listing, "CS-Li, RFR-Wang")
        detail = self.client.get(f"/products/{self.product.pk}/")
        self.assertContains(detail, "Power box type")
        self.assertContains(detail, "CS-Li")
        self.assertContains(detail, "Control panel type")
        self.assertContains(detail, "CP-Li")
        self.assertNotContains(detail, "CP-Li, CP-RFR")

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
        page = self.client.get("/power-boxes/")
        rows = page.content.decode().split("<tr>")
        v10_row = next(row for row in rows if "Luis_v1.0" in row and "Luis_v1.1" not in row)
        v11_row = next(row for row in rows if "Luis_v1.1" in row)
        self.assertIn("ACD 2", v10_row)
        self.assertNotIn("ACD 3", v10_row)
        self.assertIn('aria-label="ACD - instruction document.pdf"', v10_row)
        self.assertIn('aria-label="ACD - instruction video.mp4"', v10_row)
        self.assertIn('target="_blank"', v10_row)
        self.assertIn("M14 2H6", v10_row)
        self.assertIn("M17 10.5V7", v10_row)
        self.assertNotIn(">ACD - instruction document.pdf<", v10_row)
        self.assertIn("ACD 3", v11_row)
        self.assertNotIn("ACD 2", v11_row)

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
        listing = self.client.get("/products/")
        self.assertContains(listing, ">Product name</a>")
        self.assertNotContains(listing, "Plug type")
        self.assertNotContains(listing, "Voltage")
        self.assertNotContains(listing, "Wattage")
        self.assertNotContains(listing, "Watt on label")
        detail = self.client.get(f"/products/{self.product.pk}/")
        self.assertContains(detail, "Watt on label")
        self.assertContains(detail, "L6-20P")
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
        self.assertNotContains(page, "Order no")
        self.assertNotContains(page, "QC_Status")
        self.assertContains(page, "Firmware update instruction")
        self.assertEqual(page.content.decode().count("Firmware update instruction"), 1)
        self.assertContains(page, "Control panel instruction")
        self.assertEqual(page.content.decode().count("Control panel instruction"), 1)
        self.assertNotContains(page, "Control panel info")
        self.assertNotContains(page, "Power box info")
        self.assertContains(page, "Control panel picture")
        self.assertContains(page, "Power box picture")
        self.assertContains(page, "None")
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
        linked = self.client.get(f"/products/{self.product.pk}/")
        unit_linked = self.client.get(f"/units/{self.unit.pk}/")
        self.assertNotContains(unit_linked, "panel-guide.pdf")
        self.assertNotContains(unit_linked, "panel-update.mp4")
        self.assertNotContains(unit_linked, "box-firmware.pdf")
        self.assertContains(linked, "Firmware update instruction")
        self.assertEqual(linked.content.decode().count("Firmware update instruction"), 1)
        self.assertNotContains(linked, "Control panel firmware update")
        self.assertNotContains(linked, "Power box firmware update instruction")
        self.assertNotContains(linked, "Firmware update device")
        self.assertNotContains(linked, "Li-Device")
        self.assertNotContains(linked, "ACD2")
        linked_html = linked.content.decode()
        self.assertContains(linked, "Control panel instruction")
        self.assertLess(linked_html.index("box-firmware.pdf"), linked_html.index("panel-update.mp4"))
        self.assertLess(linked_html.index("panel-update.mp4"), linked_html.index("panel-guide.pdf"))
        self.assertContains(linked, 'class="qc-support-file-list"')
        self.assertContains(linked, "panel-guide.pdf")
        self.assertContains(linked, "panel-update.mp4")
        self.assertContains(linked, "box-firmware.pdf")
        self.assertContains(linked, "picture_1.png")
        self.assertContains(linked, 'class="qc-support-photo qc-support-photo-wide"')
        self.assertContains(linked, f"/products/{self.product.pk}/support/control-panel/{panel.pk}/picture/")
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
        luis_page = self.client.get(f"/products/{self.product.pk}/")
        self.assertNotContains(luis_page, "panel-update.mp4")
        self.assertNotContains(luis_page, "panel-guide.pdf")
        self.assertNotContains(luis_page, "Luis-Devices(ACD2, ACD3)")
        self.assertNotContains(luis_page, "Li-Device")
