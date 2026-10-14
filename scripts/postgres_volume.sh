#!/usr/bin/env bash
# Copy the Postgres Docker volume to a tar archive, or replace the volume from one.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

COMPOSE=(docker compose)
BACKUP_DIR="${ROOT}/data/backups"
IMAGE="postgres:16-alpine"

volume_name() {
  "${COMPOSE[@]}" config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["volumes"]["postgres_data"]["name"])'
}

postgres_running() {
  "${COMPOSE[@]}" ps --status running --services 2>/dev/null | grep -qx postgres
}

stop_db() {
  "${COMPOSE[@]}" stop django_web postgres
}

start_db() {
  "${COMPOSE[@]}" up -d postgres django_web
}

backup() {
  mkdir -p "${BACKUP_DIR}"
  local vol
  vol="$(volume_name)"
  if ! docker volume inspect "${vol}" >/dev/null 2>&1; then
    echo "Postgres volume ${vol} does not exist. Start once: make start" >&2
    exit 1
  fi
  local stamp name restart=0 status=0
  stamp="$(date +%Y-%m-%d_%H-%M-%S)"
  name="postgres_data_${stamp}.tar.gz"
  if postgres_running; then
    restart=1
    echo "Stopping Postgres so the volume copy is consistent..."
    stop_db
  fi
  docker run --rm --entrypoint tar \
    -v "${vol}:/volume:ro" \
    -v "${BACKUP_DIR}:/backup" \
    "${IMAGE}" \
    czf "/backup/${name}" -C /volume . || status=$?
  if [[ "${restart}" -eq 1 ]]; then
    echo "Starting Postgres and Django..."
    start_db
  fi
  if [[ "${status}" -ne 0 ]]; then
    exit "${status}"
  fi
  local bytes
  bytes="$(wc -c < "${BACKUP_DIR}/${name}" | tr -d ' ')"
  echo "Volume backup written: data/backups/${name} (${bytes} bytes)"
  echo "This file is not in git. Copy data/backups/${name} and .env onto the other machine, then run:"
  echo "  make db-restore FILE=data/backups/${name}"
}

restore() {
  local file="${1:-}"
  if [[ -z "${file}" ]]; then
    echo "Usage: make db-restore FILE=data/backups/postgres_data_YYYY-MM-DD_HH-MM-SS.tar.gz" >&2
    exit 1
  fi
  if [[ ! -f "${file}" ]]; then
    echo "File not found: ${file}" >&2
    exit 1
  fi
  if [[ "${file}" != *.tar.gz ]]; then
    echo "Expected a volume archive ending in .tar.gz." >&2
    exit 1
  fi
  local listing
  listing="$(tar tzf "${file}" 2>/dev/null || true)"
  if [[ -z "${listing}" ]]; then
    echo "Could not read archive: ${file}" >&2
    exit 1
  fi
  if ! grep -q 'PG_VERSION' <<< "${listing}"; then
    echo "Archive is not a Postgres data directory (missing PG_VERSION)." >&2
    exit 1
  fi
  local vol
  vol="$(volume_name)"
  if postgres_running; then
    echo "Stopping Postgres..."
    stop_db
  fi
  docker volume create "${vol}" >/dev/null
  echo "Replacing volume ${vol} from ${file} ..."
  docker run --rm --entrypoint find \
    -v "${vol}:/volume" \
    "${IMAGE}" \
    /volume -mindepth 1 -delete
  local abs_dir base
  abs_dir="$(cd "$(dirname "${file}")" && pwd)"
  base="$(basename "${file}")"
  docker run --rm --entrypoint tar \
    -v "${vol}:/volume" \
    -v "${abs_dir}:/backup:ro" \
    "${IMAGE}" \
    xzf "/backup/${base}" -C /volume
  echo "Starting Postgres and Django..."
  start_db
  echo "Volume restored from ${file}"
}

case "${1:-}" in
  backup) backup ;;
  restore) restore "${2:-}" ;;
  *)
    echo "Usage: $0 backup|restore [file]" >&2
    exit 1
    ;;
esac
