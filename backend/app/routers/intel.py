from __future__ import annotations

from datetime import datetime, timedelta
import json
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db, require_roles
from ..models import (
    IntelItem,
    IntelProjectLink,
    IntelSyncJob,
    IntelWatchRule,
    ProjectBaseInfo,
    UserRole,
)
from ..schemas import (
    IntelFollowUpIn,
    IntelItemDetailOut,
    IntelItemsResponse,
    IntelItemListOut,
    IntelKpisOut,
    IntelLinkProjectIn,
    IntelLinkProjectOut,
    IntelLinkedProjectOut,
    IntelSyncJobOut,
    IntelSyncRunIn,
    IntelSyncRunOut,
    IntelWatchRuleCreate,
    IntelWatchRuleOut,
    IntelWatchRuleUpdate,
)
from ..services.audit import log_event
from ..services.intel import now_iso, run_sync

router = APIRouter(prefix="/api/intel", tags=["intel"])


def extract_intel_source_meta(payload_json: Optional[str]) -> tuple[Optional[str], list[str]]:
    if not payload_json:
        return None, []
    try:
        payload = json.loads(payload_json)
    except Exception:
        return None, []
    category = payload.get("source_category")
    tags = payload.get("source_tags") or []
    if not isinstance(tags, list):
        tags = []
    tags = [str(tag).strip() for tag in tags if str(tag).strip()]
    return (str(category).strip() if category else None), tags


def _safe_date(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.min


@router.get("/kpis", response_model=IntelKpisOut)
def get_intel_kpis(
    item_type: str = Query(default="all", pattern="^(all|news|tender)$"),
    city: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    query = db.query(IntelItem)
    if item_type != "all":
        query = query.filter(IntelItem.item_type == item_type)
    if city:
        query = query.filter(IntelItem.city == city)
    if district:
        query = query.filter(IntelItem.district == district)

    rows = query.all()
    today_prefix = datetime.utcnow().date().isoformat()
    total_count = len(rows)
    today_count = sum(1 for row in rows if (row.published_at or "").startswith(today_prefix))
    pending_count = sum(1 for row in rows if (row.follow_up_status or "none") == "pending")
    now = datetime.utcnow()
    due_soon = 0
    hit_count = 0
    for row in rows:
        if (row.matched_rule_count or 0) > 0:
            hit_count += 1
        deadline = _safe_date(row.deadline_at)
        if deadline != datetime.min and now <= deadline <= now + timedelta(days=7):
            due_soon += 1
    hit_rate = round((hit_count / total_count) * 100, 2) if total_count else 0.0
    return IntelKpisOut(
        total_count=total_count,
        today_count=today_count,
        pending_follow_up_count=pending_count,
        due_soon_count=due_soon,
        hit_rate=hit_rate,
    )


@router.get("/items", response_model=IntelItemsResponse)
def list_intel_items(
    item_type: str = Query(default="all", pattern="^(all|news|tender)$"),
    city: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    follow_up_status: str = Query(default="all", pattern="^(all|none|pending|done|ignored)$"),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    base_query = db.query(IntelItem)
    if item_type != "all":
        base_query = base_query.filter(IntelItem.item_type == item_type)
    if city:
        base_query = base_query.filter(IntelItem.city == city)
    if district:
        base_query = base_query.filter(IntelItem.district == district)
    if follow_up_status != "all":
        base_query = base_query.filter(IntelItem.follow_up_status == follow_up_status)
    if date_from:
        base_query = base_query.filter(IntelItem.published_at >= date_from)
    if date_to:
        base_query = base_query.filter(IntelItem.published_at <= date_to)
    if keyword:
        kw = keyword.strip()
        if kw:
            base_query = base_query.filter(
                or_(
                    IntelItem.title.contains(kw),
                    IntelItem.summary.contains(kw),
                    IntelItem.source_name.contains(kw),
                    IntelItem.issuer.contains(kw),
                )
            )

    total = base_query.count()
    rows = (
        base_query.order_by(IntelItem.published_at.desc(), IntelItem.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    item_ids = [row.id for row in rows]
    link_counts = {}
    if item_ids:
        link_rows = (
            db.query(IntelProjectLink.intel_item_id, func.count(IntelProjectLink.id))
            .filter(IntelProjectLink.intel_item_id.in_(item_ids))
            .group_by(IntelProjectLink.intel_item_id)
            .all()
        )
        link_counts = {row[0]: int(row[1]) for row in link_rows}

    items = [
        (
            lambda category, tags: IntelItemListOut(
                id=row.id,
                item_type=row.item_type,
                title=row.title,
                source_name=row.source_name,
                source_category=category,
                source_tags=tags,
                published_at=row.published_at,
                city=row.city,
                district=row.district,
                summary=row.summary,
                raw_url=row.raw_url,
                budget_amount=row.budget_amount,
                deadline_at=row.deadline_at,
                issuer=row.issuer,
                matched_rule_count=int(row.matched_rule_count or 0),
                follow_up_status=row.follow_up_status or "none",
                linked_project_count=link_counts.get(row.id, 0),
                created_at=row.created_at,
            )
        )(*extract_intel_source_meta(row.payload_json))
        for row in rows
    ]
    return IntelItemsResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/items/{item_id}", response_model=IntelItemDetailOut)
def get_intel_item_detail(
    item_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    item = db.query(IntelItem).filter(IntelItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="情报不存在")

    link_rows = db.query(IntelProjectLink).filter(IntelProjectLink.intel_item_id == item_id).all()
    project_ids = [row.project_id for row in link_rows]
    project_name_map = {}
    if project_ids:
        projects = (
            db.query(ProjectBaseInfo.project_id, ProjectBaseInfo.project_name)
            .filter(ProjectBaseInfo.project_id.in_(project_ids))
            .all()
        )
        project_name_map = {row.project_id: row.project_name for row in projects}

    links = [
        IntelLinkedProjectOut(
            project_id=row.project_id,
            project_name=project_name_map.get(row.project_id),
            linked_at=row.created_at,
            link_type=row.link_type,
        )
        for row in link_rows
    ]

    category, tags = extract_intel_source_meta(item.payload_json)

    return IntelItemDetailOut(
        id=item.id,
        item_type=item.item_type,
        title=item.title,
        source_name=item.source_name,
        source_category=category,
        source_tags=tags,
        published_at=item.published_at,
        city=item.city,
        district=item.district,
        summary=item.summary,
        raw_url=item.raw_url,
        budget_amount=item.budget_amount,
        deadline_at=item.deadline_at,
        issuer=item.issuer,
        payload_json=item.payload_json,
        matched_rule_count=int(item.matched_rule_count or 0),
        follow_up_status=item.follow_up_status or "none",
        linked_projects=links,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("/items/{item_id}/link-project", response_model=IntelLinkProjectOut)
def link_item_project(
    item_id: str,
    payload: IntelLinkProjectIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    item = db.query(IntelItem).filter(IntelItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="情报不存在")
    project = db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    existing = (
        db.query(IntelProjectLink)
        .filter(
            and_(
                IntelProjectLink.intel_item_id == item_id,
                IntelProjectLink.project_id == payload.project_id,
            )
        )
        .first()
    )
    if existing:
        return IntelLinkProjectOut(
            intel_item_id=item_id,
            project_id=payload.project_id,
            link_type=existing.link_type,
        )

    link = IntelProjectLink(
        id=f"intel-link-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        intel_item_id=item_id,
        project_id=payload.project_id,
        link_type=payload.link_type,
        created_by=user.id,
        created_at=now_iso(),
    )
    db.add(link)
    db.commit()
    log_event(
        db,
        action="INTEL_LINK_PROJECT",
        entity_type="intel_item",
        entity_id=item_id,
        user_id=user.id,
        metadata={"project_id": payload.project_id, "link_type": payload.link_type},
        ip=request.client.host if request.client else None,
    )
    return IntelLinkProjectOut(
        intel_item_id=item_id,
        project_id=payload.project_id,
        link_type=payload.link_type,
    )


@router.post("/items/{item_id}/follow-up", response_model=IntelItemDetailOut)
def update_follow_up_status(
    item_id: str,
    payload: IntelFollowUpIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    item = db.query(IntelItem).filter(IntelItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="情报不存在")
    item.follow_up_status = payload.status
    item.updated_at = now_iso()
    db.commit()
    return get_intel_item_detail(item_id=item_id, db=db, user=user)


@router.post("/sync/run", response_model=IntelSyncRunOut)
def run_intel_sync(
    request: Request,
    payload: IntelSyncRunIn = Body(default_factory=IntelSyncRunIn),
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    try:
        job, stats = run_sync(
            db,
            created_by=user.id,
            trigger_type="manual",
            payload_items=payload.payload_items,
            window_start=payload.window_start,
            window_end=payload.window_end,
            item_type=payload.item_type,
            source_system=payload.source_system,
        )
        db.commit()
    except Exception as exc:
        db.commit()
        log_event(
            db,
            action="INTEL_SYNC_RUN",
            entity_type="intel_sync_job",
            entity_id="failed",
            user_id=user.id,
            metadata={"status": "failed", "message": str(exc), "source_system": payload.source_system},
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=500, detail=f"同步失败: {exc}") from exc

    log_event(
        db,
            action="INTEL_SYNC_RUN",
            entity_type="intel_sync_job",
            entity_id=job.id,
            user_id=user.id,
            metadata={"status": job.status, "source_system": payload.source_system, **stats},
            ip=request.client.host if request.client else None,
        )
    log_event(
        db,
        action="INTEL_ITEM_UPSERT",
        entity_type="intel_item",
        entity_id=job.id,
        user_id=user.id,
        metadata={"source_system": payload.source_system, **stats},
        ip=request.client.host if request.client else None,
    )
    if stats.get("matched_rule_hits", 0) > 0:
        log_event(
            db,
            action="INTEL_RULE_HIT",
            entity_type="intel_item",
            entity_id=job.id,
            user_id=user.id,
            metadata={"matched_rule_hits": stats["matched_rule_hits"]},
            ip=request.client.host if request.client else None,
        )

    return IntelSyncRunOut(
        job_id=job.id,
        source_system=job.source_system,
        status=job.status,
        pulled_count=job.pulled_count,
        upserted_count=job.upserted_count,
        deduped_count=job.deduped_count,
        failed_count=job.failed_count,
        matched_rule_hits=stats.get("matched_rule_hits", 0),
        started_at=job.started_at,
        ended_at=job.ended_at,
    )


@router.get("/sync/jobs", response_model=list[IntelSyncJobOut])
def list_sync_jobs(
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    _ = user
    rows = db.query(IntelSyncJob).order_by(IntelSyncJob.started_at.desc()).limit(limit).all()
    return [
        IntelSyncJobOut(
            id=row.id,
            source_system=row.source_system,
            trigger_type=row.trigger_type,
            status=row.status,
            started_at=row.started_at,
            ended_at=row.ended_at,
            window_start=row.window_start,
            window_end=row.window_end,
            pulled_count=row.pulled_count,
            upserted_count=row.upserted_count,
            deduped_count=row.deduped_count,
            failed_count=row.failed_count,
            error_message=row.error_message,
            created_by=row.created_by,
        )
        for row in rows
    ]


@router.get("/rules", response_model=list[IntelWatchRuleOut])
def list_watch_rules(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    rows = db.query(IntelWatchRule).order_by(IntelWatchRule.created_at.desc()).all()
    return [
        IntelWatchRuleOut(
            id=row.id,
            name=row.name,
            item_type=row.item_type,
            keywords=row.keywords,
            city=row.city,
            district=row.district,
            budget_min=row.budget_min,
            budget_max=row.budget_max,
            is_enabled=row.is_enabled,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.post("/rules", response_model=IntelWatchRuleOut)
def create_watch_rule(
    payload: IntelWatchRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    entity = IntelWatchRule(
        id=f"intel-rule-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        name=payload.name,
        item_type=payload.item_type,
        keywords=payload.keywords,
        city=payload.city,
        district=payload.district,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        is_enabled=payload.is_enabled,
        created_by=user.id,
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    db.add(entity)
    db.commit()
    log_event(
        db,
        action="INTEL_RULE_UPSERT",
        entity_type="intel_watch_rule",
        entity_id=entity.id,
        user_id=user.id,
        metadata=payload.model_dump(),
        ip=request.client.host if request.client else None,
    )
    return IntelWatchRuleOut(
        id=entity.id,
        name=entity.name,
        item_type=entity.item_type,
        keywords=entity.keywords,
        city=entity.city,
        district=entity.district,
        budget_min=entity.budget_min,
        budget_max=entity.budget_max,
        is_enabled=entity.is_enabled,
        created_by=entity.created_by,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.put("/rules/{rule_id}", response_model=IntelWatchRuleOut)
def update_watch_rule(
    rule_id: str,
    payload: IntelWatchRuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    entity = db.query(IntelWatchRule).filter(IntelWatchRule.id == rule_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="规则不存在")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(entity, key, value)
    entity.updated_at = now_iso()
    db.commit()
    log_event(
        db,
        action="INTEL_RULE_UPSERT",
        entity_type="intel_watch_rule",
        entity_id=entity.id,
        user_id=user.id,
        metadata=data,
        ip=request.client.host if request.client else None,
    )
    return IntelWatchRuleOut(
        id=entity.id,
        name=entity.name,
        item_type=entity.item_type,
        keywords=entity.keywords,
        city=entity.city,
        district=entity.district,
        budget_min=entity.budget_min,
        budget_max=entity.budget_max,
        is_enabled=entity.is_enabled,
        created_by=entity.created_by,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.delete("/rules/{rule_id}")
def delete_watch_rule(
    rule_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    entity = db.query(IntelWatchRule).filter(IntelWatchRule.id == rule_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(entity)
    db.commit()
    log_event(
        db,
        action="INTEL_RULE_DELETE",
        entity_type="intel_watch_rule",
        entity_id=rule_id,
        user_id=user.id,
        metadata={},
        ip=request.client.host if request.client else None,
    )
    return {"ok": True}
