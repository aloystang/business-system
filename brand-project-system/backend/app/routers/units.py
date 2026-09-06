"""铺位路由（模板 05）：CRUD + 状态变更。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Project, Unit
from ..schemas_leasing import UnitIn, UnitOut, UnitStatusIn

router = APIRouter(prefix="/api/v1/units", tags=["铺位"])
_STATUSES = {"空置", "在租", "自营", "装修"}


@router.get("", response_model=list[UnitOut])
def list_units(project_id: int | None = None, status: str | None = None,
               db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Unit)
    if project_id is not None:
        q = q.filter(Unit.project_id == project_id)
    if status:
        q = q.filter(Unit.status == status)
    return q.order_by(Unit.project_id, Unit.floor, Unit.unit_code).all()


@router.post("", response_model=UnitOut, status_code=201)
def create_unit(body: UnitIn, db: Session = Depends(get_db),
                _=Depends(require_perm("project:write"))):
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "所属项目不存在")
    if body.status not in _STATUSES:
        raise HTTPException(400, f"非法铺位状态：{body.status}")
    dup = db.query(Unit).filter(Unit.project_id == body.project_id,
                                Unit.unit_code == body.unit_code).first()
    if dup:
        raise HTTPException(409, f"该项目下铺位编码已存在：{body.unit_code}")
    u = Unit(**body.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.get("/{unit_id}", response_model=UnitOut)
def get_unit(unit_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    u = db.get(Unit, unit_id)
    if not u:
        raise HTTPException(404, "铺位不存在")
    return u


@router.patch("/{unit_id}", response_model=UnitOut)
def update_unit(unit_id: int, body: UnitIn, db: Session = Depends(get_db),
                _=Depends(require_perm("project:write"))):
    u = db.get(Unit, unit_id)
    if not u:
        raise HTTPException(404, "铺位不存在")
    for k, v in body.model_dump(exclude={"project_id", "unit_code"}).items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return u


@router.post("/{unit_id}/status", response_model=UnitOut)
def change_status(unit_id: int, body: UnitStatusIn, db: Session = Depends(get_db),
                  _=Depends(require_perm("project:write"))):
    u = db.get(Unit, unit_id)
    if not u:
        raise HTTPException(404, "铺位不存在")
    if body.status not in _STATUSES:
        raise HTTPException(400, f"非法铺位状态：{body.status}")
    u.status = body.status
    db.commit()
    db.refresh(u)
    return u
