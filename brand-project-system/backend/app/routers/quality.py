"""数据质量中心路由。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Brand, Project, ProjectLocation

router = APIRouter(prefix="/api/v1/data-quality", tags=["数据质量"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), _=Depends(get_current_user)):
    projects = db.query(Project).filter(Project.is_deleted.is_(False)).count()
    geocode_failed = db.query(ProjectLocation).filter(
        ProjectLocation.geocoding_status.in_(["定位失败", "待定位"])).count()
    missing_grade_proj = db.query(Project).filter(
        Project.is_deleted.is_(False), Project.grade.is_(None)).count()
    missing_grade_brand = db.query(Brand).filter(
        Brand.is_deleted.is_(False), Brand.grade.is_(None)).count()
    # 名称重复（潜在重复主数据）
    dup_brand = db.query(Brand.brand_name).filter(Brand.is_deleted.is_(False)).group_by(
        Brand.brand_name).having(func.count() > 1).count()
    return {
        "projects_total": projects,
        "geocode_failed": geocode_failed,
        "projects_missing_grade": missing_grade_proj,
        "brands_missing_grade": missing_grade_brand,
        "duplicate_brand_names": dup_brand,
    }


@router.get("/geocode-failed")
def geocode_failed(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = (
        db.query(Project.id, Project.project_code, Project.project_name,
                 ProjectLocation.address, ProjectLocation.geocoding_status)
        .join(ProjectLocation, ProjectLocation.project_id == Project.id)
        .filter(ProjectLocation.geocoding_status.in_(["定位失败", "待定位"]),
                Project.is_deleted.is_(False))
        .all()
    )
    return [{"project_id": r[0], "project_code": r[1], "project_name": r[2],
             "address": r[3], "geocoding_status": r[4]} for r in rows]
