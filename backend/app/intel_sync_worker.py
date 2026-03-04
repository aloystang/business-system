from __future__ import annotations

from app.config import FOLO_SYNC_ENABLED
from app.database import SessionLocal
from app.services.intel import run_sync


def main() -> None:
    db = SessionLocal()
    try:
        source_system = "all" if FOLO_SYNC_ENABLED else "bidmonitor"
        run_sync(db, created_by=None, trigger_type="scheduled", source_system=source_system)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
