from __future__ import annotations

from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import PUBLIC_SHARE_BASE
from ..deps import get_current_user, get_db
from ..models import ExternalShare, Project
from ..schemas import ShareCreateRequest, ShareResponse
from ..services.audit import log_event

router = APIRouter(tags=["shares"])


def _generate_token(db: Session) -> str:
    for _ in range(5):
        token = secrets.token_urlsafe(24)
        exists = db.query(ExternalShare).filter(ExternalShare.token == token).first()
        if not exists:
            return token
    raise HTTPException(status_code=500, detail="Failed to generate token")


@router.post("/api/projects/{project_id}/share", response_model=ShareResponse)
def create_share(
    project_id: int,
    request: Request,
    payload: ShareCreateRequest | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.external_enabled:
        raise HTTPException(status_code=400, detail="Enable external sharing first")

    payload = payload or ShareCreateRequest()
    expires_in_days = payload.expires_in_days
    expires_at = None
    if expires_in_days is None or expires_in_days == 0:
        expires_at = None
    elif expires_in_days < 0:
        raise HTTPException(status_code=400, detail="Invalid expires_in_days")
    else:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    token = _generate_token(db)
    share = ExternalShare(
        project_id=project_id,
        token=token,
        expires_at=expires_at,
        revoked=False,
        created_by=user.id,
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    log_event(
        db,
        action="SHARE_CREATE",
        entity_type="project",
        entity_id=project_id,
        user_id=user.id,
        metadata={"project_id": project_id, "token": token, "expires_at": str(expires_at)},
        ip=request.client.host if request.client else None,
    )

    base = PUBLIC_SHARE_BASE.rstrip("/")
    return ShareResponse(
        share_url=f"{base}/share/{token}",
        token=token,
        expires_at=expires_at,
    )


@router.post("/api/shares/{token}/revoke")
def revoke_share(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    share = db.query(ExternalShare).filter(ExternalShare.token == token).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    share.revoked = True
    db.commit()

    log_event(
        db,
        action="SHARE_REVOKE",
        entity_type="share",
        entity_id=token,
        user_id=user.id,
        metadata={"project_id": share.project_id, "token": token},
        ip=request.client.host if request.client else None,
    )

    return {"ok": True}
