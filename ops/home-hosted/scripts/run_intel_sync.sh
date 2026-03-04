#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

if [ ! -x "$BACKEND_DIR/.venv/bin/python" ]; then
  echo "Missing backend virtualenv: $BACKEND_DIR/.venv/bin/python" >&2
  exit 1
fi

cd "$BACKEND_DIR"

set -a
[ -f "$BACKEND_DIR/.env" ] && . "$BACKEND_DIR/.env"
set +a

exec "$BACKEND_DIR/.venv/bin/python" -m app.intel_sync_worker
