# Django admin

Staff edit catalog and QC records at http://localhost:8000/admin/. From another computer, use `http://<this-machine-ip>:8000/admin/` (`make urls`).

The public site at http://localhost:8000/ does not ask for a login. Admin does.

## Login

| Setting in `.env` | Purpose |
|-------------------|---------|
| `DJANGO_SUPERUSER_USERNAME` | Login name |
| `DJANGO_SUPERUSER_PASSWORD` | Login password |
| `DJANGO_SUPERUSER_EMAIL` | Stored on the account; not used to sign in |

The account is created on the first `make start` when it does not already exist.

## Reset the admin password

1. Set `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` in `.env`.
2. Run `make reset_admin` while the stack is up.
3. Open http://localhost:8000/admin/ and sign in with those values.

Or set a password interactively:

```bash
docker compose exec django_web python manage.py changepassword admin
```

## Sections

| Section | What it holds |
|---------|----------------|
| Products | Item number, name, voltage, plug, wattage, label watt, supplier name, cords, and one power box. The list has separate control_panel_firmware and power box firmware columns. Product ID is hidden. The power box is a dropdown on the edit page. Supplier is text stored on the product. |
| Power boxes | Named boxes, an optional part number, and one control panel. Part number is text on the list and edited on the change page. Pictures accepts up to three images, named picture_1, picture_2, and picture_3. Files are uploaded on the edit page and stored in the database. A Delete checkbox on that page removes a saved file. Each product points at one box. |
| Control panels | CP types. Part number is text on the list and edited on the change page. Picture accepts one image. The instruction column accepts up to three PDF files, uploaded on the edit page. Control panel update accepts up to two PDF or video files. The picture and the PDFs are stored in the database. A Delete checkbox on the edit page removes a saved file. Each power box points at one panel. Note text shows on the list only when a note has been saved. |
| Power box firmware devices | Devices such as Luis-ACD2 and Luis-ACD3. A power box can use more than one device, and a device can be used on more than one power box. ACD2 and ACD3 are both used on the Luis power boxes. The list columns are Device_name, power_box, and instruction_document. Power boxes and instruction files are edited on the change page. |
| Control panel firmware devices | Devices linked to one control panel, including the RFR EVR1 re-calibration file on CP-Li and the CS-CP unlock file on CP-wang. The list columns are cp_device_name, control_panel, and instruction_document. |
| Product items | One serial number, an optional revised serial number for reconciliation, item number, product name, optional order number, PO date, proforma, date received, container batch, and an optional shipped-to destination. |
| QC records | QC status, approval, tester, and dates for one product item. Testers are assigned here. |
| QC testers | People who can be assigned on a QC record. |

## Other staff users

A user can open `/admin/` only when **Active** and **Staff status** are both on.

| Permission | Result |
|------------|--------|
| Can view | Read-only forms |
| Can change | Can edit existing rows |
| Can add / Can delete | Create or remove rows |
| Superuser | All of the above |

Grant change rights from the project directory:

```bash
docker compose exec django_web python manage.py grant_admin_edit_permissions USERNAME
```

`make reset_admin` updates only the superuser from `.env`. For anyone else:

```bash
docker compose exec django_web python manage.py changepassword THEIR_USERNAME
```

## pgAdmin

Django admin edits application records. pgAdmin is a separate optional SQL browser. See [PGADMIN.md](PGADMIN.md).
