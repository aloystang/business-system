"""经营台账聚合路由：单项目经营 + 首页多项目经营总览（财务/领导视角）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Project
from ..services import operations as ops

router = APIRouter(prefix="/api/v1", tags=["经营台账"])


@router.get("/projects/{project_id}/operations")
def project_operations(project_id: int, period: str | None = None,
                       db: Session = Depends(get_db), _=Depends(get_current_user)):
    """点开项目看经营台账：出租率/收入/成本/NOI/收缴/欠租/坪效/到期。period=YYYY-MM 可选。"""
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    return ops.project_operations(db, project_id, period)


@router.get("/dashboard/operations")
def portfolio_operations(period: str | None = None, db: Session = Depends(get_db),
                         _=Depends(get_current_user)):
    """首页 · 多项目经营总览：组合 KPI、项目对比榜、收入/成本结构、欠租 Top。"""
    return ops.portfolio_operations(db, period)


@router.get("/dashboard/risk-alerts")
def portfolio_risk_alerts(expiring_days: int = 90, top_n: int = 8,
                          db: Session = Depends(get_db), _=Depends(get_current_user)):
    """首页/管理中心 · 跨项目运营风险：欠租 Top、近期到期租约、空置 Top。"""
    return ops.portfolio_risk_alerts(db, expiring_days, top_n)
