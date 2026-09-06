"""品牌路由：CRUD + 联系人 + 拓展要求 + 评分。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Brand, BrandContact, BrandExpansion, BrandScore, User
from ..schemas import (
    BrandCreate, BrandOut, BrandUpdate, ContactIn, ContactOut,
    ExpansionIn, ExpansionOut, ScoreIn, ScoreOut,
)
from ..services import classification, scoring
from ..services.audit import record

router = APIRouter(prefix="/api/v1/brands", tags=["品牌"])


def _get(db: Session, brand_id: int) -> Brand:
    b = db.get(Brand, brand_id)
    if not b or b.is_deleted:
        raise HTTPException(404, "品牌不存在")
    return b


@router.get("", response_model=list[BrandOut])
def list_brands(q: str | None = None, l1: str | None = None,
                db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = db.query(Brand).filter(Brand.is_deleted.is_(False))
    if q:
        query = query.filter(Brand.brand_name.like(f"%{q}%"))
    if l1:
        query = query.filter(Brand.l1_category == l1)
    return query.order_by(Brand.brand_code).all()


@router.post("", response_model=BrandOut, status_code=201)
def create_brand(body: BrandCreate, db: Session = Depends(get_db),
                 user: User = Depends(require_perm("brand:write"))):
    if db.query(Brand).filter(Brand.brand_code == body.brand_code).first():
        raise HTTPException(409, f"品牌编码已存在：{body.brand_code}")
    try:
        classification.validate_brand_category(
            db, body.l1_category, body.l2_category, body.l3_category)
    except classification.ClassificationError as e:
        raise HTTPException(400, str(e))
    b = Brand(**body.model_dump())
    db.add(b)
    db.flush()
    record(db, user, "create", "brand", b.id, {"code": b.brand_code})
    db.commit()
    db.refresh(b)
    return b


@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return _get(db, brand_id)


@router.patch("/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: int, body: BrandUpdate, db: Session = Depends(get_db),
                 user: User = Depends(require_perm("brand:write"))):
    b = _get(db, brand_id)
    patch = body.model_dump(exclude_unset=True)
    if {"l1_category", "l2_category", "l3_category"} & patch.keys():
        try:
            classification.validate_brand_category(
                db,
                patch.get("l1_category", b.l1_category),
                patch.get("l2_category", b.l2_category),
                patch.get("l3_category", b.l3_category),
            )
        except classification.ClassificationError as e:
            raise HTTPException(400, str(e))
    for k, v in patch.items():
        setattr(b, k, v)
    record(db, user, "update", "brand", b.id)
    db.commit()
    db.refresh(b)
    return b


@router.delete("/{brand_id}")
def delete_brand(brand_id: int, db: Session = Depends(get_db),
                 user: User = Depends(require_perm("brand:write"))):
    b = _get(db, brand_id)
    b.is_deleted = True
    record(db, user, "delete", "brand", b.id)
    db.commit()
    return {"ok": True, "deleted_id": brand_id}


# ---------- 联系人 ----------

@router.get("/{brand_id}/contacts", response_model=list[ContactOut])
def list_contacts(brand_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    _get(db, brand_id)
    return db.query(BrandContact).filter(BrandContact.brand_id == brand_id).all()


@router.post("/{brand_id}/contacts", response_model=ContactOut, status_code=201)
def add_contact(brand_id: int, body: ContactIn, db: Session = Depends(get_db),
                _=Depends(require_perm("brand:write"))):
    _get(db, brand_id)
    data = body.model_dump(exclude={"party_type"})
    c = BrandContact(brand_id=brand_id, **data)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{brand_id}/contacts/{cid}")
def del_contact(brand_id: int, cid: int, db: Session = Depends(get_db),
                _=Depends(require_perm("brand:write"))):
    c = db.get(BrandContact, cid)
    if not c or c.brand_id != brand_id:
        raise HTTPException(404, "联系人不存在")
    db.delete(c)
    db.commit()
    return {"ok": True}


# ---------- 拓展要求 ----------

@router.get("/{brand_id}/expansion", response_model=ExpansionOut | None)
def get_expansion(brand_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    _get(db, brand_id)
    return db.query(BrandExpansion).filter(BrandExpansion.brand_id == brand_id).first()


@router.put("/{brand_id}/expansion", response_model=ExpansionOut)
def put_expansion(brand_id: int, body: ExpansionIn, db: Session = Depends(get_db),
                  _=Depends(require_perm("brand:write"))):
    _get(db, brand_id)
    exp = db.query(BrandExpansion).filter(BrandExpansion.brand_id == brand_id).first()
    if not exp:
        exp = BrandExpansion(brand_id=brand_id)
        db.add(exp)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(exp, k, v)
    db.commit()
    db.refresh(exp)
    return exp


# ---------- 评分（按规则算等级，历史留档） ----------

@router.get("/{brand_id}/scores", response_model=list[ScoreOut])
def list_scores(brand_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    _get(db, brand_id)
    return db.query(BrandScore).filter(BrandScore.brand_id == brand_id).order_by(
        BrandScore.id.desc()).all()


@router.post("/{brand_id}/scores", response_model=ScoreOut, status_code=201)
def submit_score(brand_id: int, body: ScoreIn, db: Session = Depends(get_db),
                 user: User = Depends(require_perm("brand:write"))):
    b = _get(db, brand_id)
    if len(body.dims) != len(scoring.BRAND_DIMS):
        raise HTTPException(400, f"须提交 {len(scoring.BRAND_DIMS)} 个评分维度")
    try:
        total, grade = scoring.total_and_grade(body.dims)
    except ValueError as e:
        raise HTTPException(400, str(e))
    db.query(BrandScore).filter(BrandScore.brand_id == brand_id,
                                BrandScore.is_current.is_(True)).update(
        {"is_current": False})
    fields = dict(zip(scoring.BRAND_DIMS, body.dims))
    s = BrandScore(brand_id=brand_id, total_score=total, grade=grade, basis=body.basis,
                   scorer_id=user.id, rule_version=scoring.RULE_VERSION, is_current=True,
                   **fields)
    b.grade = grade
    db.add(s)
    record(db, user, "score", "brand", brand_id, {"total": total, "grade": grade})
    db.commit()
    db.refresh(s)
    return s
