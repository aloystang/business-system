#!/bin/zsh

set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
export REPO_DIR BACKEND_DIR

set -a
[ -f "$BACKEND_DIR/.env" ] && . "$BACKEND_DIR/.env"
set +a

UID_VALUE="$(id -u)"
AGENTS=(
  "com.codex.bidmonitor"
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
bidmonitor_auth_header=""
if [ -n "${BIDMONITOR_USERNAME:-}" ] && [ -n "${BIDMONITOR_PASSWORD:-}" ]; then
  bidmonitor_auth_header="$(printf '%s' "${BIDMONITOR_USERNAME}:${BIDMONITOR_PASSWORD}" | /usr/bin/base64)"
elif [ -n "${BIDMONITOR_API_TOKEN:-}" ] && [[ "$BIDMONITOR_API_TOKEN" == *:* ]]; then
  bidmonitor_auth_header="$(printf '%s' "$BIDMONITOR_API_TOKEN" | /usr/bin/base64)"
fi

if [ -n "$bidmonitor_auth_header" ] && curl -fsS -H "Authorization: Basic $bidmonitor_auth_header" http://127.0.0.1:8080/api/status >/dev/null 2>&1; then
  echo "  OK   bidmonitor http://127.0.0.1:8080/api/status"
elif [ -z "$bidmonitor_auth_header" ]; then
  echo "  MISS bidmonitor credentials for http://127.0.0.1:8080/api/status"
else
  echo "  FAIL bidmonitor http://127.0.0.1:8080/api/status"
fi

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

echo
echo "Recent sync jobs"
python3 <<'PY'
import os
import sqlite3
import sys

db_url = os.getenv("DATABASE_URL", "")
repo_dir = os.getenv("REPO_DIR", "")
backend_dir = os.path.join(repo_dir, "backend") if repo_dir else ""

if db_url.startswith("sqlite:///"):
    db_path = db_url[len("sqlite:///"):]
else:
    db_path = os.path.join(backend_dir, "data", "app.db")

if not os.path.exists(db_path):
    print(f"  MISS sync database {db_path}")
    raise SystemExit(0)

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_system, status, pulled_count, upserted_count, started_at
        FROM intel_sync_job
        ORDER BY started_at DESC
        LIMIT 4
        """
    )
    rows = cur.fetchall()
except sqlite3.Error as exc:
    print(f"  FAIL intel_sync_job query failed: {exc}")
    raise SystemExit(0)
finally:
    try:
        conn.close()
    except Exception:
        pass

if not rows:
    print("  MISS no intel_sync_job rows")
    raise SystemExit(0)

for source_system, status, pulled_count, upserted_count, started_at in rows:
    print(
        f"  {source_system:<10} {status:<7} pulled={pulled_count:<4} "
        f"upserted={upserted_count:<4} started_at={started_at}"
    )
PY

if [ -d "$HOME/Library/Logs/codex-home-hosted" ]; then
  echo
  echo "Recent logs"
  ls -lt "$HOME/Library/Logs/codex-home-hosted" | head -n 8
fi
