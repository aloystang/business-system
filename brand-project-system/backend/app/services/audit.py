"""审计写入助手。不自行 commit，交调用方事务统一提交。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AuditLog, User


def record(db: Session, actor: User | None, action: str, entity_type: str,
           entity_id: str | int | None = None, detail: dict | None = None) -> None:
    db.add(AuditLog(
        actor_id=actor.id if actor else None,
        actor_name=actor.username if actor else None,
        action=action, entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        detail=detail,
    ))
