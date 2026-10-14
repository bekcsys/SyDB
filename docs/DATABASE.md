# Database

PostgreSQL 16 holds the application data. Django is the application server.

| Service | Default host port | Container |
|---------|-------------------|-----------|
| Postgres | 5433 | `sauna-postgres` |
| Django | 8000 | `sauna-django` |
| pgAdmin (optional) | 5050 | separate stack in `pgadmin/` |

Database name, user, and password come from `.env` (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`). Defaults are `sauna_tests` and `sauna_user`.

## Connect

```bash
docker compose exec postgres psql -U sauna_user -d sauna_tests
```

From the host, if `psql` is installed:

```bash
psql -h localhost -p 5433 -U sauna_user -d sauna_tests
```

## Tables

| Table | Contents |
|-------|----------|
| `products` | Catalog rows keyed by item number, including the supplier name. Each product has one power box |
| `power_boxes` | Power box names, part number, one control panel, and up to three pictures |
| `control_panels` | Control panel names, part number, notes, one picture, up to three instruction PDFs, and up to two control panel update PDFs or videos |
| `power_box_firmware_devices` | Firmware devices, with up to two instruction PDFs or videos |
| `power_box_firmware_device_boxes` | Which power boxes can use each firmware device. One power box can use more than one device |
| `control_panel_firmware_devices` | Firmware devices linked to one control panel |
| `product_items` | One serial number, item number, product name, optional order number, date received, and container batch |
| `qc_records` | QC status, approval, tester, dates, notes, and upload metadata for one product item |
| `qc_testers` | QC tester names, linked from QC records |

Uploaded QC files are not in these tables. They live on disk under `data/qc_media/`.

## Example

```sql
SELECT p.item_no, p.product_name, b.name AS power_box, c.name AS control_panel
FROM products p
LEFT JOIN power_boxes b ON b.power_box_id = p.power_box_id
LEFT JOIN control_panels c ON c.control_panel_id = b.control_panel_id
ORDER BY p.product_name, b.name;
```

## Backup

```bash
make db-backup
make db-restore FILE=data/backups/postgres_data_YYYY-MM-DD_HH-MM-SS.tar.gz
```

See [DATABASE_BACKUP.md](DATABASE_BACKUP.md).
