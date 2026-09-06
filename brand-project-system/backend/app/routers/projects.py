"""项目路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Project, ProjectContact, ProjectLocation, ProjectScore, User
from ..schemas import (
    ContactIn, ContactOut, LocationUpdateIn, ProjectCreate, ProjectOut, ScoreIn, ScoreOut,
)
from ..services import classification, scoring
from ..services.audit import record
from ..services.geocoding import (
    LocationInvariantError,
    apply_geocode,
    enforce_location_invariant,
    geocode_address,
)

router = APIRouter(prefix="/api/v1/projects", tags=["项目"])


@router.get("", response_model=list[ProjectOut])
def list_projects(q: str | None = None, type: str | None = None, status: str | None = None,
                  db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(Project).options(joinedload(Project.location)).filter(
        Project.is_deleted.is_(False))
    if q:
        query = query.filter(Project.project_name.like(f"%{q}%"))
    if type:
        query = query.filter(Project.project_type == type)
    if status:
        query = query.filter(Project.project_status == status)
    return query.order_by(Project.project_code).all()


@router.post("/recompute-status")
def recompute_status(db: Session = Depends(get_db),
                     user: User = Depends(require_perm("project:write"))):
    """按经营数据（生效租约/在营商户/在租铺位）批量重分项目状态。"""
    changes = classification.recompute_all_statuses(db)
    for c in changes:
        record(db, user, "reclassify", "project", None, c)
    db.commit()
    return {"changed": len(changes), "details": changes}


@router.post("/recompute-types")
def recompute_types(apply: bool = False, only_imported: bool = True,
                    db: Session = Depends(get_db),
                    user: User = Depends(require_perm("project:write"))):
    """按业态细分口径重算项目类型。apply=false 仅预览(dry-run)，true 才落库。"""
    changes = classification.recompute_project_types(db, only_imported=only_imported,
                                                     apply=apply)
    if apply:
        for c in changes:
            record(db, user, "reclassify_type", "project", None, c)
        db.commit()
    return {"applied": apply, "changed": len(changes), "details": changes}


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Project).options(joinedload(Project.location)).filter(
        Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "项目不存在")
    return p


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db),
                   _=Depends(require_perm("project:write"))):
    if db.query(Project).filter(Project.project_code == body.project_code).first():
        raise HTTPException(409, f"项目编码已存在：{body.project_code}")
    try:
        classification.validate_project_type(db, body.project_type)
        classification.validate_project_status(db, body.project_status)
    except classification.ClassificationError as e:
        raise HTTPException(400, str(e))
    p = Project(
        project_code=body.project_code, project_name=body.project_name,
        project_short_name=body.project_short_name, project_type=body.project_type,
        project_status=body.project_status, operator=body.operator,
        asset_holder=body.asset_holder, business_area_m2=body.business_area_m2,
        leasable_area_m2=body.business_area_m2, target_formats=body.target_formats,
        core_customers=body.core_customers, cooperation_will=body.cooperation_will,
        is_sensitive=body.is_sensitive,
    )
    db.add(p)
    db.flush()
    loc = ProjectLocation(project_id=p.id, province=body.province, city=body.city,
                          district=body.district, address=body.address,
                          geocoding_status="待定位")
    # 新建时自动解析坐标（失败则保持“定位失败”，不落错误坐标）
    apply_geocode(loc, geocode_address(body.address, body.city))
    db.add(loc)
    db.commit()
    return db.get(Project, p.id, options=[joinedload(Project.location)])


@router.put("/{project_id}/location", response_model=ProjectOut)
def update_location(project_id: int, body: LocationUpdateIn, db: Session = Depends(get_db),
                    _=Depends(require_perm("project:write"))):
    p = db.get(Project, project_id, options=[joinedload(Project.location)])
    if not p:
        raise HTTPException(404, "项目不存在")
    try:
        enforce_location_invariant(body.geocoding_status, body.longitude, body.latitude)
    except LocationInvariantError as e:
        raise HTTPException(400, str(e))
    loc = p.location or ProjectLocation(project_id=p.id)
    loc.province, loc.city, loc.district, loc.address = (
        body.province, body.city, body.district, body.address)
    loc.longitude, loc.latitude = body.longitude, body.latitude
    loc.geocoding_status, loc.manually_adjusted = body.geocoding_status, body.manually_adjusted
    if loc.id is None:
        db.add(loc)
    db.commit()
    return db.get(Project, p.id, options=[joinedload(Project.location)])


# ---------- 项目联系人 ----------

@router.get("/{project_id}/contacts", response_model=list[ContactOut])
def list_contacts(project_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    return db.query(ProjectContact).filter(ProjectContact.project_id == project_id).all()


@router.post("/{project_id}/contacts", response_model=ContactOut, status_code=201)
def add_contact(project_id: int, body: ContactIn, db: Session = Depends(get_db),
                _=Depends(require_perm("project:write"))):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    c = ProjectContact(project_id=project_id, **body.model_dump(exclude={"region"}))
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ---------- 项目评分 ----------

@router.get("/{project_id}/scores", response_model=list[ScoreOut])
def list_scores(project_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(ProjectScore).filter(ProjectScore.project_id == project_id).order_by(
        ProjectScore.id.desc()).all()


@router.post("/{project_id}/scores", response_model=ScoreOut, status_code=201)
def submit_score(project_id: int, body: ScoreIn, db: Session = Depends(get_db),
                 user: User = Depends(require_perm("project:write"))):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "项目不存在")
    if len(body.dims) != len(scoring.PROJECT_DIMS):
        raise HTTPException(400, f"须提交 {len(scoring.PROJECT_DIMS)} 个评分维度")
    try:
        total, grade = scoring.total_and_grade(body.dims)
    except ValueError as e:
        raise HTTPException(400, str(e))
    db.query(ProjectScore).filter(ProjectScore.project_id == project_id,
                                  ProjectScore.is_current.is_(True)).update(
        {"is_current": False})
    fields = dict(zip(scoring.PROJECT_DIMS, body.dims))
    s = ProjectScore(project_id=project_id, total_score=total, grade=grade, basis=body.basis,
                     scorer_id=user.id, rule_version=scoring.RULE_VERSION, is_current=True,
                     **fields)
    p.grade = grade
    db.add(s)
    record(db, user, "score", "project", project_id, {"total": total, "grade": grade})
    db.commit()
    db.refresh(s)
    return s
