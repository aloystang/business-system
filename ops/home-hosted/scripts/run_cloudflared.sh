#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "Missing cloudflared in PATH" >&2
  exit 1
fi

cd "$BACKEND_DIR"

set -a
[ -f "$BACKEND_DIR/.env" ] && . "$BACKEND_DIR/.env"
set +a

if [ -z "${CLOUDFLARED_TUNNEL_TOKEN:-}" ]; then
  echo "Missing CLOUDFLARED_TUNNEL_TOKEN in $BACKEND_DIR/.env" >&2
  exit 1
fi

exec cloudflared tunnel run --token "$CLOUDFLARED_TUNNEL_TOKEN"
