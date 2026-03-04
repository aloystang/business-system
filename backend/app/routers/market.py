from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db, require_roles
from ..models import (
    MarketCompetitorItem,
    MarketMerchantItem,
    MarketSubmission,
    ProjectBaseInfo,
    UserRole,
)
from ..schemas import (
    MarketBulkActionIn,
    MarketBulkActionOut,
    MarketHistoryPointOut,
    MarketHistoryResponse,
    MarketHistorySubmissionOut,
    MarketHistorySummaryOut,
    MarketSubmissionCreateIn,
    MarketSubmissionCreateOut,
    SurveyDeleteActionOut,
    SurveyDeleteIn,
)
from ..services.audit import log_event
from ..services.market import create_market_submission

router = APIRouter(prefix="/api/market", tags=["market"])


def _safe_time(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _completeness_for_merchant(item: MarketMerchantItem) -> float:
    required = [
        item.name,
        item.category,
        item.area_m2,
        item.rent_unit_price,
        item.daily_flow,
        item.address,
        item.city,
        item.district,
    ]
    ok = sum(1 for value in required if value is not None and str(value).strip() != "")
    return ok / len(required)


def _completeness_for_competitor(item: MarketCompetitorItem) -> float:
    required = [
        item.name,
        item.scale_m2,
        item.avg_rent_unit_price,
        item.vacancy_rate,
        item.business_type,
        item.distance_km,
        item.target_people,
        item.address,
        item.city,
        item.district,
    ]
    ok = sum(1 for value in required if value is not None and str(value).strip() != "")
    return ok / len(required)


def _freshness_score(created_at: Optional[str]) -> float:
    dt = _safe_time(created_at)
    if dt == datetime.min.replace(tzinfo=timezone.utc):
        return 0.0
    days = max((datetime.now(timezone.utc) - dt).days, 0)
    if days <= 30:
        return 1.0
    if days >= 365:
        return 0.0
    return max(1.0 - (days - 30) / 335.0, 0.0)


def _to_point_rows(
    merchants: list[MarketMerchantItem],
    competitors: list[MarketCompetitorItem],
    project_name_map: dict[str, str],
) -> list[MarketHistoryPointOut]:
    points: list[MarketHistoryPointOut] = []
    for item in merchants:
        points.append(
            MarketHistoryPointOut(
                point_id=f"merchant:{item.id}",
                point_type="merchant",
                item_id=item.id,
                submission_id=item.submission_id,
                project_id=item.project_id,
                project_name=project_name_map.get(item.project_id or "", None),
                name=item.name,
                city=item.city,
                district=item.district,
                industry=item.category,
                target_people=None,
                address=item.address,
                created_at=item.created_at,
                deleted=bool(item.deleted),
                deleted_at=item.deleted_at,
                deleted_by=item.deleted_by,
                delete_reason=item.delete_reason,
            )
        )
    for item in competitors:
        points.append(
            MarketHistoryPointOut(
                point_id=f"competitor:{item.id}",
                point_type="competitor",
                item_id=item.id,
                submission_id=item.submission_id,
                project_id=item.project_id,
                project_name=project_name_map.get(item.project_id or "", None),
                name=item.name,
                city=item.city,
                district=item.district,
                industry=item.business_type,
                target_people=item.target_people,
                address=item.address,
                created_at=item.created_at,
                deleted=bool(item.deleted),
                deleted_at=item.deleted_at,
                deleted_by=item.deleted_by,
                delete_reason=item.delete_reason,
            )
        )
    points.sort(key=lambda row: _safe_time(row.created_at), reverse=True)
    return points


def _apply_common_item_filters(
    query,
    model,
    *,
    city: Optional[str],
    district: Optional[str],
    industry: Optional[str],
    keyword: Optional[str],
):
    if city:
        query = query.filter(model.city == city)
    if district:
        query = query.filter(model.district == district)
    if industry:
        if model is MarketMerchantItem:
            query = query.filter(MarketMerchantItem.category == industry)
        elif model is MarketCompetitorItem:
            query = query.filter(MarketCompetitorItem.business_type == industry)
    if keyword:
        kw = keyword.strip()
        if kw:
            query = query.filter(
                or_(
                    model.name.contains(kw),
                    model.address.contains(kw),
                    model.submission_id.contains(kw),
                    model.project_id.contains(kw),
                )
            )
    return query


@router.post("/merchant/submissions", response_model=MarketSubmissionCreateOut)
def create_merchant_submission(
    payload: MarketSubmissionCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if payload.source_mode == "project" and not payload.project_id:
        raise HTTPException(status_code=400, detail="project模式必须传project_id")
    if not payload.merchant_rows:
        raise HTTPException(status_code=400, detail="merchant_rows不能为空")
    submission, m_count, c_count = create_market_submission(
        db,
        source_mode=payload.source_mode,
        project_id=payload.project_id,
        city=payload.city,
        district=payload.district,
        created_by=user.id,
        merchant_rows=[row.model_dump() for row in payload.merchant_rows],
        competitor_rows=[],
    )
    db.commit()
    log_event(
        db,
        action="MARKET_SUBMISSION_CREATE",
        entity_type="market_submission",
        entity_id=submission.id,
        user_id=user.id,
        metadata={
            "source_mode": payload.source_mode,
            "project_id": payload.project_id,
            "merchant_count": m_count,
            "competitor_count": c_count,
        },
        ip=request.client.host if request.client else None,
    )
    return MarketSubmissionCreateOut(
        submission_id=submission.id,
        source_mode=submission.source_mode,
        project_id=submission.project_id,
        city=submission.city,
        district=submission.district,
        merchant_count=m_count,
        competitor_count=c_count,
        created_at=submission.created_at,
    )


@router.post("/competitor/submissions", response_model=MarketSubmissionCreateOut)
def create_competitor_submission(
    payload: MarketSubmissionCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if payload.source_mode == "project" and not payload.project_id:
        raise HTTPException(status_code=400, detail="project模式必须传project_id")
    if not payload.competitor_rows:
        raise HTTPException(status_code=400, detail="competitor_rows不能为空")
    submission, m_count, c_count = create_market_submission(
        db,
        source_mode=payload.source_mode,
        project_id=payload.project_id,
        city=payload.city,
        district=payload.district,
        created_by=user.id,
        merchant_rows=[],
        competitor_rows=[row.model_dump() for row in payload.competitor_rows],
    )
    db.commit()
    log_event(
        db,
        action="MARKET_SUBMISSION_CREATE",
        entity_type="market_submission",
        entity_id=submission.id,
        user_id=user.id,
        metadata={
            "source_mode": payload.source_mode,
            "project_id": payload.project_id,
            "merchant_count": m_count,
            "competitor_count": c_count,
        },
        ip=request.client.host if request.client else None,
    )
    return MarketSubmissionCreateOut(
        submission_id=submission.id,
        source_mode=submission.source_mode,
        project_id=submission.project_id,
        city=submission.city,
        district=submission.district,
        merchant_count=m_count,
        competitor_count=c_count,
        created_at=submission.created_at,
    )


@router.get("/history", response_model=MarketHistoryResponse)
def get_market_history(
    city: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    type: str = Query(default="all", pattern="^(all|merchant|competitor)$"),
    status: str = Query(default="all", pattern="^(all|active|deleted)$"),
    industry: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    keyword_text = (keyword or "").strip()

    project_name_rows = db.query(ProjectBaseInfo.project_id, ProjectBaseInfo.project_name).all()
    project_name_map = {row.project_id: row.project_name for row in project_name_rows}

    sub_query = db.query(MarketSubmission)
    if city:
        sub_query = sub_query.filter(MarketSubmission.city == city)
    if district:
        sub_query = sub_query.filter(MarketSubmission.district == district)
    if keyword_text:
        sub_query = sub_query.filter(
            or_(
                MarketSubmission.id.contains(keyword_text),
                MarketSubmission.project_id.contains(keyword_text),
            )
        )
    submissions_all = sub_query.order_by(MarketSubmission.created_at.desc()).all()

    merchant_query = db.query(MarketMerchantItem)
    competitor_query = db.query(MarketCompetitorItem)
    if city:
        merchant_query = merchant_query.filter(MarketMerchantItem.city == city)
        competitor_query = competitor_query.filter(MarketCompetitorItem.city == city)
    if district:
        merchant_query = merchant_query.filter(MarketMerchantItem.district == district)
        competitor_query = competitor_query.filter(MarketCompetitorItem.district == district)
    if industry:
        merchant_query = merchant_query.filter(MarketMerchantItem.category == industry)
        competitor_query = competitor_query.filter(MarketCompetitorItem.business_type == industry)
    if keyword_text:
        merchant_query = merchant_query.filter(
            or_(
                MarketMerchantItem.name.contains(keyword_text),
                MarketMerchantItem.address.contains(keyword_text),
                MarketMerchantItem.submission_id.contains(keyword_text),
                MarketMerchantItem.project_id.contains(keyword_text),
            )
        )
        competitor_query = competitor_query.filter(
            or_(
                MarketCompetitorItem.name.contains(keyword_text),
                MarketCompetitorItem.address.contains(keyword_text),
                MarketCompetitorItem.submission_id.contains(keyword_text),
                MarketCompetitorItem.project_id.contains(keyword_text),
            )
        )

    merchants_all = merchant_query.all() if type in {"all", "merchant"} else []
    competitors_all = competitor_query.all() if type in {"all", "competitor"} else []

    points_all = _to_point_rows(merchants_all, competitors_all, project_name_map)
    if status == "active":
        points_filtered = [row for row in points_all if not row.deleted]
        submissions_filtered_raw = [row for row in submissions_all if row.deleted == 0]
    elif status == "deleted":
        points_filtered = [row for row in points_all if row.deleted]
        submissions_filtered_raw = [row for row in submissions_all if row.deleted == 1]
    else:
        points_filtered = points_all
        submissions_filtered_raw = submissions_all

    merchant_counts = (
        db.query(
            MarketMerchantItem.submission_id.label("sid"),
            func.sum(case((MarketMerchantItem.deleted == 0, 1), else_=0)).label("active_count"),
            func.count(MarketMerchantItem.id).label("total_count"),
        )
        .group_by(MarketMerchantItem.submission_id)
        .all()
    )
    competitor_counts = (
        db.query(
            MarketCompetitorItem.submission_id.label("sid"),
            func.sum(case((MarketCompetitorItem.deleted == 0, 1), else_=0)).label("active_count"),
            func.count(MarketCompetitorItem.id).label("total_count"),
        )
        .group_by(MarketCompetitorItem.submission_id)
        .all()
    )
    merchant_map = {row.sid: (int(row.active_count or 0), int(row.total_count or 0)) for row in merchant_counts}
    competitor_map = {row.sid: (int(row.active_count or 0), int(row.total_count or 0)) for row in competitor_counts}

    submissions_filtered = []
    for row in submissions_filtered_raw:
        ma, mt = merchant_map.get(row.id, (0, 0))
        ca, ct = competitor_map.get(row.id, (0, 0))
        submissions_filtered.append(
            MarketHistorySubmissionOut(
                submission_id=row.id,
                source_mode=row.source_mode,
                project_id=row.project_id,
                project_name=project_name_map.get(row.project_id or "", None),
                city=row.city,
                district=row.district,
                created_at=row.created_at,
                merchant_count=ma,
                competitor_count=ca,
                total_count=mt + ct,
                deleted=bool(row.deleted),
                deleted_at=row.deleted_at,
                deleted_by=row.deleted_by,
                delete_reason=row.delete_reason,
            )
        )

    total_points = len(points_filtered)
    start = (page - 1) * page_size
    end = start + page_size

    summary = MarketHistorySummaryOut(
        total_submissions=len(submissions_all),
        active_submissions=sum(1 for row in submissions_all if row.deleted == 0),
        deleted_submissions=sum(1 for row in submissions_all if row.deleted == 1),
        total_points=len(points_all),
        active_points=sum(1 for row in points_all if not row.deleted),
        deleted_points=sum(1 for row in points_all if row.deleted),
    )
    return MarketHistoryResponse(
        summary=summary,
        submissions=submissions_filtered,
        points=points_filtered[start:end],
        page=page,
        page_size=page_size,
        total_points=total_points,
    )


@router.post("/submissions/{submission_id}/delete", response_model=SurveyDeleteActionOut)
def delete_market_submission(
    submission_id: str,
    body: SurveyDeleteIn = Body(default_factory=SurveyDeleteIn),
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    submission = db.query(MarketSubmission).filter(MarketSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="批次不存在")
    if submission.deleted == 1:
        return SurveyDeleteActionOut(target="submission", id=submission_id, deleted=True, affected_count=0, message="已删除")
    now = datetime.utcnow().isoformat(timespec="seconds")
    reason = (body.reason or "").strip() or None
    submission.deleted = 1
    submission.deleted_by = user.id
    submission.deleted_at = now
    submission.delete_reason = reason
    m_affected = (
        db.query(MarketMerchantItem)
        .filter(and_(MarketMerchantItem.submission_id == submission_id, MarketMerchantItem.deleted == 0))
        .update(
            {
                MarketMerchantItem.deleted: 1,
                MarketMerchantItem.deleted_by: user.id,
                MarketMerchantItem.deleted_at: now,
                MarketMerchantItem.delete_reason: reason,
            },
            synchronize_session=False,
        )
    )
    c_affected = (
        db.query(MarketCompetitorItem)
        .filter(and_(MarketCompetitorItem.submission_id == submission_id, MarketCompetitorItem.deleted == 0))
        .update(
            {
                MarketCompetitorItem.deleted: 1,
                MarketCompetitorItem.deleted_by: user.id,
                MarketCompetitorItem.deleted_at: now,
                MarketCompetitorItem.delete_reason: reason,
            },
            synchronize_session=False,
        )
    )
    db.commit()
    affected = int(m_affected or 0) + int(c_affected or 0)
    log_event(
        db,
        action="MARKET_SUBMISSION_DELETE",
        entity_type="market_submission",
        entity_id=submission_id,
        user_id=user.id,
        metadata={"submission_id": submission_id, "affected_count": affected, "reason": reason},
        ip=request.client.host if request and request.client else None,
    )
    return SurveyDeleteActionOut(target="submission", id=submission_id, deleted=True, affected_count=affected, message="删除成功")


@router.post("/submissions/{submission_id}/restore", response_model=SurveyDeleteActionOut)
def restore_market_submission(
    submission_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    submission = db.query(MarketSubmission).filter(MarketSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="批次不存在")
    if submission.deleted == 0:
        return SurveyDeleteActionOut(target="submission", id=submission_id, deleted=False, affected_count=0, message="已是正常状态")
    submission.deleted = 0
    submission.deleted_by = None
    submission.deleted_at = None
    submission.delete_reason = None
    m_affected = (
        db.query(MarketMerchantItem)
        .filter(and_(MarketMerchantItem.submission_id == submission_id, MarketMerchantItem.deleted == 1))
        .update(
            {
                MarketMerchantItem.deleted: 0,
                MarketMerchantItem.deleted_by: None,
                MarketMerchantItem.deleted_at: None,
                MarketMerchantItem.delete_reason: None,
            },
            synchronize_session=False,
        )
    )
    c_affected = (
        db.query(MarketCompetitorItem)
        .filter(and_(MarketCompetitorItem.submission_id == submission_id, MarketCompetitorItem.deleted == 1))
        .update(
            {
                MarketCompetitorItem.deleted: 0,
                MarketCompetitorItem.deleted_by: None,
                MarketCompetitorItem.deleted_at: None,
                MarketCompetitorItem.delete_reason: None,
            },
            synchronize_session=False,
        )
    )
    db.commit()
    affected = int(m_affected or 0) + int(c_affected or 0)
    log_event(
        db,
        action="MARKET_SUBMISSION_RESTORE",
        entity_type="market_submission",
        entity_id=submission_id,
        user_id=user.id,
        metadata={"submission_id": submission_id, "affected_count": affected},
        ip=request.client.host if request.client else None,
    )
    return SurveyDeleteActionOut(target="submission", id=submission_id, deleted=False, affected_count=affected, message="恢复成功")


@router.post("/items/{point_id}/delete", response_model=SurveyDeleteActionOut)
def delete_market_item(
    point_id: str,
    body: SurveyDeleteIn = Body(default_factory=SurveyDeleteIn),
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    if ":" not in point_id:
        raise HTTPException(status_code=400, detail="point_id格式无效")
    point_type, item_id = point_id.split(":", 1)
    now = datetime.utcnow().isoformat(timespec="seconds")
    reason = (body.reason or "").strip() or None
    if point_type == "merchant":
        item = db.query(MarketMerchantItem).filter(MarketMerchantItem.id == item_id).first()
    elif point_type == "competitor":
        item = db.query(MarketCompetitorItem).filter(MarketCompetitorItem.id == item_id).first()
    else:
        raise HTTPException(status_code=400, detail="point_id格式无效")
    if not item:
        raise HTTPException(status_code=404, detail="点位不存在")
    if item.deleted == 1:
        return SurveyDeleteActionOut(target="item", id=point_id, deleted=True, affected_count=0, message="已删除")
    item.deleted = 1
    item.deleted_by = user.id
    item.deleted_at = now
    item.delete_reason = reason
    db.commit()
    log_event(
        db,
        action="MARKET_ITEM_DELETE",
        entity_type="market_item",
        entity_id=point_id,
        user_id=user.id,
        metadata={"point_id": point_id, "submission_id": item.submission_id, "reason": reason},
        ip=request.client.host if request and request.client else None,
    )
    return SurveyDeleteActionOut(target="item", id=point_id, deleted=True, affected_count=1, message="删除成功")


@router.post("/items/{point_id}/restore", response_model=SurveyDeleteActionOut)
def restore_market_item(
    point_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    if ":" not in point_id:
        raise HTTPException(status_code=400, detail="point_id格式无效")
    point_type, item_id = point_id.split(":", 1)
    if point_type == "merchant":
        item = db.query(MarketMerchantItem).filter(MarketMerchantItem.id == item_id).first()
    elif point_type == "competitor":
        item = db.query(MarketCompetitorItem).filter(MarketCompetitorItem.id == item_id).first()
    else:
        raise HTTPException(status_code=400, detail="point_id格式无效")
    if not item:
        raise HTTPException(status_code=404, detail="点位不存在")
    submission = db.query(MarketSubmission).filter(MarketSubmission.id == item.submission_id).first()
    if submission and submission.deleted == 1:
        raise HTTPException(status_code=400, detail="所属批次已删除，请先恢复批次")
    if item.deleted == 0:
        return SurveyDeleteActionOut(target="item", id=point_id, deleted=False, affected_count=0, message="已是正常状态")
    item.deleted = 0
    item.deleted_by = None
    item.deleted_at = None
    item.delete_reason = None
    db.commit()
    log_event(
        db,
        action="MARKET_ITEM_RESTORE",
        entity_type="market_item",
        entity_id=point_id,
        user_id=user.id,
        metadata={"point_id": point_id, "submission_id": item.submission_id},
        ip=request.client.host if request.client else None,
    )
    return SurveyDeleteActionOut(target="item", id=point_id, deleted=False, affected_count=1, message="恢复成功")


@router.post("/items/bulk-delete", response_model=MarketBulkActionOut)
def bulk_delete_market_items(
    body: MarketBulkActionIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    now = datetime.utcnow().isoformat(timespec="seconds")
    reason = (body.reason or "").strip() or None

    merchant_affected = 0
    competitor_affected = 0

    if body.type in {"all", "merchant"}:
        merchant_query = _apply_common_item_filters(
            db.query(MarketMerchantItem),
            MarketMerchantItem,
            city=body.city,
            district=body.district,
            industry=body.industry,
            keyword=body.keyword,
        ).filter(MarketMerchantItem.deleted == 0)
        merchant_affected = int(
            merchant_query.update(
                {
                    MarketMerchantItem.deleted: 1,
                    MarketMerchantItem.deleted_by: user.id,
                    MarketMerchantItem.deleted_at: now,
                    MarketMerchantItem.delete_reason: reason,
                },
                synchronize_session=False,
            )
            or 0
        )

    if body.type in {"all", "competitor"}:
        competitor_query = _apply_common_item_filters(
            db.query(MarketCompetitorItem),
            MarketCompetitorItem,
            city=body.city,
            district=body.district,
            industry=body.industry,
            keyword=body.keyword,
        ).filter(MarketCompetitorItem.deleted == 0)
        competitor_affected = int(
            competitor_query.update(
                {
                    MarketCompetitorItem.deleted: 1,
                    MarketCompetitorItem.deleted_by: user.id,
                    MarketCompetitorItem.deleted_at: now,
                    MarketCompetitorItem.delete_reason: reason,
                },
                synchronize_session=False,
            )
            or 0
        )

    db.commit()
    affected_count = merchant_affected + competitor_affected
    log_event(
        db,
        action="MARKET_ITEM_DELETE",
        entity_type="market_item",
        entity_id="bulk",
        user_id=user.id,
        metadata={
            "action": "bulk_delete",
            "city": body.city,
            "district": body.district,
            "type": body.type,
            "industry": body.industry,
            "keyword": body.keyword,
            "reason": reason,
            "affected_count": affected_count,
            "merchant_affected": merchant_affected,
            "competitor_affected": competitor_affected,
        },
        ip=request.client.host if request.client else None,
    )
    return MarketBulkActionOut(
        action="bulk_delete",
        affected_count=affected_count,
        merchant_affected=merchant_affected,
        competitor_affected=competitor_affected,
        message="批量删除完成" if affected_count else "无匹配点位",
    )


@router.post("/items/bulk-restore", response_model=MarketBulkActionOut)
def bulk_restore_market_items(
    body: MarketBulkActionIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    merchant_affected = 0
    competitor_affected = 0

    active_submission_ids = db.query(MarketSubmission.id).filter(MarketSubmission.deleted == 0).subquery()

    if body.type in {"all", "merchant"}:
        merchant_query = _apply_common_item_filters(
            db.query(MarketMerchantItem),
            MarketMerchantItem,
            city=body.city,
            district=body.district,
            industry=body.industry,
            keyword=body.keyword,
        ).filter(
            and_(
                MarketMerchantItem.deleted == 1,
                MarketMerchantItem.submission_id.in_(active_submission_ids),
            )
        )
        merchant_affected = int(
            merchant_query.update(
                {
                    MarketMerchantItem.deleted: 0,
                    MarketMerchantItem.deleted_by: None,
                    MarketMerchantItem.deleted_at: None,
                    MarketMerchantItem.delete_reason: None,
                },
                synchronize_session=False,
            )
            or 0
        )

    if body.type in {"all", "competitor"}:
        competitor_query = _apply_common_item_filters(
            db.query(MarketCompetitorItem),
            MarketCompetitorItem,
            city=body.city,
            district=body.district,
            industry=body.industry,
            keyword=body.keyword,
        ).filter(
            and_(
                MarketCompetitorItem.deleted == 1,
                MarketCompetitorItem.submission_id.in_(active_submission_ids),
            )
        )
        competitor_affected = int(
            competitor_query.update(
                {
                    MarketCompetitorItem.deleted: 0,
                    MarketCompetitorItem.deleted_by: None,
                    MarketCompetitorItem.deleted_at: None,
                    MarketCompetitorItem.delete_reason: None,
                },
                synchronize_session=False,
            )
            or 0
        )

    db.commit()
    affected_count = merchant_affected + competitor_affected
    log_event(
        db,
        action="MARKET_ITEM_RESTORE",
        entity_type="market_item",
        entity_id="bulk",
        user_id=user.id,
        metadata={
            "action": "bulk_restore",
            "city": body.city,
            "district": body.district,
            "type": body.type,
            "industry": body.industry,
            "keyword": body.keyword,
            "affected_count": affected_count,
            "merchant_affected": merchant_affected,
            "competitor_affected": competitor_affected,
        },
        ip=request.client.host if request.client else None,
    )
    return MarketBulkActionOut(
        action="bulk_restore",
        affected_count=affected_count,
        merchant_affected=merchant_affected,
        competitor_affected=competitor_affected,
        message="批量恢复完成" if affected_count else "无可恢复点位",
    )
