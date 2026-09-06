"""沟通记录路由。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import CommunicationRecord, User
from ..schemas import CommIn, CommOut

router = APIRouter(prefix="/api/v1/communications", tags=["沟通记录"])
_RELATED = {"brand", "project", "match"}


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(400, f"日期格式应为 YYYY-MM-DD：{s}")


@router.get("", response_model=list[CommOut])
def list_comms(brand_id: int | None = None, project_id: int | None = None,
               db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(CommunicationRecord)
    if brand_id is not None:
        q = q.filter(CommunicationRecord.brand_id == brand_id)
    if project_id is not None:
        q = q.filter(CommunicationRecord.project_id == project_id)
    return q.order_by(CommunicationRecord.comm_date.desc()).all()


@router.post("", response_model=CommOut, status_code=201)
def add_comm(body: CommIn, db: Session = Depends(get_db),
             user: User = Depends(require_perm("match:write"))):
    if body.related_type not in _RELATED:
        raise HTTPException(400, "related_type 须为 brand/project/match")
    data = body.model_dump()
    data["comm_date"] = _parse_date(body.comm_date)
    data["plan_date"] = _parse_date(body.plan_date)
    rec = CommunicationRecord(owner_id=user.id, **data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
