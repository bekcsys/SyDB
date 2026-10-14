# Database backup and restore

PostgreSQL data lives in the Docker volume `postgres_data`, not in the Django image. Backup copies that volume. Restore creates the volume on this machine and fills it from the archive.

| What | Survives `make rebuild`? | Survives `make stop`? | Survives a new machine? |
|------|--------------------------|-----------------------|-------------------------|
| Database volume | Yes | Yes | Only if you restore a volume archive |
| `data/qc_media/` | Yes, it is a folder in this repo | Yes | Only if you copy the folder |
| `data/backups/` | Yes | Yes | Only if you copy the archive |

## Backup

```bash
make db-backup
```

Postgres stops for the copy, then starts again. The archive is timestamped:

`data/backups/postgres_data_2026-09-28_21-46-26.tar.gz`

Copy that file off this machine. Also copy `.env` and `data/qc_media/` if the QC photos, video, and forms should come along. Catalog pictures and instruction files are inside the volume.

## Restore on this machine

This replaces the current Postgres volume.

```bash
make db-restore FILE=data/backups/postgres_data_2026-09-28_21-46-26.tar.gz
```

## New machine

1. Clone this repository.
2. Copy `.env` from the old machine. Django uses that password to connect, and the password stored in the volume must be the same one.
3. Copy the `.tar.gz` archive into `data/backups/`.
4. Restore before the first start:

```bash
make db-restore FILE=data/backups/postgres_data_YYYY-MM-DD_HH-MM-SS.tar.gz
```

That creates this machine's Postgres volume, loads the archive into it, and starts Postgres and Django. The folder name can differ from the old machine. The archive is the data directory, and this project attaches it to the local volume.

5. Copy `data/qc_media/` from the old machine if those uploaded files should come back.

Use the same Postgres major version (the image is `postgres:16`). Do not run `make start` before the restore. A first start creates an empty database, and the restore then replaces it.

## What deletes the database

```bash
docker compose down -v
```

That removes the Postgres volume. `make stop` does not.

Find the volume name with `docker volume ls` before deleting one by hand.
