# pgAdmin — run from this directory: cd WebApp/pgadmin && make <target>
SHELL := /bin/bash
COMPOSE := docker compose --env-file ../.env
WEBAPP_COMPOSE := docker compose -f ../docker-compose.yml --env-file ../.env

.PHONY: help start stop restart logs status reset urls

help:
	@echo "pgAdmin targets (optional DB browser — separate from WebApp):"
	@echo "  make start     Start pgAdmin only"
	@echo "  make stop      Stop pgAdmin"
	@echo "  make restart   Stop and start pgAdmin"
	@echo "  make logs      Follow pgAdmin logs"
	@echo "  make status    Show pgAdmin container status"
	@echo "  make reset     Remove pgAdmin container + data volume (fresh login)"
	@echo "  make urls      Show pgAdmin URL"
	@echo ""
	@echo "Requires PostgreSQL from the main WebApp stack:"
	@echo "  cd .. && make start"
	@echo ""
	@echo "Full guide: pgadmin/README.md"

start:
	@if ! $(WEBAPP_COMPOSE) ps --status running --services 2>/dev/null | grep -qx postgres; then \
		echo "PostgreSQL is not running. Start the WebApp first:" >&2; \
		echo "  cd .. && make start" >&2; \
		exit 1; \
	fi
	$(COMPOSE) up -d
	@echo ""
	@echo "Waiting for pgAdmin (first start can take 30-90 seconds)..."
	@for i in $$(seq 1 36); do \
		if $(COMPOSE) ps pgadmin 2>/dev/null | grep -q '(healthy)'; then \
			echo "pgAdmin is ready."; \
			break; \
		fi; \
		if [[ $$i -eq 36 ]]; then \
			echo "WARNING: pgAdmin not healthy yet. Check: make logs"; \
		fi; \
		sleep 5; \
	done
	@$(MAKE) urls

stop:
	$(COMPOSE) down

restart: stop start

logs:
	$(COMPOSE) logs -f pgadmin

status:
	@$(COMPOSE) ps

reset:
	$(COMPOSE) down -v
	@echo "pgAdmin data removed. Run 'make start' for a fresh setup."

urls:
	@port=$${PGADMIN_PUBLISH_PORT:-5050}; \
	lan_ip=$$(hostname -I 2>/dev/null | awk '{print $$1}'); \
	echo "pgAdmin URLs (port $$port):"; \
	echo "  On this Pi:    http://localhost:$$port/"; \
	if [[ -n "$$lan_ip" ]]; then \
	  echo "  From LAN/PC:   http://$$lan_ip:$$port/"; \
	fi; \
	echo "  Login: PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD in ../.env"
