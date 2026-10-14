# Development

`make start` builds Django inside the `sauna-django` container. Use a host virtualenv only when you run Django on the machine itself.

## One-time setup

```bash
./scripts/setup_venv.sh
cp .env.example .env
```

Point host commands at the published Postgres port:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

Postgres is already started by `make start`. To start only the database:

```bash
docker compose up -d postgres
```

## Host commands

```bash
source scripts/activate_venv.sh
python manage.py migrate
python manage.py test sauna_data
python manage.py createsuperuser
```

Or migrate and run the development server:

```bash
./scripts/run_dev.sh
```

The Docker app does not mount the source tree. After code changes, run `make rebuild`.

## Django superuser

```bash
docker compose exec django_web python manage.py createsuperuser
```

Or set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, and `DJANGO_SUPERUSER_EMAIL` in `.env` before the first `make start`.

QC photos, video, and forms are stored under `data/qc_media/`. That folder is mounted into the container. A database dump does not include those files.
