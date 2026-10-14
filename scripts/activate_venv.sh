#!/usr/bin/env bash
# Activate WebApp-only venv (separate from repo-root venv used for MQTT/plotting).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/.venv"

if [[ ! -f "${VENV}/bin/activate" ]]; then
  echo "WebApp venv not found at ${VENV}" >&2
  echo "Create it with: ${ROOT}/scripts/setup_venv.sh" >&2
  return 1 2>/dev/null || exit 1
fi

# shellcheck source=/dev/null
source "${VENV}/bin/activate"
cd "${ROOT}"
