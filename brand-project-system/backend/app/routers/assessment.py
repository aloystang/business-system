"""铺位匹配（模板 12）与商户盘点评估（模板 13）路由。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Brand, Merchant, MerchantAssessment, Unit, UnitBrandMatch
from ..schemas_leasing import (
    MerchantAssessIn, MerchantAssessOut, UnitMatchIn, UnitMatchOut,
)

router = APIRouter(prefix="/api/v1", tags=["匹配与评估"])

_MATCH_DIMS = ["dim_format", "dim_property", "dim_project", "dim_business", "dim_will"]


def _match_grade(total: int) -> str:
    if total >= 85:
        return "优先推进"
    if total >= 70:
        return "重点储备"
    if total >= 55:
        return "持续观察"
    return "暂不匹配"


# ---------- 品牌×铺位匹配 ----------
@router.get("/unit-matches", response_model=list[UnitMatchOut])
def list_unit_matches(unit_id: int | None = None, brand_id: int | None = None,
                      db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(UnitBrandMatch)
    if unit_id is not None:
        q = q.filter(UnitBrandMatch.unit_id == unit_id)
    if brand_id is not None:
        q = q.filter(UnitBrandMatch.brand_id == brand_id)
    return q.order_by(UnitBrandMatch.total.desc()).all()


@router.post("/unit-matches", response_model=UnitMatchOut, status_code=201)
def create_unit_match(body: UnitMatchIn, db: Session = Depends(get_db),
                      _=Depends(require_perm("project:write"))):
    unit = db.get(Unit, body.unit_id)
    brand = db.get(Brand, body.brand_id)
    if not unit or not brand:
        raise HTTPException(404, "铺位或品牌不存在")
    if len(body.dims) != 5 or any(not (0 <= d <= 20) for d in body.dims):
        raise HTTPException(400, "须提交 5 个维度，各 0-20 分")
    total = sum(body.dims)
    m = db.query(UnitBrandMatch).filter(UnitBrandMatch.unit_id == body.unit_id,
                                        UnitBrandMatch.brand_id == body.brand_id).first()
    if not m:
        m = UnitBrandMatch(unit_id=body.unit_id, brand_id=body.brand_id,
                           project_id=unit.project_id,
                           match_code=f"UM-{body.unit_id}-{body.brand_id}")
        db.add(m)
    for k, v in zip(_MATCH_DIMS, body.dims):
        setattr(m, k, v)
    m.total = total
    m.grade = _match_grade(total)
    m.condition_gap = body.condition_gap
    m.reno_suggestion = body.reno_suggestion
    m.leasing_suggestion = body.leasing_suggestion
    m.match_status = "待确认"
    db.commit()
    db.refresh(m)
    return m


# ---------- 商户盘点评估 ----------
@router.get("/merchant-assessments", response_model=list[MerchantAssessOut])
def list_assessments(merchant_id: int | None = None, db: Session = Depends(get_db),
                     _=Depends(get_current_user)):
    q = db.query(MerchantAssessment)
    if merchant_id is not None:
        q = q.filter(MerchantAssessment.merchant_id == merchant_id)
    return q.order_by(MerchantAssessment.id.desc()).all()


@router.post("/merchant-assessments", response_model=MerchantAssessOut, status_code=201)
def create_assessment(body: MerchantAssessIn, db: Session = Depends(get_db),
                      _=Depends(require_perm("project:write"))):
    merchant = db.get(Merchant, body.merchant_id)
    if not merchant:
        raise HTTPException(404, "商户不存在")
    if len(body.dims) != 4 or any(not (0 <= d <= 25) for d in body.dims):
        raise HTTPException(400, "须提交 4 个维度，各 0-25 分")
    total = sum(body.dims)
    action = "升级" if total >= 80 else ("维持" if total >= 60 else "置换")
    conclusion = {"升级": "优质商户，建议升级/扩位", "维持": "达标商户，建议维持",
                  "置换": "低效商户，建议置换"}[action]
    fmt, rent, oper, grade = body.dims
    a = MerchantAssessment(
        assess_code=f"MA-{body.merchant_id}-{date.today().isoformat()}",
        merchant_id=body.merchant_id, project_id=merchant.project_id,
        dim_format_contribution=fmt, dim_rent_level=rent, dim_operation_quality=oper,
        dim_brand_grade=grade, total=total, conclusion=conclusion, action=action,
        candidate_brand_id=body.candidate_brand_id, assess_date=date.today(),
        assessor=body.assessor, note=body.note,
    )
    merchant.latest_assessment = f"{action}·{total}"
    db.add(a)
    db.commit()
    db.refresh(a)
    return a
