#!/bin/zsh

set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

UID_VALUE="$(id -u)"
AGENTS=(
  "com.codex.backend"
  "com.codex.folo-bridge"
  "com.codex.cloudflared"
  "com.codex.intel-sync"
  "com.codex.backup"
)

echo "LaunchAgents"
for agent in "${AGENTS[@]}"; do
  if launchctl print "gui/$UID_VALUE/$agent" >/dev/null 2>&1; then
    echo "  OK   $agent"
  else
    echo "  MISS $agent"
  fi
done

echo
echo "Local health"
if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "  OK   backend http://127.0.0.1:8000/health"
else
  echo "  FAIL backend http://127.0.0.1:8000/health"
fi

if curl -fsS http://127.0.0.1:9090/health >/dev/null 2>&1; then
  echo "  OK   folo-bridge http://127.0.0.1:9090/health"
else
  echo "  FAIL folo-bridge http://127.0.0.1:9090/health"
fi

if [ -n "${API_PUBLIC_BASE:-}" ]; then
  echo
  echo "Public health"
  if curl -fsS "$API_PUBLIC_BASE/health" >/dev/null 2>&1; then
    echo "  OK   $API_PUBLIC_BASE/health"
  else
    echo "  FAIL $API_PUBLIC_BASE/health"
  fi
fi

if [ -d "$HOME/Library/Logs/codex-home-hosted" ]; then
  echo
  echo "Recent logs"
  ls -lt "$HOME/Library/Logs/codex-home-hosted" | head -n 8
fi
