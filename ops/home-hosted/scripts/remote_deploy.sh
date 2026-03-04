#!/bin/zsh

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <spare-mac-host> [repo-dir-on-spare-mac]" >&2
  exit 1
fi

SPARE_MAC_HOST="$1"
REMOTE_REPO_DIR="${2:-\$HOME/codex}"

exec ssh "$SPARE_MAC_HOST" "cd $REMOTE_REPO_DIR && ./ops/home-hosted/scripts/deploy_from_git.sh"
