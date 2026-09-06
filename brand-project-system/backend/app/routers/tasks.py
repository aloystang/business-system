"""跟进任务路由。"""
from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import FollowupTask, User
from ..schemas import TaskIn, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/v1/tasks", tags=["跟进任务"])
_STATUSES = {"待办", "进行中", "已完成", "已取消"}


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(400, f"日期格式应为 YYYY-MM-DD：{s}")


@router.get("", response_model=list[TaskOut])
def list_tasks(owner_id: int | None = None, status: str | None = None,
               overdue: bool = False, db: Session = Depends(get_db),
               _=Depends(get_current_user)):
    q = db.query(FollowupTask)
    if owner_id is not None:
        q = q.filter(FollowupTask.owner_id == owner_id)
    if status:
        q = q.filter(FollowupTask.status == status)
    if overdue:
        q = q.filter(FollowupTask.plan_date < date.today(),
                     FollowupTask.status.in_(["待办", "进行中"]))
    return q.order_by(FollowupTask.plan_date.is_(None), FollowupTask.plan_date).all()


@router.get("/mine", response_model=list[TaskOut])
def my_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(FollowupTask).filter(
        FollowupTask.owner_id == user.id,
        FollowupTask.status.in_(["待办", "进行中"])).all()


@router.post("", response_model=TaskOut, status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db),
                user: User = Depends(require_perm("match:write"))):
    data = body.model_dump()
    data["plan_date"] = _parse_date(body.plan_date)
    t = FollowupTask(created_by=user.id, owner_id=body.owner_id or user.id,
                     **{k: v for k, v in data.items() if k != "owner_id"})
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db),
                _=Depends(require_perm("match:write"))):
    t = db.get(FollowupTask, task_id)
    if not t:
        raise HTTPException(404, "任务不存在")
    if body.status is not None:
        if body.status not in _STATUSES:
            raise HTTPException(400, f"非法状态：{body.status}")
        t.status = body.status
        if body.status == "已完成":
            t.done_at = datetime.now(timezone.utc)
    if body.priority is not None:
        t.priority = body.priority
    if body.plan_date is not None:
        t.plan_date = _parse_date(body.plan_date)
    if body.detail is not None:
        t.detail = body.detail
    db.commit()
    db.refresh(t)
    return t
