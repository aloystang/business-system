from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import ProjectSnapshot


def create_project_snapshot(
    db: Session,
    *,
    project_id: str,
    snapshot_type: str,
    payload: dict[str, Any],
    created_by: int,
) -> ProjectSnapshot:
    latest_version = (
        db.query(func.max(ProjectSnapshot.version))
        .filter(ProjectSnapshot.project_id == project_id, ProjectSnapshot.snapshot_type == snapshot_type)
        .scalar()
    )
    version = int(latest_version or 0) + 1
    now = datetime.utcnow().isoformat(timespec="seconds")
    snapshot = ProjectSnapshot(
        id=f"{project_id}-{snapshot_type}-v{version}",
        project_id=project_id,
        snapshot_type=snapshot_type,
        version=version,
        payload_json=json.dumps(payload, ensure_ascii=False),
        created_by=created_by,
        created_at=now,
    )
    db.add(snapshot)
    db.flush()
    return snapshot
