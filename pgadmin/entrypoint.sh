#!/bin/sh
# Prepare pgpass + servers.json, register Postgres server, then start pgAdmin.
set -e

PGADMIN_DATA=/var/lib/pgadmin
PGPASS="${PGADMIN_DATA}/.pgpass"
SERVERS_JSON=/pgadmin4/servers.json
DB="${POSTGRES_DB:-sauna_tests}"
USER="${POSTGRES_USER:-sauna_user}"
PASS="${POSTGRES_PASSWORD:-}"
HOST="${PGADMIN_POSTGRES_HOST:-host.docker.internal}"
PORT="${PGADMIN_POSTGRES_PORT:-${POSTGRES_PUBLISH_PORT:-5433}}"

mkdir -p "${PGADMIN_DATA}"

if [ -n "${PASS}" ]; then
  printf '%s:%s:*:%s:%s\n' "${HOST}" "${PORT}" "${USER}" "${PASS}" > "${PGPASS}"
  chmod 600 "${PGPASS}"
  chown 5050:5050 "${PGPASS}" 2>/dev/null || chown pgadmin:pgadmin "${PGPASS}" 2>/dev/null || true
fi

cat > "${SERVERS_JSON}" <<EOF
{
  "Servers": {
    "1": {
      "Name": "Product Test DB",
      "Group": "Servers",
      "Host": "${HOST}",
      "Port": ${PORT},
      "MaintenanceDB": "${DB}",
      "Username": "${USER}",
      "SSLMode": "prefer",
      "PassFile": "/var/lib/pgadmin/.pgpass"
    }
  }
}
EOF

export PGADMIN_SERVER_JSON_FILE="${SERVERS_JSON}"

if [ -f "${PGADMIN_DATA}/pgadmin4.db" ] && [ -f "${SERVERS_JSON}" ]; then
  /venv/bin/python3 /pgadmin4/setup.py load-servers "${SERVERS_JSON}" --replace 2>/dev/null || true
fi

exec /entrypoint.sh
