from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Issue, Project, IssueStatus
from ..schemas import IssueCreate, IssueOut, IssueUpdate
from ..services.audit import log_event

router = APIRouter(tags=["issues"])


@router.get("/api/issues", response_model=list[IssueOut])
def list_issues(
    project_id: int | None = None,
    status: str | None = None,
    assignee_user_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(Issue)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    if assignee_user_id:
        query = query.filter(Issue.assignee_user_id == assignee_user_id)
    return query.order_by(Issue.updated_at.desc()).all()


@router.post("/api/projects/{project_id}/issues", response_model=IssueOut)
def create_issue(
    project_id: int,
    payload: IssueCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    issue = Issue(project_id=project_id, created_by=user.id, **payload.dict())
    db.add(issue)
    db.commit()
    db.refresh(issue)

    log_event(
        db,
        action="ISSUE_CREATE",
        entity_type="issue",
        entity_id=issue.id,
        user_id=user.id,
        metadata={"project_id": project_id},
        ip=request.client.host if request.client else None,
    )

    return issue


@router.put("/api/issues/{issue_id}", response_model=IssueOut)
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(issue, key, value)
    db.commit()
    db.refresh(issue)

    log_event(
        db,
        action="ISSUE_UPDATE",
        entity_type="issue",
        entity_id=issue.id,
        user_id=user.id,
        ip=request.client.host if request.client else None,
    )

    return issue


@router.post("/api/issues/{issue_id}/resolve", response_model=IssueOut)
def resolve_issue(
    issue_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue.status = IssueStatus.resolved
    issue.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(issue)

    log_event(
        db,
        action="ISSUE_RESOLVE",
        entity_type="issue",
        entity_id=issue.id,
        user_id=user.id,
        ip=request.client.host if request.client else None,
    )

    return issue
