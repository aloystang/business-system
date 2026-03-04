#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LAUNCHD_DIR="$REPO_DIR/ops/home-hosted/launchd"
TARGET_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs/codex-home-hosted"
UID_VALUE="$(id -u)"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

mkdir -p "$TARGET_DIR" "$LOG_DIR"

for template in "$LAUNCHD_DIR"/*.plist.example; do
  base_name="$(basename "$template" .example)"
  target="$TARGET_DIR/$base_name"
  cp "$template" "$target"
  /usr/bin/sed -i '' "s#__REPO_DIR__#$REPO_DIR#g" "$target"
  /usr/bin/sed -i '' "s#__HOME__#$HOME#g" "$target"
  launchctl bootout "gui/$UID_VALUE" "$target" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$UID_VALUE" "$target"
done

echo "Installed launch agents into $TARGET_DIR"
echo "Logs directory: $LOG_DIR"
