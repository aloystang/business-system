from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import DATA_DIR, EXPORT_DIR
from ..deps import get_db
from ..models import Deliverable, ExternalShare, Project
from ..schemas import PublicDeliverableOut, PublicProjectOut
from ..services.audit import log_event
from ..services.pdf_export import generate_project_pdf

router = APIRouter(prefix="/api/public", tags=["public"])


def _get_share_or_raise(db: Session, token: str):
    share = db.query(ExternalShare).filter(ExternalShare.token == token).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    if share.revoked:
        raise HTTPException(status_code=410, detail="Share revoked")
    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share expired")
    project = db.query(Project).filter(Project.id == share.project_id).first()
    if not project or not project.external_enabled:
        raise HTTPException(status_code=410, detail="Share disabled")
    return share, project


@router.get("/share/{token}", response_model=PublicProjectOut)
def get_public_project(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    share, project = _get_share_or_raise(db, token)

    payload = PublicProjectOut(
        code=project.code,
        name=project.name,
        region=project.region,
        asset_type=project.asset_type,
        client_name=project.client_name,
        address=project.address,
        area_m2=project.area_m2,
        population_index=project.population_index,
        current_stage=project.current_stage,
        external_summary=project.external_summary,
    )

    log_event(
        db,
        action="SHARE_VIEW",
        entity_type="share",
        entity_id=token,
        user_id=None,
        metadata={"project_id": project.id, "token": token},
        ip=request.client.host if request.client else None,
    )

    return payload


@router.get("/share/{token}/deliverables", response_model=list[PublicDeliverableOut])
def list_public_deliverables(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    share, project = _get_share_or_raise(db, token)
    items = (
        db.query(Deliverable)
        .filter(Deliverable.project_id == project.id)
        .filter(Deliverable.is_external_visible.is_(True))
        .order_by(Deliverable.created_at.desc())
        .all()
    )

    log_event(
        db,
        action="SHARE_VIEW_DELIVERABLES",
        entity_type="share",
        entity_id=token,
        user_id=None,
        metadata={"project_id": project.id, "token": token},
        ip=request.client.host if request.client else None,
    )

    return items


@router.get("/share/{token}/deliverables/{deliverable_id}/download")
def download_public_deliverable(
    token: str,
    deliverable_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    share, project = _get_share_or_raise(db, token)
    deliverable = (
        db.query(Deliverable)
        .filter(Deliverable.id == deliverable_id)
        .filter(Deliverable.project_id == project.id)
        .filter(Deliverable.is_external_visible.is_(True))
        .first()
    )
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")

    file_path = DATA_DIR / deliverable.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing")

    log_event(
        db,
        action="SHARE_FILE_DOWNLOAD",
        entity_type="deliverable",
        entity_id=deliverable.id,
        user_id=None,
        metadata={"project_id": project.id, "token": token, "deliverable_id": deliverable.id},
        ip=request.client.host if request.client else None,
    )

    return FileResponse(
        path=file_path,
        media_type=deliverable.mime_type or "application/octet-stream",
        filename=deliverable.file_name,
    )


@router.get("/share/{token}/pdf")
def export_public_pdf(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    share, project = _get_share_or_raise(db, token)
    deliverables = (
        db.query(Deliverable)
        .filter(Deliverable.project_id == project.id)
        .order_by(Deliverable.created_at.desc())
        .all()
    )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"share_{token}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    file_path = EXPORT_DIR / filename
    generate_project_pdf(project, deliverables, "external", file_path)

    log_event(
        db,
        action="SHARE_PDF_EXPORT",
        entity_type="share",
        entity_id=token,
        user_id=None,
        metadata={"project_id": project.id, "token": token, "file": filename},
        ip=request.client.host if request.client else None,
    )

    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)
