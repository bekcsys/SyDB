# WebApp — run from this directory: cd WebApp && make <target>
SHELL := /bin/bash
COMPOSE := docker compose
DJANGO := $(COMPOSE) exec -T django_web python manage.py
ROOT := $(CURDIR)
VENV_PY := $(ROOT)/.venv/bin/python
IMPORT_PENDING := $(ROOT)/data/import_pending
ARCHIVE_OK := $(ROOT)/data/archive/db_migrated
ARCHIVE_FAIL := $(ROOT)/data/archive/import_failed

.PHONY: help start stop rebuild migrate setup env import importcsv logs status urls reset_admin docker-build docker-push docker-publish db-backup db-restore

help:
	@echo "QC Automation:"
	@echo "  make start        Start Postgres and Django"
	@echo "  make stop         Stop Postgres and Django"
	@echo "  make rebuild      Rebuild the Django image and restart it"
	@echo "  make db-backup    Copy the Postgres volume to data/backups/"
	@echo "  make db-restore   Recreate the volume from FILE=data/backups/postgres_data_YYYY-MM-DD_HH-MM-SS.tar.gz"
	@echo "  make migrate      Apply database migrations"
	@echo "  make urls         Show local and LAN addresses"
	@echo "  make status       Show container status"
	@echo "  make reset_admin  Set the admin password from .env"
	@echo "  make help         Show this list"

env:
	@if [[ ! -f .env ]]; then cp .env.example .env && echo "Created .env from .env.example"; fi

setup: env
	@./scripts/setup_venv.sh

start: env
	$(COMPOSE) up -d --build postgres django_web
	@echo ""
	@port=$${DJANGO_PUBLISH_PORT:-8000}; \
	lan_ip=$$(hostname -I 2>/dev/null | awk '{print $$1}'); \
	echo "QC Automation is running:"; \
	echo "  On this machine: http://localhost:$$port/"; \
	if [[ -n "$$lan_ip" ]]; then \
	  echo "  From the LAN:    http://$$lan_ip:$$port/"; \
	fi; \
	echo "  Admin:           http://localhost:$$port/admin/"

rebuild: env
	$(COMPOSE) up -d --build --force-recreate django_web
	@echo ""
	@echo "Django rebuilt: http://localhost:$${DJANGO_PUBLISH_PORT:-8000}/"

stop:
	$(COMPOSE) down

db-backup: env
	@./scripts/postgres_volume.sh backup

db-restore: env
	@./scripts/postgres_volume.sh restore "$(FILE)"

migrate: env
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx django_web; then \
		$(DJANGO) migrate --noinput; \
	elif [[ -x $(VENV_PY) ]]; then \
		POSTGRES_HOST=$${POSTGRES_HOST:-localhost} POSTGRES_PORT=$${POSTGRES_PORT:-5433} \
			$(VENV_PY) manage.py migrate --noinput; \
	else \
		echo "Start containers first (make start) or run make setup for a host migrate." >&2; \
		exit 1; \
	fi

import: env
	@mkdir -p "$(IMPORT_PENDING)" "$(ARCHIVE_OK)" "$(ARCHIVE_FAIL)"
	@echo "=== Import CSV into PostgreSQL ==="
	@echo "Pending folder: $(IMPORT_PENDING)"
	@pending=$$(find "$(IMPORT_PENDING)" -maxdepth 1 -name '*.csv' 2>/dev/null | wc -l); \
	if [[ "$$pending" -eq 0 ]]; then \
		echo ""; \
		echo "No CSV files found. Copy exports first, for example:"; \
		echo "  cp ../SensorDataCollector/exports/*.csv data/import_pending/"; \
		echo "Then run: make import"; \
		exit 1; \
	fi
	@echo "Files to import:"
	@find "$(IMPORT_PENDING)" -maxdepth 1 -name '*.csv' -printf '  %f\n' | sort
	@echo ""
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx django_web; then \
		$(DJANGO) import_pending_csv; \
	elif [[ -x $(VENV_PY) ]]; then \
		POSTGRES_HOST=$${POSTGRES_HOST:-localhost} POSTGRES_PORT=$${POSTGRES_PORT:-5433} \
			$(VENV_PY) manage.py import_pending_csv; \
	else \
		echo "Start containers first: make start" >&2; \
		exit 1; \
	fi
	@echo ""
	@echo "Done. Successful imports archived under: data/archive/db_migrated/"
	@echo "Failed imports (if any) under:          data/archive/import_failed/"
	@echo "View runs: http://localhost:$${DJANGO_PUBLISH_PORT:-8000}/"

importcsv: import

logs:
	$(COMPOSE) logs -f django_web

status:
	@$(COMPOSE) ps

reset_admin: env
	@./scripts/reset_django_admin.sh

docker-build:
	@DOCKERHUB_USER=$${DOCKERHUB_USER:?Set DOCKERHUB_USER} ./scripts/docker-publish.sh

docker-push:
	@DOCKERHUB_USER=$${DOCKERHUB_USER:?Set DOCKERHUB_USER} PUSH=1 ./scripts/docker-publish.sh --push

docker-publish: docker-push

urls:
	@port=$${DJANGO_PUBLISH_PORT:-8000}; \
	lan_ip=$$(hostname -I 2>/dev/null | awk '{print $$1}'); \
	echo "Django app URLs (port $$port):"; \
	echo "  Browser ON the Pi:     http://localhost:$$port/"; \
	if [[ -n "$$lan_ip" ]]; then \
	  echo "  Browser on another PC: http://$$lan_ip:$$port/"; \
	  echo "  (localhost on your PC does NOT reach the Pi)"; \
	else \
	  echo "  Browser on another PC: http://<pi-ip>:$$port/"; \
	fi; \
	echo ""; \
	if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx django_web; then \
	  echo "django_web: running"; \
	else \
	  echo "django_web: NOT running — run: make start"; \
	fi
