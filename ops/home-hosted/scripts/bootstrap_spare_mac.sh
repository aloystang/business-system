#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
BRIDGE_DIR="$REPO_DIR/folo-bridge"
BIDMONITOR_DIR="$REPO_DIR/BidMonitor-AI"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

cd "$BACKEND_DIR"

if [ -f "$REPO_DIR/.gitmodules" ]; then
  git -C "$REPO_DIR" submodule sync -- BidMonitor-AI
  git -C "$REPO_DIR" submodule update --init --recursive BidMonitor-AI
fi

/bin/zsh "$REPO_DIR/ops/home-hosted/scripts/apply_bidmonitor_patch.sh"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi

if [ ! -d "$BIDMONITOR_DIR/.venv" ]; then
  python3 -m venv "$BIDMONITOR_DIR/.venv"
fi

"$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
"$BACKEND_DIR/.venv/bin/pip" install -r "$BRIDGE_DIR/requirements.txt"
"$BIDMONITOR_DIR/.venv/bin/pip" install -r "$BIDMONITOR_DIR/requirements.txt"
"$BIDMONITOR_DIR/.venv/bin/pip" install -r "$BIDMONITOR_DIR/server/requirements.txt"

if [ ! -f "$BACKEND_DIR/.env" ] && [ -f "$BACKEND_DIR/.env.example" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

if [ ! -f "$BRIDGE_DIR/.env" ] && [ -f "$BRIDGE_DIR/.env.example" ]; then
  cp "$BRIDGE_DIR/.env.example" "$BRIDGE_DIR/.env"
fi

if [ ! -f "$BRIDGE_DIR/subscriptions.yaml" ] && [ -f "$BRIDGE_DIR/subscriptions.example.yaml" ]; then
  cp "$BRIDGE_DIR/subscriptions.example.yaml" "$BRIDGE_DIR/subscriptions.yaml"
fi

mkdir -p "$HOME/Library/Logs/codex-home-hosted"
mkdir -p "$REPO_DIR/backups/runtime"
mkdir -p "$BIDMONITOR_DIR/server/logs"
mkdir -p "$BIDMONITOR_DIR/server/data"

chmod +x "$REPO_DIR"/ops/home-hosted/scripts/*.sh

set -a
[ -f "$BACKEND_DIR/.env" ] && . "$BACKEND_DIR/.env"
set +a

"$BACKEND_DIR/.venv/bin/python" -m app.init_db

cat <<EOF
Spare Mac bootstrap complete.

Next:
1. Edit $BACKEND_DIR/.env with real values.
2. Edit $BRIDGE_DIR/.env if you need bridge overrides.
3. Edit $BRIDGE_DIR/subscriptions.yaml with your feed sources.
4. Change BIDMONITOR_USERNAME / BIDMONITOR_PASSWORD away from defaults and keep BIDMONITOR_API_TOKEN in sync.
5. Install cloudflared: brew install cloudflared
6. Run ops/home-hosted/scripts/install_launch_agents.sh
7. Verify services with ops/home-hosted/scripts/status_home_hosted.sh
EOF
