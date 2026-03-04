from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Project, StageTransition
from ..schemas import (
    ProjectCreate,
    ProjectList,
    ProjectOut,
    ProjectUpdate,
    StageCheckResult,
    StageTransitionCreate,
    StageTransitionOut,
)
from ..services.audit import log_event
from ..services.stage_rules import check_requirements, get_next_stage, validate_transition, load_rules

router = APIRouter(prefix="/api/lifecycle/projects", tags=["projects"])


@router.get("", response_model=ProjectList)
def list_projects(
    q: str | None = None,
    stage: str | None = None,
    owner_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(Project)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Project.name.ilike(like)) | (Project.code.ilike(like)) | (Project.client_name.ilike(like))
        )
    if stage:
        query = query.filter(Project.current_stage == stage)
    if owner_id:
        query = query.filter(Project.owner_user_id == owner_id)

    total = query.count()
    items = (
        query.order_by(Project.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ProjectList(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = Project(**payload.dict())
    db.add(project)
    db.commit()
    db.refresh(project)
    log_event(
        db,
        action="PROJECT_CREATE",
        entity_type="project",
        entity_id=project.id,
        user_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    log_event(
        db,
        action="PROJECT_UPDATE",
        entity_type="project",
        entity_id=project.id,
        user_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    log_event(
        db,
        action="PROJECT_DELETE",
        entity_type="project",
        entity_id=project_id,
        user_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return {"ok": True}


@router.get("/{project_id}/transitions", response_model=list[StageTransitionOut])
def list_transitions(
    project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    return (
        db.query(StageTransition)
        .filter(StageTransition.project_id == project_id)
        .order_by(StageTransition.transitioned_at.desc())
        .all()
    )


@router.post("/{project_id}/transition", response_model=StageTransitionOut)
def transition_stage(
    project_id: int,
    payload: StageTransitionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    validation = validate_transition(project, payload.to_stage.value, db)
    if not validation.get("ok"):
        raise HTTPException(status_code=400, detail=validation.get("reason", "Validation failed"))

    transition = StageTransition(
        project_id=project.id,
        from_stage=project.current_stage,
        to_stage=payload.to_stage.value,
        transitioned_by=user.id,
        note=payload.note,
    )
    project.current_stage = payload.to_stage
    db.add(transition)
    db.commit()
    db.refresh(transition)

    log_event(
        db,
        action="STAGE_TRANSITION",
        entity_type="project",
        entity_id=project.id,
        user_id=user.id,
        metadata={"from": transition.from_stage, "to": transition.to_stage},
        ip=request.client.host if request.client else None,
    )
    return transition


@router.get("/{project_id}/stage-check", response_model=StageCheckResult)
def stage_check(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    target_stage = get_next_stage(project.current_stage)
    if target_stage is None:
        return StageCheckResult(
            current_stage=project.current_stage,
            target_stage=project.current_stage,
            required_fields=[],
            required_deliverables=[],
            missing_fields=[],
            missing_deliverables=[],
            ok=True,
        )
    missing_fields, missing_deliverables = check_requirements(project, target_stage, db)
    rules = load_rules().get("stages", {}).get(target_stage, {})
    return StageCheckResult(
        current_stage=project.current_stage,
        target_stage=target_stage,
        required_fields=rules.get("required_fields", []),
        required_deliverables=rules.get("required_deliverables", []),
        missing_fields=missing_fields,
        missing_deliverables=missing_deliverables,
        ok=not missing_fields and not missing_deliverables,
    )
