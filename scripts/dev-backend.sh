#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker compose up -d postgres
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://agent:agent@localhost:55432/agent_template}"
export READONLY_DATABASE_URL="${READONLY_DATABASE_URL:-postgresql+psycopg://agent:agent@localhost:55432/agent_template}"
export PYTHONPATH="$ROOT/backend"

exec "$ROOT/.venv/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port "${PORT:-8000}"
