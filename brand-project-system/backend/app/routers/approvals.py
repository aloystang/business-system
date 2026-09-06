"""审核队列路由。"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import ApprovalRecord, User
from ..schemas import ApprovalDecideIn, ApprovalOut
from ..services.audit import record

router = APIRouter(prefix="/api/v1/approvals", tags=["审核"])
_TARGETS = {"brand", "project", "brand_score", "project_score", "import_batch"}


@router.get("", response_model=list[ApprovalOut])
def list_approvals(status: str | None = "待审核", db: Session = Depends(get_db),
                   _=Depends(get_current_user)):
    q = db.query(ApprovalRecord)
    if status:
        q = q.filter(ApprovalRecord.status == status)
    return q.order_by(ApprovalRecord.submitted_at.desc()).all()


@router.post("", response_model=ApprovalOut, status_code=201)
def submit(target_type: str, target_id: int, db: Session = Depends(get_db),
           user: User = Depends(require_perm("project:write"))):
    if target_type not in _TARGETS:
        raise HTTPException(400, f"非法审核对象类型：{target_type}")
    a = ApprovalRecord(target_type=target_type, target_id=target_id, action="submit",
                       status="待审核", submitter_id=user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.post("/{approval_id}/decide", response_model=ApprovalOut)
def decide(approval_id: int, body: ApprovalDecideIn, db: Session = Depends(get_db),
           user: User = Depends(require_perm("project:write"))):
    a = db.get(ApprovalRecord, approval_id)
    if not a:
        raise HTTPException(404, "审核记录不存在")
    if a.status != "待审核":
        raise HTTPException(409, "该记录已审结")
    if body.action not in {"approve", "reject"}:
        raise HTTPException(400, "action 须为 approve/reject")
    a.status = "通过" if body.action == "approve" else "驳回"
    a.approver_id = user.id
    a.comment = body.comment
    a.decided_at = datetime.now(timezone.utc)
    record(db, user, f"approval_{body.action}", a.target_type, a.target_id)
    db.commit()
    db.refresh(a)
    return a
