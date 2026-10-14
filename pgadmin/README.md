# pgAdmin

Optional PostgreSQL browser. It is a separate Docker stack from the QC app.

| Stack | Start |
|-------|--------|
| QC app (Postgres + Django) | `make start` from the repository root |
| pgAdmin | `cd pgadmin && make start` |

## Start

```bash
make start
cd pgadmin
make start
```

Wait until the command says pgAdmin is ready.

- On this machine: http://localhost:5050/
- From another computer: `http://<this-machine-ip>:5050/`

Sign in with `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` from the repository `.env`.

The server **Product Test DB** is registered on start. It uses the host port, not the Docker name `postgres`.

| Setting | Default |
|---------|---------|
| Host | `host.docker.internal` (`PGADMIN_POSTGRES_HOST`) |
| Port | `5433` (`PGADMIN_POSTGRES_PORT`) |
| Database | `sauna_tests` (`POSTGRES_DB`) |
| Username | `sauna_user` (`POSTGRES_USER`) |
| Password | `POSTGRES_PASSWORD` |

## Commands

Run these from `pgadmin/`:

| Command | Action |
|---------|--------|
| `make start` | Start pgAdmin after Postgres is up |
| `make stop` | Stop pgAdmin only |
| `make restart` | Restart pgAdmin |
| `make logs` | Follow logs |
| `make status` | Container status |
| `make reset` | Remove the pgAdmin container and its volume |
| `make urls` | Print the login URL |

`make stop` in this folder does not stop Django or Postgres. From the repository root, `make stop` stops those.

## Tables

| Table | Contents |
|-------|----------|
| `products` | Catalog, including the supplier name |
| `power_boxes` | Power boxes and their control panel |
| `control_panels` | Control panel types |
| `power_box_firmware_devices` | Firmware devices and their instruction files |
| `power_box_firmware_device_boxes` | Power boxes that can use each firmware device |
| `control_panel_firmware_devices` | Firmware devices for a control panel |
| `product_items` | Serial number, item number, optional order number, date received, and container batch |
| `qc_records` | QC status, approval, and tester for one product item |
| `qc_testers` | Tester names |

Example:

```sql
SELECT p.item_no, p.product_name, b.name AS power_box
FROM products p
LEFT JOIN power_boxes b ON b.power_box_id = p.power_box_id
ORDER BY p.product_name;
```

More: [../docs/DATABASE.md](../docs/DATABASE.md).

## Reset

If the password or server list is stuck:

```bash
make reset
make start
```

## Problems

| Issue | Fix |
|-------|-----|
| PostgreSQL is not running | `make start` from the repository root first |
| Blank page | Wait up to a minute after `make start`, then refresh |
| Password authentication failed | `POSTGRES_PASSWORD` in `../.env` must match the running database |
| Cannot connect | Host `host.docker.internal`, port **5433** (not 5432) |
| Port 5050 is in use | Set `PGADMIN_PUBLISH_PORT` in `../.env` and restart |
| Server missing | `make reset && make start` |
