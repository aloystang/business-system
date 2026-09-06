"""出租经营台账路由（模板 08/09/10 + 项目成本）：商户 / 租约 / 收费 / 成本。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Lease, Merchant, Project, ProjectCost, Receivable, Unit
from ..schemas_leasing import (
    LeaseIn, LeaseOut, MerchantIn, MerchantOut, ProjectCostIn, ProjectCostOut,
    ReceivableIn, ReceivableOut,
)

router = APIRouter(prefix="/api/v1", tags=["出租经营台账"])


# ---------- 商户 ----------
@router.get("/merchants", response_model=list[MerchantOut])
def list_merchants(project_id: int | None = None, db: Session = Depends(get_db),
                   _=Depends(get_current_user)):
    q = db.query(Merchant)
    if project_id is not None:
        q = q.filter(Merchant.project_id == project_id)
    return q.order_by(Merchant.merchant_code).all()


@router.post("/merchants", response_model=MerchantOut, status_code=201)
def create_merchant(body: MerchantIn, db: Session = Depends(get_db),
                    _=Depends(require_perm("project:write"))):
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "所属项目不存在")
    if db.query(Merchant).filter(Merchant.merchant_code == body.merchant_code).first():
        raise HTTPException(409, f"商户编码已存在：{body.merchant_code}")
    m = Merchant(**body.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/merchants/{merchant_id}", response_model=MerchantOut)
def get_merchant(merchant_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.get(Merchant, merchant_id)
    if not m:
        raise HTTPException(404, "商户不存在")
    return m


# ---------- 租约 ----------
@router.get("/leases", response_model=list[LeaseOut])
def list_leases(project_id: int | None = None, merchant_id: int | None = None,
                db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Lease)
    if project_id is not None:
        q = q.filter(Lease.project_id == project_id)
    if merchant_id is not None:
        q = q.filter(Lease.merchant_id == merchant_id)
    return q.order_by(Lease.lease_code).all()


@router.post("/leases", response_model=LeaseOut, status_code=201)
def create_lease(body: LeaseIn, db: Session = Depends(get_db),
                 _=Depends(require_perm("project:write"))):
    if not db.get(Merchant, body.merchant_id):
        raise HTTPException(404, "所属商户不存在")
    if db.query(Lease).filter(Lease.lease_code == body.lease_code).first():
        raise HTTPException(409, f"租约编码已存在：{body.lease_code}")
    lease = Lease(**body.model_dump())
    db.add(lease)
    # 关联铺位置为"在租"
    if body.unit_id:
        u = db.get(Unit, body.unit_id)
        if u and u.status == "空置":
            u.status = "在租"
    db.commit()
    db.refresh(lease)
    return lease


# ---------- 收费欠租 ----------
def _aging_bucket(overdue_days: int) -> str:
    if overdue_days <= 0:
        return "未逾期"
    if overdue_days <= 30:
        return "0-30"
    if overdue_days <= 60:
        return "30-60"
    if overdue_days <= 90:
        return "60-90"
    return "90+"


@router.get("/receivables", response_model=list[ReceivableOut])
def list_receivables(project_id: int | None = None, lease_id: int | None = None,
                     period: str | None = None, only_arrears: bool = False,
                     db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Receivable)
    if project_id is not None:
        q = q.filter(Receivable.project_id == project_id)
    if lease_id is not None:
        q = q.filter(Receivable.lease_id == lease_id)
    if period:
        q = q.filter(Receivable.period == period)
    if only_arrears:
        q = q.filter(Receivable.arrears > 0)
    return q.order_by(Receivable.period.desc(), Receivable.receivable_code).all()


@router.post("/receivables", response_model=ReceivableOut, status_code=201)
def create_receivable(body: ReceivableIn, db: Session = Depends(get_db),
                      _=Depends(require_perm("project:write"))):
    lease = db.get(Lease, body.lease_id)
    if not lease:
        raise HTTPException(404, "所属租约不存在")
    if db.query(Receivable).filter(Receivable.receivable_code == body.receivable_code).first():
        raise HTTPException(409, f"应收记录编码已存在：{body.receivable_code}")
    arrears = round(max(body.amount_due - body.amount_received - body.prepay_offset, 0.0), 2)
    overdue = body.overdue_days
    if overdue is None:
        overdue = (date.today() - body.due_date).days if (arrears > 0 and body.due_date) else 0
        overdue = max(overdue, 0)
    status = body.collect_status or ("已结清" if arrears <= 0 else "催收中")
    r = Receivable(
        **body.model_dump(exclude={"overdue_days", "collect_status"}),
        arrears=arrears, overdue_days=overdue,
        aging=_aging_bucket(overdue) if arrears > 0 else "未逾期",
        collect_status=status,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


# ---------- 项目成本 ----------
@router.get("/project-costs", response_model=list[ProjectCostOut])
def list_costs(project_id: int | None = None, period: str | None = None,
               db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(ProjectCost)
    if project_id is not None:
        q = q.filter(ProjectCost.project_id == project_id)
    if period:
        q = q.filter(ProjectCost.period == period)
    return q.order_by(ProjectCost.period.desc(), ProjectCost.cost_type).all()


@router.post("/project-costs", response_model=ProjectCostOut, status_code=201)
def create_cost(body: ProjectCostIn, db: Session = Depends(get_db),
                _=Depends(require_perm("project:write"))):
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "所属项目不存在")
    existing = db.query(ProjectCost).filter(
        ProjectCost.project_id == body.project_id, ProjectCost.period == body.period,
        ProjectCost.cost_type == body.cost_type).first()
    if existing:                       # 同项目+账期+成本类型 → 覆盖金额（幂等）
        existing.amount = body.amount
        existing.remark = body.remark
        db.commit()
        db.refresh(existing)
        return existing
    c = ProjectCost(**body.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
