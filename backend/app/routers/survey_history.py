from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles
from ..models import (
    ProjectBaseInfo,
    SurveyCompetitorItem,
    SurveyMerchantItem,
    SurveySubmission,
    UserRole,
)
from ..schemas import (
    SurveyDeleteActionOut,
    SurveyDeleteIn,
    SurveyHistoryPointOut,
    SurveyHistoryResponse,
    SurveyHistorySubmissionOut,
    SurveyHistorySummaryOut,
)
from ..services.audit import log_event

router = APIRouter(prefix="/api/survey/history", tags=["survey-history"])


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _parse_time(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _parse_point_id(point_id: str) -> tuple[str, str]:
    if ":" not in point_id:
        raise HTTPException(status_code=400, detail="point_id格式无效")
    point_type, item_id = point_id.split(":", 1)
    point_type = point_type.strip()
    item_id = item_id.strip()
    if point_type not in {"merchant", "competitor"} or not item_id:
        raise HTTPException(status_code=400, detail="point_id格式无效")
    return point_type, item_id


@router.get("", response_model=SurveyHistoryResponse)
def get_survey_history(
    city: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    type: str = Query(default="all", pattern="^(all|merchant|competitor)$"),
    status: str = Query(default="all", pattern="^(all|active|deleted)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    keyword_text = (keyword or "").strip()

    merchant_counts_rows = (
        db.query(
            SurveyMerchantItem.submission_id.label("submission_id"),
            func.sum(case((SurveyMerchantItem.deleted == 0, 1), else_=0)).label("active_count"),
            func.count(SurveyMerchantItem.id).label("total_count"),
        )
        .group_by(SurveyMerchantItem.submission_id)
        .all()
    )
    competitor_counts_rows = (
        db.query(
            SurveyCompetitorItem.submission_id.label("submission_id"),
            func.sum(case((SurveyCompetitorItem.deleted == 0, 1), else_=0)).label("active_count"),
            func.count(SurveyCompetitorItem.id).label("total_count"),
        )
        .group_by(SurveyCompetitorItem.submission_id)
        .all()
    )
    merchant_counts = {
        row.submission_id: (int(row.active_count or 0), int(row.total_count or 0))
        for row in merchant_counts_rows
    }
    competitor_counts = {
        row.submission_id: (int(row.active_count or 0), int(row.total_count or 0))
        for row in competitor_counts_rows
    }

    submission_query = (
        db.query(SurveySubmission, ProjectBaseInfo.project_name)
        .outerjoin(ProjectBaseInfo, SurveySubmission.project_id == ProjectBaseInfo.project_id)
    )
    if city:
        submission_query = submission_query.filter(SurveySubmission.city == city)
    if district:
        submission_query = submission_query.filter(SurveySubmission.district == district)
    if keyword_text:
        submission_query = submission_query.filter(
            or_(
                SurveySubmission.id.contains(keyword_text),
                SurveySubmission.project_id.contains(keyword_text),
                ProjectBaseInfo.project_name.contains(keyword_text),
            )
        )

    raw_submissions = submission_query.all()
    submissions_all: list[SurveyHistorySubmissionOut] = []
    for submission, project_name in raw_submissions:
        merchant_active, merchant_total = merchant_counts.get(submission.id, (0, 0))
        competitor_active, competitor_total = competitor_counts.get(submission.id, (0, 0))
        submissions_all.append(
            SurveyHistorySubmissionOut(
                submission_id=submission.id,
                project_id=submission.project_id,
                project_name=project_name,
                city=submission.city,
                district=submission.district,
                version=int(submission.version or 0),
                merchant_count=merchant_active,
                competitor_count=competitor_active,
                total_count=merchant_total + competitor_total,
                created_at=submission.created_at,
                deleted=bool(submission.deleted),
                deleted_at=submission.deleted_at,
                deleted_by=submission.deleted_by,
                delete_reason=submission.delete_reason,
            )
        )
    submissions_all.sort(key=lambda row: _parse_time(row.created_at), reverse=True)

    merchant_query = (
        db.query(SurveyMerchantItem, ProjectBaseInfo.project_name)
        .outerjoin(ProjectBaseInfo, SurveyMerchantItem.project_id == ProjectBaseInfo.project_id)
    )
    if city:
        merchant_query = merchant_query.filter(SurveyMerchantItem.city == city)
    if district:
        merchant_query = merchant_query.filter(SurveyMerchantItem.district == district)
    if keyword_text:
        merchant_query = merchant_query.filter(
            or_(
                SurveyMerchantItem.name.contains(keyword_text),
                SurveyMerchantItem.address.contains(keyword_text),
                ProjectBaseInfo.project_name.contains(keyword_text),
                SurveyMerchantItem.submission_id.contains(keyword_text),
            )
        )

    competitor_query = (
        db.query(SurveyCompetitorItem, ProjectBaseInfo.project_name)
        .outerjoin(ProjectBaseInfo, SurveyCompetitorItem.project_id == ProjectBaseInfo.project_id)
    )
    if city:
        competitor_query = competitor_query.filter(SurveyCompetitorItem.city == city)
    if district:
        competitor_query = competitor_query.filter(SurveyCompetitorItem.district == district)
    if keyword_text:
        competitor_query = competitor_query.filter(
            or_(
                SurveyCompetitorItem.name.contains(keyword_text),
                SurveyCompetitorItem.address.contains(keyword_text),
                ProjectBaseInfo.project_name.contains(keyword_text),
                SurveyCompetitorItem.submission_id.contains(keyword_text),
            )
        )

    points_all: list[SurveyHistoryPointOut] = []
    if type in {"all", "merchant"}:
        for item, project_name in merchant_query.all():
            points_all.append(
                SurveyHistoryPointOut(
                    point_id=f"merchant:{item.id}",
                    point_type="merchant",
                    item_id=item.id,
                    submission_id=item.submission_id,
                    project_id=item.project_id,
                    project_name=project_name,
                    name=item.name,
                    city=item.city,
                    district=item.district,
                    address=item.address,
                    created_at=item.created_at,
                    deleted=bool(item.deleted),
                    deleted_at=item.deleted_at,
                    deleted_by=item.deleted_by,
                    delete_reason=item.delete_reason,
                )
            )
    if type in {"all", "competitor"}:
        for item, project_name in competitor_query.all():
            points_all.append(
                SurveyHistoryPointOut(
                    point_id=f"competitor:{item.id}",
                    point_type="competitor",
                    item_id=item.id,
                    submission_id=item.submission_id,
                    project_id=item.project_id,
                    project_name=project_name,
                    name=item.name,
                    city=item.city,
                    district=item.district,
                    address=item.address,
                    created_at=item.created_at,
                    deleted=bool(item.deleted),
                    deleted_at=item.deleted_at,
                    deleted_by=item.deleted_by,
                    delete_reason=item.delete_reason,
                )
            )
    points_all.sort(key=lambda row: _parse_time(row.created_at), reverse=True)

    if status == "active":
        submissions_filtered = [row for row in submissions_all if not row.deleted]
        points_filtered = [row for row in points_all if not row.deleted]
    elif status == "deleted":
        submissions_filtered = [row for row in submissions_all if row.deleted]
        points_filtered = [row for row in points_all if row.deleted]
    else:
        submissions_filtered = submissions_all
        points_filtered = points_all

    total_points = len(points_filtered)
    start = (page - 1) * page_size
    end = start + page_size
    points_page = points_filtered[start:end]

    summary = SurveyHistorySummaryOut(
        total_submissions=len(submissions_all),
        active_submissions=sum(1 for row in submissions_all if not row.deleted),
        deleted_submissions=sum(1 for row in submissions_all if row.deleted),
        total_points=len(points_all),
        active_points=sum(1 for row in points_all if not row.deleted),
        deleted_points=sum(1 for row in points_all if row.deleted),
    )
    return SurveyHistoryResponse(
        summary=summary,
        submissions=submissions_filtered,
        points=points_page,
        page=page,
        page_size=page_size,
        total_points=total_points,
    )


@router.post("/submissions/{submission_id}/delete", response_model=SurveyDeleteActionOut)
def delete_submission(
    submission_id: str,
    body: SurveyDeleteIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    submission = db.query(SurveySubmission).filter(SurveySubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="调研批次不存在")
    if submission.deleted:
        return SurveyDeleteActionOut(
            target="submission",
            id=submission_id,
            deleted=True,
            affected_count=0,
            message="该批次已删除",
        )

    now = _now_iso()
    reason = (body.reason or "").strip() or None
    submission.deleted = 1
    submission.deleted_by = user.id
    submission.deleted_at = now
    submission.delete_reason = reason

    merchant_count = (
        db.query(SurveyMerchantItem)
        .filter(SurveyMerchantItem.submission_id == submission_id)
        .filter(SurveyMerchantItem.deleted == 0)
        .update(
            {
                SurveyMerchantItem.deleted: 1,
                SurveyMerchantItem.deleted_by: user.id,
                SurveyMerchantItem.deleted_at: now,
                SurveyMerchantItem.delete_reason: reason,
            },
            synchronize_session=False,
        )
    )
    competitor_count = (
        db.query(SurveyCompetitorItem)
        .filter(SurveyCompetitorItem.submission_id == submission_id)
        .filter(SurveyCompetitorItem.deleted == 0)
        .update(
            {
                SurveyCompetitorItem.deleted: 1,
                SurveyCompetitorItem.deleted_by: user.id,
                SurveyCompetitorItem.deleted_at: now,
                SurveyCompetitorItem.delete_reason: reason,
            },
            synchronize_session=False,
        )
    )
    db.commit()

    affected_count = int(merchant_count or 0) + int(competitor_count or 0)
    log_event(
        db,
        action="SURVEY_SUBMISSION_DELETE",
        entity_type="survey_submission",
        entity_id=submission_id,
        user_id=user.id,
        metadata={
            "submission_id": submission_id,
            "project_id": submission.project_id,
            "affected_count": affected_count,
            "reason": reason,
        },
        ip=request.client.host if request.client else None,
    )
    return SurveyDeleteActionOut(
        target="submission",
        id=submission_id,
        deleted=True,
        affected_count=affected_count,
        message="调研批次已删除",
    )


@router.post("/submissions/{submission_id}/restore", response_model=SurveyDeleteActionOut)
def restore_submission(
    submission_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    submission = db.query(SurveySubmission).filter(SurveySubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="调研批次不存在")
    if not submission.deleted:
        return SurveyDeleteActionOut(
            target="submission",
            id=submission_id,
            deleted=False,
            affected_count=0,
            message="该批次当前为正常状态",
        )

    submission.deleted = 0
    submission.deleted_by = None
    submission.deleted_at = None
    submission.delete_reason = None

    merchant_count = (
        db.query(SurveyMerchantItem)
        .filter(SurveyMerchantItem.submission_id == submission_id)
        .filter(SurveyMerchantItem.deleted == 1)
        .update(
            {
                SurveyMerchantItem.deleted: 0,
                SurveyMerchantItem.deleted_by: None,
                SurveyMerchantItem.deleted_at: None,
                SurveyMerchantItem.delete_reason: None,
            },
            synchronize_session=False,
        )
    )
    competitor_count = (
        db.query(SurveyCompetitorItem)
        .filter(SurveyCompetitorItem.submission_id == submission_id)
        .filter(SurveyCompetitorItem.deleted == 1)
        .update(
            {
                SurveyCompetitorItem.deleted: 0,
                SurveyCompetitorItem.deleted_by: None,
                SurveyCompetitorItem.deleted_at: None,
                SurveyCompetitorItem.delete_reason: None,
            },
            synchronize_session=False,
        )
    )
    db.commit()

    affected_count = int(merchant_count or 0) + int(competitor_count or 0)
    log_event(
        db,
        action="SURVEY_SUBMISSION_RESTORE",
        entity_type="survey_submission",
        entity_id=submission_id,
        user_id=user.id,
        metadata={
            "submission_id": submission_id,
            "project_id": submission.project_id,
            "affected_count": affected_count,
        },
        ip=request.client.host if request.client else None,
    )
    return SurveyDeleteActionOut(
        target="submission",
        id=submission_id,
        deleted=False,
        affected_count=affected_count,
        message="调研批次已恢复",
    )


@router.post("/items/{point_id}/delete", response_model=SurveyDeleteActionOut)
def delete_point_item(
    point_id: str,
    body: SurveyDeleteIn,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    point_type, item_id = _parse_point_id(point_id)
    reason = (body.reason or "").strip() or None
    now = _now_iso()

    if point_type == "merchant":
        item = db.query(SurveyMerchantItem).filter(SurveyMerchantItem.id == item_id).first()
    else:
        item = db.query(SurveyCompetitorItem).filter(SurveyCompetitorItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="点位不存在")
    if item.deleted:
        return SurveyDeleteActionOut(
            target="item",
            id=point_id,
            deleted=True,
            affected_count=0,
            message="该点位已删除",
        )

    if point_type == "merchant":
        item.deleted = 1
        item.deleted_by = user.id
        item.deleted_at = now
        item.delete_reason = reason
    else:
        item.deleted = 1
        item.deleted_by = user.id
        item.deleted_at = now
        item.delete_reason = reason

    db.commit()

    log_event(
        db,
        action="SURVEY_POINT_DELETE",
        entity_type="survey_point",
        entity_id=point_id,
        user_id=user.id,
        metadata={
            "point_id": point_id,
            "submission_id": item.submission_id,
            "project_id": item.project_id,
            "reason": reason,
        },
        ip=request.client.host if request.client else None,
    )
    return SurveyDeleteActionOut(
        target="item",
        id=point_id,
        deleted=True,
        affected_count=1,
        message="点位已删除",
    )


@router.post("/items/{point_id}/restore", response_model=SurveyDeleteActionOut)
def restore_point_item(
    point_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    point_type, item_id = _parse_point_id(point_id)
    if point_type == "merchant":
        item = db.query(SurveyMerchantItem).filter(SurveyMerchantItem.id == item_id).first()
    else:
        item = db.query(SurveyCompetitorItem).filter(SurveyCompetitorItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="点位不存在")

    submission = db.query(SurveySubmission).filter(SurveySubmission.id == item.submission_id).first()
    if submission and submission.deleted:
        raise HTTPException(status_code=400, detail="该点位所属批次已删除，请先恢复批次")
    if not item.deleted:
        return SurveyDeleteActionOut(
            target="item",
            id=point_id,
            deleted=False,
            affected_count=0,
            message="该点位当前为正常状态",
        )

    item.deleted = 0
    item.deleted_by = None
    item.deleted_at = None
    item.delete_reason = None
    db.commit()

    log_event(
        db,
        action="SURVEY_POINT_RESTORE",
        entity_type="survey_point",
        entity_id=point_id,
        user_id=user.id,
        metadata={
            "point_id": point_id,
            "submission_id": item.submission_id,
            "project_id": item.project_id,
        },
        ip=request.client.host if request.client else None,
    )
    return SurveyDeleteActionOut(
        target="item",
        id=point_id,
        deleted=False,
        affected_count=1,
        message="点位已恢复",
    )

