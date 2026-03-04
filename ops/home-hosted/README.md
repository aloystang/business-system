# Home-Hosted Deployment

This setup separates the machines:

- your current computer is the development and release machine
- the spare Mac is the always-on runtime host
- Vercel only serves the frontend
- Cloudflare Tunnel exposes the backend over HTTPS

Use this folder when you want a zero-server deployment path without moving the backend to Vercel or to a paid VPS.

For a copy-paste deployment guide in Chinese, start with [STEP_BY_STEP.zh-CN.md](./STEP_BY_STEP.zh-CN.md).

## Final Topology

- Vercel hosts the static frontend from `frontend/`
- the spare Mac runs:
  - FastAPI backend on `127.0.0.1:8000`
  - `folo-bridge` on `127.0.0.1:9090`
  - `cloudflared` named tunnel
  - scheduled sync and backup jobs via `launchd`
- the current machine is used for:
  - code changes
  - Git pushes
  - Vercel deploys
  - spare Mac maintenance

## Source Of Truth

- production data lives only on the spare Mac
- `backend/data/app.db` on the spare Mac is the only online primary database
- the current development machine can have a local database, but it is not the online source of truth

Do not try to keep SQLite writable on both machines.

## Required Accounts And Services

- Git repository host such as GitHub
- Vercel Hobby account
- Cloudflare account
- a domain name delegated to Cloudflare DNS

## Deployment Flow

1. Develop on the current machine
2. Commit and push to the Git repository
3. Vercel rebuilds the frontend from `frontend/`
4. SSH into the spare Mac and run `ops/home-hosted/scripts/deploy_from_git.sh`
5. The spare Mac pulls the latest branch and restarts backend, bridge, tunnel, and one sync job

This keeps release and runtime responsibilities separate.

## Environment Files

Copy the templates first:

```bash
cp backend/.env.example backend/.env
cp folo-bridge/.env.example folo-bridge/.env
```

### `backend/.env`

At minimum, set these values on the spare Mac:

```dotenv
JWT_SECRET=replace-with-a-long-random-secret
CORS_ORIGINS=https://app.yourdomain.com,http://localhost:3000,http://127.0.0.1:3000
PUBLIC_SHARE_BASE=https://app.yourdomain.com
DATABASE_URL=sqlite:////ABSOLUTE/PATH/TO/codex/backend/data/app.db
UPLOAD_DIR=/ABSOLUTE/PATH/TO/codex/backend/data/uploads
EXPORT_DIR=/ABSOLUTE/PATH/TO/codex/backend/data/exports
FOLO_BASE_URL=http://127.0.0.1:9090
FOLO_API_TOKEN=replace-with-a-private-token
FOLO_SYNC_ENABLED=true
CLOUDFLARED_TUNNEL_TOKEN=replace-with-cloudflare-named-tunnel-token
BACKUP_DIR=/ABSOLUTE/PATH/TO/codex/backups/runtime
BACKUP_RETENTION_DAYS=14
```

### `folo-bridge/.env`

Use this file if you need bridge-specific overrides:

```dotenv
FOLO_BRIDGE_TOKEN=replace-with-a-private-token
FOLO_BRIDGE_DB=/ABSOLUTE/PATH/TO/codex/folo-bridge/data/folo_bridge.db
FOLO_BRIDGE_SUBSCRIPTIONS=/ABSOLUTE/PATH/TO/codex/folo-bridge/subscriptions.yaml
FOLO_BRIDGE_REFRESH_MINUTES=120
```

## Spare Mac Bootstrap

On the spare Mac:

1. clone the repo
2. create the backend virtualenv and install backend requirements
3. install Node only if you also want local frontend preview on the spare Mac
4. install `cloudflared`
5. copy the `.env` templates and fill in real values
6. make the scripts executable:

```bash
chmod +x /ABSOLUTE/PATH/TO/codex/ops/home-hosted/scripts/*.sh
```

## Cloudflare Named Tunnel

Create a named tunnel in Cloudflare and point `api.yourdomain.com` at the spare Mac tunnel. This repo expects the token-based runtime form:

```bash
cloudflared tunnel run --token "$CLOUDFLARED_TUNNEL_TOKEN"
```

The launchd job uses `ops/home-hosted/scripts/run_cloudflared.sh`, which reads the token from `backend/.env`.

## Vercel Frontend

1. import the repository into Vercel
2. set the project root directory to `frontend`
3. set build command to `npm run build`
4. set output directory to `dist`
5. set the environment variable:

```dotenv
VITE_API_BASE=https://api.yourdomain.com
```

6. bind `app.yourdomain.com` as the custom domain

`frontend/vercel.json` already contains SPA fallback rewrites.

## Available Runtime Scripts

- `run_backend.sh`
- `run_folo_bridge.sh`
- `run_intel_sync.sh`
- `run_cloudflared.sh`
- `backup_runtime_data.sh`
- `deploy_from_git.sh`
- `bootstrap_spare_mac.sh`
- `install_launch_agents.sh`
- `status_home_hosted.sh`
- `remote_deploy.sh`

## launchd Setup On The Spare Mac

1. make scripts executable:

```bash
chmod +x /ABSOLUTE/PATH/TO/codex/ops/home-hosted/scripts/*.sh
```

2. install and load all launch agents in one command:

```bash
/ABSOLUTE/PATH/TO/codex/ops/home-hosted/scripts/install_launch_agents.sh
```

This copies the example plists into `~/Library/LaunchAgents`, replaces the placeholders, and bootstraps all services.

3. if you prefer the manual path, create the log directory:

```bash
mkdir -p "$HOME/Library/Logs/codex-home-hosted"
```

4. copy the example plists:

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp /ABSOLUTE/PATH/TO/codex/ops/home-hosted/launchd/*.plist.example "$HOME/Library/LaunchAgents/"
```

5. in each copied plist, replace:

- `__REPO_DIR__` with the repository absolute path on the spare Mac
- `__HOME__` with the spare Mac home directory

6. rename the files to remove `.example`

7. load them:

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.codex.backend.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.codex.folo-bridge.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.codex.cloudflared.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.codex.intel-sync.plist"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.codex.backup.plist"
```

8. confirm status:

```bash
launchctl print "gui/$(id -u)/com.codex.backend"
launchctl print "gui/$(id -u)/com.codex.folo-bridge"
launchctl print "gui/$(id -u)/com.codex.cloudflared"
launchctl print "gui/$(id -u)/com.codex.intel-sync"
launchctl print "gui/$(id -u)/com.codex.backup"
```

Defaults:

- sync every 7200 seconds
- backup every day at 03:30

To get a quick summary later:

```bash
API_PUBLIC_BASE=https://api.yourdomain.com /ABSOLUTE/PATH/TO/codex/ops/home-hosted/scripts/status_home_hosted.sh
```

## Trigger A Deploy From The Current Machine

If the spare Mac is reachable over SSH, you can update it from the current machine:

```bash
/ABSOLUTE/PATH/TO/codex/ops/home-hosted/scripts/remote_deploy.sh user@spare-mac.local /ABSOLUTE/PATH/TO/codex
```

This runs `deploy_from_git.sh` remotely on the spare Mac.

## Health Checks

On the spare Mac:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:9090/health
```

Externally:

```bash
curl -s https://api.yourdomain.com/health
```

Then open `https://app.yourdomain.com` and verify login, overview, planning, and intel pages.

## Backup Layout

By default `backup_runtime_data.sh` writes timestamped snapshots under:

```text
$BACKUP_DIR/YYYYMMDD-HHMMSS/
```

Each snapshot contains:

- backend database
- uploads
- exports
- optional `folo_bridge.db`
- optional `subscriptions.yaml`

Old snapshots are pruned by `BACKUP_RETENTION_DAYS`.

## Suggested Linear Usage

See [LINEAR.md](./LINEAR.md) for a starter project layout and suggested issues.

## Important Caveats

- if the spare Mac sleeps, the site backend and sync jobs stop
- if the spare Mac loses network, Vercel still serves HTML but API requests fail
- this is a low-cost home-hosted setup, not a production-grade high-availability architecture
- rotate secrets before exposing the backend on a public domain
