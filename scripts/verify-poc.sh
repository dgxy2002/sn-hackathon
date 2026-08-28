#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x backend/.venv/bin/python ]]; then
  echo "backend/.venv is missing. Follow the backend setup in README.md." >&2
  exit 1
fi

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=backend \
  backend/.venv/bin/python -m pytest backend/tests -q
VITE_API_URL="${VITE_API_URL:-http://localhost:8000}" \
  npm --prefix frontend run build

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose config --quiet
fi