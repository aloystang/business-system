#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
BIDMONITOR_DIR="$REPO_DIR/BidMonitor-AI"
SERVER_DIR="$BIDMONITOR_DIR/server"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

if [ ! -x "$BIDMONITOR_DIR/.venv/bin/python" ]; then
  echo "Missing BidMonitor virtualenv: $BIDMONITOR_DIR/.venv/bin/python" >&2
  exit 1
fi

mkdir -p "$SERVER_DIR/logs" "$SERVER_DIR/data"
cd "$SERVER_DIR"

set -a
[ -f "$BACKEND_DIR/.env" ] && . "$BACKEND_DIR/.env"
set +a

export PYTHONUNBUFFERED=1
export BIDMONITOR_USERNAME="${BIDMONITOR_USERNAME:-CDKJ}"
export BIDMONITOR_PASSWORD="${BIDMONITOR_PASSWORD:-cdkj}"

exec "$BIDMONITOR_DIR/.venv/bin/python" -m uvicorn app:app --host 127.0.0.1 --port 8080
