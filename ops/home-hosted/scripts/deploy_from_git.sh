#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

cd "$REPO_DIR"

if ! git diff --quiet --ignore-submodules HEAD --; then
  echo "Working tree is dirty; commit or stash changes before pulling." >&2
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"

git fetch --all --prune
git pull --ff-only origin "$BRANCH"

if [ -f "$REPO_DIR/.gitmodules" ]; then
  git submodule sync -- BidMonitor-AI
  git submodule update --init --recursive BidMonitor-AI
fi

/bin/zsh "$REPO_DIR/ops/home-hosted/scripts/apply_bidmonitor_patch.sh"

launchctl kickstart -k "gui/$(id -u)/com.codex.bidmonitor"
launchctl kickstart -k "gui/$(id -u)/com.codex.folo-bridge"
launchctl kickstart -k "gui/$(id -u)/com.codex.backend"
launchctl kickstart -k "gui/$(id -u)/com.codex.cloudflared"

# Run one sync immediately after the deploy to warm the latest data path.
launchctl kickstart -k "gui/$(id -u)/com.codex.intel-sync"
