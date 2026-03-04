from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import ProjectBaseInfo, ProjectScreeningResult
from ..schemas import (
    ScreeningHistoryItem,
    ScreeningHistoryKpis,
    ScreeningHistoryPagination,
    ScreeningHistoryResponse,
)
from ..services.screening_config import get_screening_config_payload

router = APIRouter(prefix="/api/screening", tags=["screening"])


@router.get("/config")
def get_screening_config():
    return get_screening_config_payload()


@router.get("/history", response_model=ScreeningHistoryResponse)
def get_screening_history(
    q: str | None = Query(default=None),
    city: str | None = Query(default=None),
    conclusion: str | None = Query(default=None),
    status: str = Query(default="all", pattern="^(all|screened|pending)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    latest_version_subquery = (
        db.query(
            ProjectScreeningResult.project_id.label("project_id"),
            func.max(ProjectScreeningResult.calc_version).label("max_calc_version"),
        )
        .group_by(ProjectScreeningResult.project_id)
        .subquery()
    )

    latest_result_subquery = (
        db.query(
            ProjectScreeningResult.project_id.label("project_id"),
            ProjectScreeningResult.total_score.label("total_score"),
            ProjectScreeningResult.conclusion.label("conclusion"),
            ProjectScreeningResult.calc_version.label("calc_version"),
            ProjectScreeningResult.created_at.label("screening_created_at"),
        )
        .join(
            latest_version_subquery,
            and_(
                ProjectScreeningResult.project_id == latest_version_subquery.c.project_id,
                ProjectScreeningResult.calc_version == latest_version_subquery.c.max_calc_version,
            ),
        )
        .subquery()
    )

    filtered_query = (
        db.query(
            ProjectBaseInfo,
            latest_result_subquery.c.project_id.label("latest_project_id"),
            latest_result_subquery.c.total_score.label("latest_total_score"),
            latest_result_subquery.c.conclusion.label("latest_conclusion"),
            latest_result_subquery.c.calc_version.label("latest_calc_version"),
            latest_result_subquery.c.screening_created_at.label("latest_created_at"),
        )
        .outerjoin(
            latest_result_subquery,
            ProjectBaseInfo.project_id == latest_result_subquery.c.project_id,
        )
    )

    if q:
        keyword = q.strip()
        if keyword:
            filtered_query = filtered_query.filter(ProjectBaseInfo.project_name.contains(keyword))

    if city:
        city_keyword = city.strip()
        if city_keyword:
            filtered_query = filtered_query.filter(ProjectBaseInfo.city == city_keyword)

    if conclusion:
        filtered_query = filtered_query.filter(latest_result_subquery.c.conclusion == conclusion)

    if status == "screened":
        filtered_query = filtered_query.filter(latest_result_subquery.c.project_id.isnot(None))
    elif status == "pending":
        filtered_query = filtered_query.filter(latest_result_subquery.c.project_id.is_(None))

    total_projects, screened_projects, avg_score_raw, high_recommend_count = (
        filtered_query.with_entities(
            func.count(ProjectBaseInfo.project_id),
            func.sum(case((latest_result_subquery.c.project_id.isnot(None), 1), else_=0)),
            func.avg(latest_result_subquery.c.total_score),
            func.sum(
                case(
                    (
                        latest_result_subquery.c.conclusion.in_(["高度推荐", "强烈推荐"]),
                        1,
                    ),
                    else_=0,
                )
            ),
        ).one()
    )

    total_count = int(total_projects or 0)
    screened_count = int(screened_projects or 0)
    avg_score = round(float(avg_score_raw), 1) if avg_score_raw is not None else None
    high_rate = (
        round(float(high_recommend_count or 0) * 100 / screened_count, 1)
        if screened_count > 0
        else None
    )

    ordered_query = filtered_query.order_by(
        func.coalesce(ProjectBaseInfo.updated_at, ProjectBaseInfo.created_at).desc(),
        ProjectBaseInfo.project_id.desc(),
    )
    rows = (
        ordered_query.offset((page - 1) * page_size).limit(page_size).all()
    )

    items: list[ScreeningHistoryItem] = []
    for (
        project,
        latest_project_id,
        latest_total_score,
        latest_conclusion,
        latest_calc_version,
        latest_created_at,
    ) in rows:
        has_screening = latest_project_id is not None
        items.append(
            ScreeningHistoryItem(
                project_id=project.project_id,
                project_name=project.project_name,
                city=project.city,
                district=project.district,
                is_confirmed=project.is_confirmed or 0,
                screening_status="screened" if has_screening else "pending",
                total_score=round(float(latest_total_score), 1)
                if has_screening and latest_total_score is not None
                else None,
                conclusion=latest_conclusion if has_screening else None,
                calc_version=latest_calc_version if has_screening else None,
                screening_created_at=latest_created_at if has_screening else None,
                updated_at=project.updated_at or project.created_at,
            )
        )

    return ScreeningHistoryResponse(
        kpis=ScreeningHistoryKpis(
            total_projects=total_count,
            screened_projects=screened_count,
            avg_score=avg_score,
            high_recommend_rate=high_rate,
        ),
        items=items,
        pagination=ScreeningHistoryPagination(
            page=page,
            page_size=page_size,
            total=total_count,
        ),
    )
