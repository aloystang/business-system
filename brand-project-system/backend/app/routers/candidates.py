"""候选清单路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Brand, CandidateList, CandidateListItem, User
from ..schemas import (
    CandidateItemIn, CandidateItemOut, CandidateItemStatusIn, CandidateListIn, CandidateListOut,
)

router = APIRouter(prefix="/api/v1/candidate-lists", tags=["候选清单"])
_ITEM_STATUSES = {"储备", "已接触", "洽谈中", "已签约", "已否决"}


def _item_out(it: CandidateListItem) -> CandidateItemOut:
    return CandidateItemOut(id=it.id, brand_id=it.brand_id,
                           brand_name=it.brand.brand_name if it.brand else None,
                           item_status=it.item_status, note=it.note)


@router.get("", response_model=list[CandidateListOut])
def list_lists(db: Session = Depends(get_db), _=Depends(get_current_user)):
    lists = db.query(CandidateList).options(
        joinedload(CandidateList.items).joinedload(CandidateListItem.brand)).all()
    return [CandidateListOut(id=l.id, list_name=l.list_name,
                            target_project_id=l.target_project_id, description=l.description,
                            items=[_item_out(i) for i in l.items]) for l in lists]


@router.post("", response_model=CandidateListOut, status_code=201)
def create_list(body: CandidateListIn, db: Session = Depends(get_db),
                user: User = Depends(require_perm("match:write"))):
    cl = CandidateList(list_name=body.list_name, target_project_id=body.target_project_id,
                       description=body.description, owner_id=user.id)
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return CandidateListOut(id=cl.id, list_name=cl.list_name,
                           target_project_id=cl.target_project_id, description=cl.description,
                           items=[])


@router.post("/{list_id}/items", response_model=CandidateItemOut, status_code=201)
def add_item(list_id: int, body: CandidateItemIn, db: Session = Depends(get_db),
             user: User = Depends(require_perm("match:write"))):
    if not db.get(CandidateList, list_id):
        raise HTTPException(404, "清单不存在")
    if body.item_status not in _ITEM_STATUSES:
        raise HTTPException(400, f"非法条目状态：{body.item_status}")
    dup = db.query(CandidateListItem).filter(
        CandidateListItem.list_id == list_id,
        CandidateListItem.brand_id == body.brand_id).first()
    if dup:
        raise HTTPException(409, "该品牌已在清单中")
    it = CandidateListItem(list_id=list_id, added_by=user.id, **body.model_dump())
    db.add(it)
    db.commit()
    db.refresh(it)
    it.brand = db.get(Brand, it.brand_id)
    return _item_out(it)


@router.patch("/{list_id}/items/{item_id}", response_model=CandidateItemOut)
def update_item(list_id: int, item_id: int, body: CandidateItemStatusIn,
                db: Session = Depends(get_db), _=Depends(require_perm("match:write"))):
    it = db.get(CandidateListItem, item_id)
    if not it or it.list_id != list_id:
        raise HTTPException(404, "条目不存在")
    if body.item_status not in _ITEM_STATUSES:
        raise HTTPException(400, f"非法条目状态：{body.item_status}")
    it.item_status = body.item_status
    db.commit()
    db.refresh(it)
    return _item_out(it)


@router.delete("/{list_id}/items/{item_id}")
def remove_item(list_id: int, item_id: int, db: Session = Depends(get_db),
                _=Depends(require_perm("match:write"))):
    it = db.get(CandidateListItem, item_id)
    if not it or it.list_id != list_id:
        raise HTTPException(404, "条目不存在")
    db.delete(it)
    db.commit()
    return {"ok": True}
