from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import DATA_DIR, UPLOAD_DIR
from ..deps import get_current_user, get_db
from ..models import Deliverable, Project
from ..schemas import DeliverableOut
from ..services.audit import log_event

router = APIRouter(tags=["deliverables"])


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


@router.post("/api/projects/{project_id}/deliverables", response_model=DeliverableOut)
async def upload_deliverable(
    project_id: int,
    request: Request,
    file: UploadFile = File(...),
    type: str = Form(...),
    title: str = Form(...),
    stage: str = Form(...),
    is_external_visible: str | None = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    latest_version = (
        db.query(func.max(Deliverable.version))
        .filter(Deliverable.project_id == project_id, Deliverable.type == type)
        .scalar()
    )
    version = (latest_version or 0) + 1

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = UPLOAD_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex}_{file.filename}"
    file_path = project_dir / safe_name
    contents = await file.read()
    file_path.write_bytes(contents)

    rel_path = str(file_path.relative_to(DATA_DIR))

    deliverable = Deliverable(
        project_id=project_id,
        stage=stage,
        type=type,
        title=title,
        version=version,
        file_path=rel_path,
        file_name=file.filename,
        mime_type=file.content_type,
        is_external_visible=_parse_bool(is_external_visible),
        created_by=user.id,
    )

    db.add(deliverable)
    db.commit()
    db.refresh(deliverable)

    log_event(
        db,
        action="FILE_UPLOAD",
        entity_type="deliverable",
        entity_id=deliverable.id,
        user_id=user.id,
        metadata={"project_id": project_id, "type": type, "version": version},
        ip=request.client.host if request.client else None,
    )

    return deliverable


@router.get("/api/projects/{project_id}/deliverables", response_model=list[DeliverableOut])
def list_deliverables(
    project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    return (
        db.query(Deliverable)
        .filter(Deliverable.project_id == project_id)
        .order_by(Deliverable.created_at.desc())
        .all()
    )


@router.get("/api/deliverables/{deliverable_id}/download")
def download_deliverable(
    deliverable_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    deliverable = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    file_path = DATA_DIR / deliverable.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing")
    log_event(
        db,
        action="FILE_DOWNLOAD",
        entity_type="deliverable",
        entity_id=deliverable.id,
        user_id=user.id,
        ip=request.client.host if request.client else None,
    )
    return FileResponse(
        path=file_path,
        media_type=deliverable.mime_type or "application/octet-stream",
        filename=deliverable.file_name,
    )
