#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
BRIDGE_DIR="$REPO_DIR/folo-bridge"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

set -a
[ -f "$BACKEND_DIR/.env" ] && . "$BACKEND_DIR/.env"
[ -f "$BRIDGE_DIR/.env" ] && . "$BRIDGE_DIR/.env"
set +a

BACKUP_ROOT="${BACKUP_DIR:-$REPO_DIR/backups/runtime}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date '+%Y%m%d-%H%M%S')"
TARGET_DIR="$BACKUP_ROOT/$STAMP"

mkdir -p "$TARGET_DIR/backend" "$TARGET_DIR/folo-bridge"

if [ -f "$BACKEND_DIR/data/app.db" ]; then
  cp "$BACKEND_DIR/data/app.db" "$TARGET_DIR/backend/app.db"
fi

if [ -d "$BACKEND_DIR/data/uploads" ]; then
  rsync -a --delete "$BACKEND_DIR/data/uploads/" "$TARGET_DIR/backend/uploads/"
fi

if [ -d "$BACKEND_DIR/data/exports" ]; then
  rsync -a --delete "$BACKEND_DIR/data/exports/" "$TARGET_DIR/backend/exports/"
fi

if [ "${BACKUP_INCLUDE_BRIDGE_DB:-true}" = "true" ] && [ -f "${FOLO_BRIDGE_DB:-$BRIDGE_DIR/data/folo_bridge.db}" ]; then
  cp "${FOLO_BRIDGE_DB:-$BRIDGE_DIR/data/folo_bridge.db}" "$TARGET_DIR/folo-bridge/folo_bridge.db"
fi

if [ "${BACKUP_INCLUDE_BRIDGE_SUBSCRIPTIONS:-true}" = "true" ] && [ -f "${FOLO_BRIDGE_SUBSCRIPTIONS:-$BRIDGE_DIR/subscriptions.yaml}" ]; then
  cp "${FOLO_BRIDGE_SUBSCRIPTIONS:-$BRIDGE_DIR/subscriptions.yaml}" "$TARGET_DIR/folo-bridge/subscriptions.yaml"
fi

find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime "+$RETENTION_DAYS" -exec rm -rf {} +
