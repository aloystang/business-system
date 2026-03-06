from __future__ import annotations

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def _load_env_file() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        clean = value.strip().strip('"').strip("'")
        os.environ[key] = clean


_load_env_file()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(DATA_DIR / "uploads")))
EXPORT_DIR = Path(os.getenv("EXPORT_DIR", str(DATA_DIR / "exports")))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'app.db'}")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
PUBLIC_SHARE_BASE = os.getenv("PUBLIC_SHARE_BASE", "http://localhost:3000")
AMAP_WEB_KEY = os.getenv("AMAP_WEB_KEY", "")
MAP_DEFAULT_CITY = os.getenv("MAP_DEFAULT_CITY", "")
BIDMONITOR_BASE_URL = os.getenv("BIDMONITOR_BASE_URL", "")
BIDMONITOR_API_TOKEN = os.getenv("BIDMONITOR_API_TOKEN", "")
BIDMONITOR_PULL_PATH = os.getenv("BIDMONITOR_PULL_PATH", "/api/results")
FOLO_BASE_URL = os.getenv("FOLO_BASE_URL", "")
FOLO_API_TOKEN = os.getenv("FOLO_API_TOKEN", "")
FOLO_PULL_PATH = os.getenv("FOLO_PULL_PATH", "/api/intel/items")
FOLO_SYNC_ENABLED = os.getenv("FOLO_SYNC_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
INTEL_DEFAULT_CITY = os.getenv("INTEL_DEFAULT_CITY", "重庆市")

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
