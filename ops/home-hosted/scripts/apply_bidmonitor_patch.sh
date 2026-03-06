#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BIDMONITOR_DIR="$REPO_DIR/BidMonitor-AI"
PATCH_FILE="$REPO_DIR/ops/home-hosted/patches/bidmonitor-home-hosted.patch"

if [ ! -d "$BIDMONITOR_DIR/.git" ] && [ ! -f "$BIDMONITOR_DIR/.git" ]; then
  echo "BidMonitor-AI submodule is missing. Run: git submodule update --init BidMonitor-AI" >&2
  exit 1
fi

if [ ! -f "$PATCH_FILE" ]; then
  echo "Missing patch file: $PATCH_FILE" >&2
  exit 1
fi

if git -C "$BIDMONITOR_DIR" apply --check "$PATCH_FILE" >/dev/null 2>&1; then
  git -C "$BIDMONITOR_DIR" apply "$PATCH_FILE"
  echo "Applied BidMonitor home-hosted patch."
elif git -C "$BIDMONITOR_DIR" apply --reverse --check "$PATCH_FILE" >/dev/null 2>&1; then
  echo "BidMonitor home-hosted patch already applied."
else
  echo "BidMonitor home-hosted patch does not apply cleanly. Check submodule state." >&2
  exit 1
fi
