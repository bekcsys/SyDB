#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo ""
echo "WebApp venv ready at ${ROOT}/.venv"
echo "Activate (does not use repo-root venv/):"
echo "  source ${ROOT}/scripts/activate_venv.sh"
