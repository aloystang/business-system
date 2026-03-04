from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import EXPORT_DIR
from ..deps import get_current_user, get_db
from ..models import Deliverable, Project
from ..services.audit import log_event
from ..services.pdf_export import generate_project_pdf

router = APIRouter(tags=["export"])


@router.post("/api/projects/{project_id}/export/pdf")
def export_project_pdf(
    project_id: int,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    audience = payload.get("audience", "internal")
    if audience not in {"internal", "external"}:
        raise HTTPException(status_code=400, detail="Invalid audience")

    deliverables = (
        db.query(Deliverable)
        .filter(Deliverable.project_id == project_id)
        .order_by(Deliverable.created_at.desc())
        .all()
    )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"project_{project_id}_{audience}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    file_path = EXPORT_DIR / filename
    generate_project_pdf(project, deliverables, audience, file_path)

    log_event(
        db,
        action="PDF_EXPORT",
        entity_type="project",
        entity_id=project.id,
        user_id=user.id,
        metadata={"audience": audience, "file": filename},
        ip=request.client.host if request.client else None,
    )

    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)
