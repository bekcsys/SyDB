# QC Automation

Django and PostgreSQL app for sauna orders, product specs, and quality control. The public site follows the shop process. Django admin is where catalog data is maintained.

## Start

```bash
cp .env.example .env   # first time: set passwords and DJANGO_SECRET_KEY
make start
```

| Command | Action |
|---------|--------|
| `make start` | Start Postgres and Django |
| `make stop` | Stop Postgres and Django |
| `make rebuild` | Rebuild the Django image and restart it |
| `make db-backup` | Copy the Postgres volume to `data/backups/` |
| `make db-restore` | Recreate that volume from `FILE=data/backups/postgres_data_YYYY-MM-DD_HH-MM-SS.tar.gz` |
| `make migrate` | Apply database migrations |
| `make urls` | Show this machine's addresses |
| `make status` | Show whether the containers are running |
| `make reset_admin` | Set the Django admin password from `.env` |
| `make help` | List these commands |

- On this machine: http://localhost:8000/
- From another computer: `http://<this-machine-ip>:8000/` (`make urls`)
- Django admin: http://localhost:8000/admin/

Admin username and password come from `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` in `.env`. If login fails, see [docs/DJANGO_ADMIN.md](docs/DJANGO_ADMIN.md).

## Public site

The header steps match the business process:

1. **Products** — catalog: item number, voltage, plug, wattage, supplier, cords, power box, and control panel.
2. **Quality control (QC)** — one QC record per product item. Record status, tester, dates, and upload the form, video, and photos.
3. **Customer service** — look up a serial number. Order number, QC, product, and file links are view-only.

## Django admin

Models are listed in this order:

1. Products
2. Power boxes
3. Control panels
4. Power box firmware devices
5. Control panel firmware devices
6. Product items
7. QC records
8. QC testers

Product IDs are not shown. Supplier is a name on the product. Each product has one power box, and each power box has one control panel. Power box firmware devices store instruction files and can be used on more than one power box. A power box can use more than one device. A product reaches those devices through its power box. Control panel firmware devices belong to a control panel.

Control panel and firmware-device notes show on the list only after they are written. The note field is on the edit page.

## Documentation

| Guide | Contents |
|-------|----------|
| [docs/DJANGO_ADMIN.md](docs/DJANGO_ADMIN.md) | Admin login, password reset, and what each section is for |
| [docs/DATABASE.md](docs/DATABASE.md) | PostgreSQL access and the current tables |
| [docs/DATABASE_BACKUP.md](docs/DATABASE_BACKUP.md) | Copy the Postgres volume to another machine |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Host virtualenv and running Django outside Docker |
| [docs/DOCKER_HUB.md](docs/DOCKER_HUB.md) | Optional image publish and pull |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Connection refused, login, and allowed hosts |
| [docs/PGADMIN.md](docs/PGADMIN.md) | Optional pgAdmin browser |
