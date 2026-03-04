from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..models import AuditLog


def log_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    record = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        ip=ip,
    )
    db.add(record)
    db.commit()
