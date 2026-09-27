"""业态与调改：现有业态构成 + 逐铺位调改计划（单一现行计划）+ 调改后测算。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Project, Unit, UnitAdjustmentPlan, User
from ..models.adjustment import ADJUST_ACTIONS, PLAN_STATUSES
from ..schemas import AdjustmentPlanIn
from ..services import tenant_mix
from ..services.audit import record

router = APIRouter(prefix="/api/v1/projects", tags=["业态与调改"])


def _project_or_404(db: Session, project_id: int) -> Project:
    p = db.get(Project, project_id)
    if not p or p.is_deleted:
        raise HTTPException(404, "项目不存在")
    return p


@router.get("/{project_id}/tenant-mix")
def get_tenant_mix(project_id: int, db: Session = Depends(get_db),
                   _=Depends(get_current_user)):
    """现有业态构成（按业态/一级业态汇总铺位数·面积·租金·占比，空置单列）。"""
    _project_or_404(db, project_id)
    return tenant_mix.current_mix(db, project_id)


@router.get("/{project_id}/unit-layout")
def get_unit_layout(project_id: int, db: Session = Depends(get_db),
                    _=Depends(get_current_user)):
    """2.5D 铺位沙盘数据源：逐铺位(楼层/面积/状态/租户/业态/租金/调改计划)，已按楼层排序。"""
    _project_or_404(db, project_id)
    return tenant_mix.unit_layout(db, project_id)


@router.get("/{project_id}/adjustment-plan")
def get_adjustment_plan(project_id: int, db: Session = Depends(get_db),
                        _=Depends(get_current_user)):
    """逐铺位调改计划 + 调改后预测（现状 vs 计划的租金/坪效/出租率/NOI）。"""
    _project_or_404(db, project_id)
    return tenant_mix.plan_summary(db, project_id)


@router.get("/{project_id}/adjustment-roadmap")
def get_adjustment_roadmap(project_id: int, db: Session = Depends(get_db),
                           _=Depends(get_current_user)):
    """分批调改路线图：按季度、跟随租约到期分批，含累积出租率/租金曲线与到期窗口。"""
    _project_or_404(db, project_id)
    return tenant_mix.adjustment_roadmap(db, project_id)


@router.get("/{project_id}/adjustment-plan/{unit_id}/early-swap-tradeoff")
def get_early_swap_tradeoff(
    project_id: int, unit_id: int,
    termination_months: float | None = None, free_rent_months: float | None = None,
    fitout_cost_psm: float | None = None, horizon_months: int | None = None,
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    """提前置换 vs 等到期 的成本收益对比（估算；可传参覆盖默认假设）。"""
    _project_or_404(db, project_id)
    try:
        return tenant_mix.early_swap_tradeoff(
            db, project_id, unit_id, termination_months, free_rent_months,
            fitout_cost_psm, horizon_months)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/{project_id}/adjustment-plan/{unit_id}")
def upsert_plan(project_id: int, unit_id: int, body: AdjustmentPlanIn,
                db: Session = Depends(get_db),
                user: User = Depends(require_perm("project:write"))):
    """新增/更新某铺位的调改计划（每铺位唯一现行计划）。"""
    _project_or_404(db, project_id)
    unit = db.get(Unit, unit_id)
    if not unit or unit.project_id != project_id:
        raise HTTPException(404, "铺位不存在或不属于该项目")
    if body.action not in ADJUST_ACTIONS:
        raise HTTPException(400, f"动作非法，须为：{'/'.join(ADJUST_ACTIONS)}")
    if body.plan_status not in PLAN_STATUSES:
        raise HTTPException(400, f"计划状态非法，须为：{'/'.join(PLAN_STATUSES)}")
    plan_date = None
    if body.plan_date:
        try:
            plan_date = date.fromisoformat(body.plan_date)
        except ValueError:
            raise HTTPException(400, "plan_date 格式应为 YYYY-MM-DD")

    plan = db.query(UnitAdjustmentPlan).filter(
        UnitAdjustmentPlan.unit_id == unit_id).first()
    if not plan:
        plan = UnitAdjustmentPlan(project_id=project_id, unit_id=unit_id, action=body.action)
        db.add(plan)
    plan.action = body.action
    plan.to_format = body.to_format
    plan.from_format = body.from_format
    plan.target_brand_id = body.target_brand_id
    plan.expected_rent = body.expected_rent
    plan.expected_rent_psm = body.expected_rent_psm
    plan.plan_status = body.plan_status
    plan.plan_date = plan_date
    plan.reason = body.reason
    plan.owner = body.owner
    record(db, user, "adjust_plan", "unit", unit_id, {"action": body.action})
    db.commit()
    return tenant_mix.plan_summary(db, project_id)


@router.delete("/{project_id}/adjustment-plan/{unit_id}")
def delete_plan(project_id: int, unit_id: int, db: Session = Depends(get_db),
                user: User = Depends(require_perm("project:write"))):
    plan = db.query(UnitAdjustmentPlan).filter(
        UnitAdjustmentPlan.unit_id == unit_id,
        UnitAdjustmentPlan.project_id == project_id).first()
    if not plan:
        raise HTTPException(404, "该铺位暂无调改计划")
    db.delete(plan)
    record(db, user, "adjust_plan_delete", "unit", unit_id)
    db.commit()
    return {"ok": True, "unit_id": unit_id}
