"""地图路由：视口加载 / 行政区聚合 / 周边 / 详情卡片 / 图层。

方言自适应：Postgres 走 geom + GiST 空间索引（&& / ST_DWithin），SQLite 走 lng/lat + 半正矢。
"""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_user
from ..models import CommunicationRecord, FollowupTask, Match, Project, ProjectLocation, User
from ..schemas import MarkerOut
from ..services.sensitivity import can_view_sensitive, mask_point

router = APIRouter(prefix="/api/v1/map", tags=["地图"])


def _is_postgres(db: Session) -> bool:
    return db.get_bind().dialect.name == "postgresql"

LAYERS = [
    {"key": "distribution", "name": "项目分布"},
    {"key": "status", "name": "项目状态"},
    {"key": "type", "name": "项目类型"},
    {"key": "grade", "name": "项目等级"},
    {"key": "leasing_stage", "name": "招商阶段"},
    {"key": "high_match", "name": "高匹配机会"},
]


def _haversine(lng1, lat1, lng2, lat2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@router.get("/projects", response_model=list[MarkerOut])
def viewport(bbox: str = Query(..., description="min_lng,min_lat,max_lng,max_lat"),
             type: str | None = None, status: str | None = None,
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        min_lng, min_lat, max_lng, max_lat = (float(x) for x in bbox.split(","))
    except ValueError:
        raise HTTPException(400, "bbox 格式应为 min_lng,min_lat,max_lng,max_lat")

    allowed = can_view_sensitive(db, user)

    def _marker(pid, code, name, ptype, pstatus, grade, lng, lat, sensitive):
        mlng, mlat, blurred = mask_point(sensitive, allowed, lng, lat)
        return MarkerOut(id=pid, project_code=code, name=name, type=ptype, status=pstatus,
                         grade=grade, lng=mlng, lat=mlat, is_sensitive=sensitive,
                         blurred=blurred)

    if _is_postgres(db):
        # Postgres：走 geom + GiST 空间索引（&& + ST_MakeEnvelope）
        sql = text(
            "SELECT p.id, p.project_code, p.project_name, p.project_type, p.project_status, "
            "       p.grade, p.is_sensitive, l.longitude, l.latitude "
            "FROM projects p JOIN project_locations l ON l.project_id = p.id "
            "WHERE NOT p.is_deleted AND l.geom IS NOT NULL "
            "  AND l.geom && ST_MakeEnvelope(:minlng, :minlat, :maxlng, :maxlat, 4326) "
            "  AND (:type IS NULL OR p.project_type = :type) "
            "  AND (:status IS NULL OR p.project_status = :status)"
        )
        rows = db.execute(sql, {"minlng": min_lng, "minlat": min_lat, "maxlng": max_lng,
                                "maxlat": max_lat, "type": type, "status": status}).all()
        return [_marker(r.id, r.project_code, r.project_name, r.project_type,
                        r.project_status, r.grade, r.longitude, r.latitude, r.is_sensitive)
                for r in rows]

    # SQLite：lng/lat 范围过滤（无 PostGIS）
    q = (db.query(Project).join(ProjectLocation, ProjectLocation.project_id == Project.id)
         .options(joinedload(Project.location))
         .filter(Project.is_deleted.is_(False), ProjectLocation.longitude.isnot(None),
                 ProjectLocation.longitude >= min_lng, ProjectLocation.longitude <= max_lng,
                 ProjectLocation.latitude >= min_lat, ProjectLocation.latitude <= max_lat))
    if type:
        q = q.filter(Project.project_type == type)
    if status:
        q = q.filter(Project.project_status == status)
    return [_marker(p.id, p.project_code, p.project_name, p.project_type, p.project_status,
                    p.grade, p.location.longitude, p.location.latitude, p.is_sensitive)
            for p in q.all()]


@router.get("/aggregate")
def aggregate(level: str = "city", type: str | None = None, status: str | None = None,
              db: Session = Depends(get_db), _=Depends(get_current_user)):
    """行政区聚合（省/市/区数量），低 zoom 用。"""
    col = {"province": ProjectLocation.province, "city": ProjectLocation.city,
           "district": ProjectLocation.district}.get(level)
    if col is None:
        raise HTTPException(400, "level 须为 province/city/district")
    q = (db.query(col, func.count())
         .join(Project, Project.id == ProjectLocation.project_id)
         .filter(Project.is_deleted.is_(False), ProjectLocation.longitude.isnot(None)))
    if type:
        q = q.filter(Project.project_type == type)
    if status:
        q = q.filter(Project.project_status == status)
    rows = q.group_by(col).all()
    return {"level": level, "buckets": [{"name": k, "count": n} for k, n in rows if k]}


@router.get("/projects/{project_id}/nearby")
def nearby(project_id: int, radius: int = 3000, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    origin = db.query(ProjectLocation).filter(
        ProjectLocation.project_id == project_id).first()
    if not origin or origin.longitude is None:
        raise HTTPException(404, "项目无有效坐标")

    allowed = can_view_sensitive(db, user)

    if _is_postgres(db):
        # Postgres：ST_DWithin(geography) 按米算，GiST 加速
        sql = text(
            "SELECT p.id, p.project_name, p.project_type, p.project_status, p.is_sensitive, "
            "       l.longitude, l.latitude, "
            "       ST_Distance(l.geom::geography, o.geom::geography) AS dist_m "
            "FROM projects p JOIN project_locations l ON l.project_id = p.id, "
            "     project_locations o "
            "WHERE o.project_id = :pid AND p.id <> :pid AND NOT p.is_deleted "
            "  AND l.geom IS NOT NULL AND o.geom IS NOT NULL "
            "  AND ST_DWithin(l.geom::geography, o.geom::geography, :radius) "
            "ORDER BY dist_m"
        )
        rows = db.execute(sql, {"pid": project_id, "radius": radius}).all()
        out = []
        for r in rows:
            lng, lat, blurred = mask_point(r.is_sensitive, allowed, r.longitude, r.latitude)
            out.append({"id": r.id, "project_name": r.project_name, "type": r.project_type,
                        "status": r.project_status, "lng": lng, "lat": lat,
                        "dist_m": round(r.dist_m), "blurred": blurred})
        return out

    # SQLite：粗 bbox 预筛 + 半正矢精算
    deg = radius / 111000.0 + 0.01
    rows = (db.query(Project, ProjectLocation)
            .join(ProjectLocation, ProjectLocation.project_id == Project.id)
            .filter(Project.id != project_id, Project.is_deleted.is_(False),
                    ProjectLocation.longitude.isnot(None),
                    ProjectLocation.longitude.between(origin.longitude - deg, origin.longitude + deg),
                    ProjectLocation.latitude.between(origin.latitude - deg, origin.latitude + deg))
            .all())
    out = []
    for p, loc in rows:
        d = _haversine(origin.longitude, origin.latitude, loc.longitude, loc.latitude)
        if d <= radius:
            lng, lat, blurred = mask_point(p.is_sensitive, allowed, loc.longitude, loc.latitude)
            out.append({"id": p.id, "project_name": p.project_name,
                        "type": p.project_type, "status": p.project_status,
                        "lng": lng, "lat": lat, "dist_m": round(d), "blurred": blurred})
    out.sort(key=lambda x: x["dist_m"])
    return out


@router.get("/projects/{project_id}/card")
def card(project_id: int, db: Session = Depends(get_db),
         user: User = Depends(get_current_user)):
    p = db.query(Project).options(joinedload(Project.location)).filter(
        Project.id == project_id, Project.is_deleted.is_(False)).first()
    if not p:
        raise HTTPException(404, "项目不存在")
    masked = p.is_sensitive and not can_view_sensitive(db, user)
    matched = db.query(Match).filter(Match.project_id == project_id).count()
    priority = db.query(Match).filter(Match.project_id == project_id,
                                      Match.match_grade == "优先推进").count()
    last_comm = (db.query(CommunicationRecord)
                 .filter(CommunicationRecord.project_id == project_id)
                 .order_by(CommunicationRecord.comm_date.desc()).first())
    next_task = (db.query(FollowupTask)
                 .filter(FollowupTask.project_id == project_id,
                         FollowupTask.status.in_(["待办", "进行中"]))
                 .order_by(FollowupTask.plan_date).first())
    loc = p.location
    return {
        "id": p.id, "project_code": p.project_code, "name": p.project_name,
        "type": p.project_type, "status": p.project_status, "grade": p.grade,
        "city": loc.city if loc else None,
        "address": ("敏感项目 · 地址已脱敏" if masked else (loc.address if loc else None)),
        "open_date": p.open_date, "business_area_m2": p.business_area_m2,
        "leasable_area_m2": p.leasable_area_m2, "target_formats": p.target_formats,
        "core_customers": p.core_customers, "operator": p.operator,
        "leasing_stage": p.leasing_stage, "cooperation_will": p.cooperation_will,
        "matched_brands": matched, "priority_brands": priority,
        "last_communication": last_comm.summary if last_comm else None,
        "next_followup": next_task.title if next_task else None,
        "is_sensitive": p.is_sensitive,
    }


@router.get("/layers")
def layers(_=Depends(get_current_user)):
    return {"layers": LAYERS}
