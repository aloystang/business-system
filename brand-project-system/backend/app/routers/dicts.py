"""字典与分类路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import BrandCategory, BrandTag, Dictionary, ProjectTag, User
from ..schemas import DictIn, DictOut

router = APIRouter(prefix="/api/v1", tags=["字典"])


@router.get("/dicts", response_model=list[DictOut])
def list_dicts(type: str | None = None, db: Session = Depends(get_db),
               _=Depends(get_current_user)):
    q = db.query(Dictionary).filter(Dictionary.is_active.is_(True))
    if type:
        q = q.filter(Dictionary.dict_type == type)
    return q.order_by(Dictionary.dict_type, Dictionary.sort_no).all()


@router.post("/dicts", response_model=DictOut, status_code=201)
def create_dict(body: DictIn, db: Session = Depends(get_db),
                _: User = Depends(require_perm("dict:write"))):
    dup = db.query(Dictionary).filter(Dictionary.dict_type == body.dict_type,
                                      Dictionary.code == body.code).first()
    if dup:
        raise HTTPException(409, "该字典项已存在")
    d = Dictionary(**body.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/dicts/{dict_id}")
def delete_dict(dict_id: int, db: Session = Depends(get_db),
                _=Depends(require_perm("dict:write"))):
    d = db.get(Dictionary, dict_id)
    if not d:
        raise HTTPException(404, "字典项不存在")
    db.delete(d)
    db.commit()
    return {"ok": True}


@router.get("/brand-categories/tree")
def category_tree(db: Session = Depends(get_db), _=Depends(get_current_user)):
    cats = db.query(BrandCategory).filter(BrandCategory.is_active.is_(True)).order_by(
        BrandCategory.sort_no).all()
    by_parent: dict[int | None, list] = {}
    for c in cats:
        by_parent.setdefault(c.parent_id, []).append(c)

    def build(parent_id):
        return [{"id": c.id, "code": c.code, "name": c.name, "level": c.level,
                 "children": build(c.id)} for c in by_parent.get(parent_id, [])]

    return {"tree": build(None)}


@router.get("/tags")
def list_tags(scope: str = "brand", db: Session = Depends(get_db), _=Depends(get_current_user)):
    Model = ProjectTag if scope == "project" else BrandTag
    rows = db.query(Model).filter(Model.is_active.is_(True)).order_by(Model.sort_no).all()
    return [{"id": t.id, "code": t.code, "name": t.name} for t in rows]
