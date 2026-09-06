"""工作首页 / 看板汇总。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    ApprovalRecord, Brand, FollowupTask, Match, Project, ProjectLocation, User,
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["工作台"])


def _group_counts(rows) -> dict[str, int]:
    return {k: n for k, n in rows if k is not None}


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    projects_total = db.query(Project).filter(Project.is_deleted.is_(False)).count()
    brands_total = db.query(Brand).filter(Brand.is_deleted.is_(False)).count()

    by_status = _group_counts(
        db.query(Project.project_status, func.count()).filter(
            Project.is_deleted.is_(False)).group_by(Project.project_status).all())
    by_type = _group_counts(
        db.query(Project.project_type, func.count()).filter(
            Project.is_deleted.is_(False)).group_by(Project.project_type).all())
    match_grades = _group_counts(
        db.query(Match.match_grade, func.count()).group_by(Match.match_grade).all())

    geocode_failed = db.query(ProjectLocation).filter(
        ProjectLocation.geocoding_status.in_(["定位失败", "待定位"])).count()
    pending_approvals = db.query(ApprovalRecord).filter(
        ApprovalRecord.status == "待审核").count()

    open_tasks = db.query(FollowupTask).filter(
        FollowupTask.owner_id == user.id,
        FollowupTask.status.in_(["待办", "进行中"])).count()
    overdue_tasks = db.query(FollowupTask).filter(
        FollowupTask.owner_id == user.id,
        FollowupTask.status.in_(["待办", "进行中"]),
        FollowupTask.plan_date < date.today()).count()

    return {
        "kpi": {
            "projects_total": projects_total,
            "brands_total": brands_total,
            "geocode_failed": geocode_failed,
            "pending_approvals": pending_approvals,
        },
        "projects_by_status": by_status,
        "projects_by_type": by_type,
        "match_grade_distribution": match_grades,
        "my_tasks": {"open": open_tasks, "overdue": overdue_tasks},
    }
