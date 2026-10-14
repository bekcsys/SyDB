#!/usr/bin/env bash
# Local Django dev server using WebApp/.venv only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ ! -f .venv/bin/activate ]]; then
  echo "Creating WebApp venv..." >&2
  "${ROOT}/scripts/setup_venv.sh"
fi

# shellcheck source=/dev/null
source .venv/bin/activate

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — set POSTGRES_HOST=localhost if Postgres runs in Docker." >&2
fi

# Local dev: Postgres is usually published on 5433 from docker-compose.
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5433}"

python manage.py migrate
echo "Starting Django at http://127.0.0.1:8000/ (POSTGRES_HOST=${POSTGRES_HOST} POSTGRES_PORT=${POSTGRES_PORT})"
exec python manage.py runserver 0.0.0.0:8000
