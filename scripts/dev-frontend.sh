#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/frontend"

if [[ ! -x node_modules/.bin/next ]]; then
  npm ci
fi

export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-}"
exec npm run dev -- --hostname 0.0.0.0 --port "${PORT:-3001}"
