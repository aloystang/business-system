from __future__ import annotations

from datetime import datetime
from statistics import median
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import (
    MarketCompetitorItem,
    MarketMerchantItem,
    ProjectBaseInfo,
    SurveyCompetitorItem,
    SurveyMerchantItem,
)
from ..schemas import (
    OverviewMapKpisOut,
    OverviewMapPointDetailOut,
    OverviewMapPointOut,
    OverviewMapPointsResponse,
)
from ..services.audit import log_event

router = APIRouter(prefix="/api/overview/map", tags=["overview-map"])


def _safe_parse_datetime(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _normalize_date_start(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) == 10:
        return f"{text}T00:00:00"
    return text


def _normalize_date_end(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) == 10:
        return f"{text}T23:59:59"
    return text


def _parse_bbox(value: Optional[str]) -> Optional[tuple[float, float, float, float]]:
    if not value:
        return None
    parts = [segment.strip() for segment in value.split(",")]
    if len(parts) != 4:
        raise HTTPException(status_code=400, detail="bbox格式应为minLng,minLat,maxLng,maxLat")
    try:
        min_lng, min_lat, max_lng, max_lat = [float(part) for part in parts]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"bbox包含非法数字: {exc}") from exc
    if min_lng >= max_lng or min_lat >= max_lat:
        raise HTTPException(status_code=400, detail="bbox范围无效")
    return (min_lng, min_lat, max_lng, max_lat)


def _city_aliases(city: Optional[str]) -> list[str]:
    if not city:
        return []
    raw = city.strip()
    if not raw:
        return []
    aliases = {raw}
    if raw.endswith("市"):
        aliases.add(raw[:-1])
    else:
        aliases.add(f"{raw}市")
    return [item for item in aliases if item]


def _point_signature(point_type: str, name: Optional[str], city: Optional[str], district: Optional[str], address: Optional[str]) -> str:
    def _norm(value: Optional[str]) -> str:
        return (
            str(value or "")
            .strip()
            .lower()
            .replace(" ", "")
            .replace("，", "")
            .replace(",", "")
            .replace("。", "")
            .replace(".", "")
        )

    return f"{point_type}|{_norm(name)}|{_norm(city)}|{_norm(district)}|{_norm(address)}"


def _merchant_query(
    db: Session,
    *,
    city: Optional[str],
    district: Optional[str],
    keyword: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    bbox: Optional[tuple[float, float, float, float]],
):
    query = (
        db.query(MarketMerchantItem, ProjectBaseInfo.project_name)
        .outerjoin(ProjectBaseInfo, MarketMerchantItem.project_id == ProjectBaseInfo.project_id)
        .filter(MarketMerchantItem.geocode_status == "success")
        .filter(MarketMerchantItem.longitude.isnot(None))
        .filter(MarketMerchantItem.latitude.isnot(None))
        .filter(MarketMerchantItem.deleted == 0)
    )
    if city:
        query = query.filter(MarketMerchantItem.city.in_(_city_aliases(city)))
    if district:
        query = query.filter(MarketMerchantItem.district == district)
    if keyword:
        query = query.filter(
            or_(
                MarketMerchantItem.name.contains(keyword),
                MarketMerchantItem.address.contains(keyword),
                ProjectBaseInfo.project_name.contains(keyword),
            )
        )
    if date_from:
        query = query.filter(MarketMerchantItem.created_at >= date_from)
    if date_to:
        query = query.filter(MarketMerchantItem.created_at <= date_to)
    if bbox:
        min_lng, min_lat, max_lng, max_lat = bbox
        query = query.filter(
            and_(
                MarketMerchantItem.longitude >= min_lng,
                MarketMerchantItem.longitude <= max_lng,
                MarketMerchantItem.latitude >= min_lat,
                MarketMerchantItem.latitude <= max_lat,
            )
        )
    return query


def _survey_merchant_query(
    db: Session,
    *,
    city: Optional[str],
    district: Optional[str],
    keyword: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    bbox: Optional[tuple[float, float, float, float]],
):
    query = (
        db.query(SurveyMerchantItem, ProjectBaseInfo.project_name)
        .outerjoin(ProjectBaseInfo, SurveyMerchantItem.project_id == ProjectBaseInfo.project_id)
        .filter(SurveyMerchantItem.geocode_status == "success")
        .filter(SurveyMerchantItem.longitude.isnot(None))
        .filter(SurveyMerchantItem.latitude.isnot(None))
        .filter(SurveyMerchantItem.deleted == 0)
    )
    if city:
        query = query.filter(SurveyMerchantItem.city.in_(_city_aliases(city)))
    if district:
        query = query.filter(SurveyMerchantItem.district == district)
    if keyword:
        query = query.filter(
            or_(
                SurveyMerchantItem.name.contains(keyword),
                SurveyMerchantItem.address.contains(keyword),
                ProjectBaseInfo.project_name.contains(keyword),
            )
        )
    if date_from:
        query = query.filter(SurveyMerchantItem.created_at >= date_from)
    if date_to:
        query = query.filter(SurveyMerchantItem.created_at <= date_to)
    if bbox:
        min_lng, min_lat, max_lng, max_lat = bbox
        query = query.filter(
            and_(
                SurveyMerchantItem.longitude >= min_lng,
                SurveyMerchantItem.longitude <= max_lng,
                SurveyMerchantItem.latitude >= min_lat,
                SurveyMerchantItem.latitude <= max_lat,
            )
        )
    return query


def _competitor_query(
    db: Session,
    *,
    city: Optional[str],
    district: Optional[str],
    keyword: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    bbox: Optional[tuple[float, float, float, float]],
):
    query = (
        db.query(MarketCompetitorItem, ProjectBaseInfo.project_name)
        .outerjoin(ProjectBaseInfo, MarketCompetitorItem.project_id == ProjectBaseInfo.project_id)
        .filter(MarketCompetitorItem.geocode_status == "success")
        .filter(MarketCompetitorItem.longitude.isnot(None))
        .filter(MarketCompetitorItem.latitude.isnot(None))
        .filter(MarketCompetitorItem.deleted == 0)
    )
    if city:
        query = query.filter(MarketCompetitorItem.city.in_(_city_aliases(city)))
    if district:
        query = query.filter(MarketCompetitorItem.district == district)
    if keyword:
        query = query.filter(
            or_(
                MarketCompetitorItem.name.contains(keyword),
                MarketCompetitorItem.address.contains(keyword),
                ProjectBaseInfo.project_name.contains(keyword),
            )
        )
    if date_from:
        query = query.filter(MarketCompetitorItem.created_at >= date_from)
    if date_to:
        query = query.filter(MarketCompetitorItem.created_at <= date_to)
    if bbox:
        min_lng, min_lat, max_lng, max_lat = bbox
        query = query.filter(
            and_(
                MarketCompetitorItem.longitude >= min_lng,
                MarketCompetitorItem.longitude <= max_lng,
                MarketCompetitorItem.latitude >= min_lat,
                MarketCompetitorItem.latitude <= max_lat,
            )
        )
    return query


def _survey_competitor_query(
    db: Session,
    *,
    city: Optional[str],
    district: Optional[str],
    keyword: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    bbox: Optional[tuple[float, float, float, float]],
):
    query = (
        db.query(SurveyCompetitorItem, ProjectBaseInfo.project_name)
        .outerjoin(ProjectBaseInfo, SurveyCompetitorItem.project_id == ProjectBaseInfo.project_id)
        .filter(SurveyCompetitorItem.geocode_status == "success")
        .filter(SurveyCompetitorItem.longitude.isnot(None))
        .filter(SurveyCompetitorItem.latitude.isnot(None))
        .filter(SurveyCompetitorItem.deleted == 0)
    )
    if city:
        query = query.filter(SurveyCompetitorItem.city.in_(_city_aliases(city)))
    if district:
        query = query.filter(SurveyCompetitorItem.district == district)
    if keyword:
        query = query.filter(
            or_(
                SurveyCompetitorItem.name.contains(keyword),
                SurveyCompetitorItem.address.contains(keyword),
                ProjectBaseInfo.project_name.contains(keyword),
            )
        )
    if date_from:
        query = query.filter(SurveyCompetitorItem.created_at >= date_from)
    if date_to:
        query = query.filter(SurveyCompetitorItem.created_at <= date_to)
    if bbox:
        min_lng, min_lat, max_lng, max_lat = bbox
        query = query.filter(
            and_(
                SurveyCompetitorItem.longitude >= min_lng,
                SurveyCompetitorItem.longitude <= max_lng,
                SurveyCompetitorItem.latitude >= min_lat,
                SurveyCompetitorItem.latitude <= max_lat,
            )
        )
    return query


@router.get("/kpis", response_model=OverviewMapKpisOut)
def get_map_kpis(
    request: Request,
    city: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    normalized_from = _normalize_date_start(date_from)
    normalized_to = _normalize_date_end(date_to)

    market_merchants = _merchant_query(
        db,
        city=city,
        district=district,
        keyword=None,
        date_from=normalized_from,
        date_to=normalized_to,
        bbox=None,
    ).all()
    survey_merchants = _survey_merchant_query(
        db,
        city=city,
        district=district,
        keyword=None,
        date_from=normalized_from,
        date_to=normalized_to,
        bbox=None,
    ).all()
    market_competitors = _competitor_query(
        db,
        city=city,
        district=district,
        keyword=None,
        date_from=normalized_from,
        date_to=normalized_to,
        bbox=None,
    ).all()
    survey_competitors = _survey_competitor_query(
        db,
        city=city,
        district=district,
        keyword=None,
        date_from=normalized_from,
        date_to=normalized_to,
        bbox=None,
    ).all()

    merchant_dict: dict[str, tuple[Any, Optional[str]]] = {}
    for item, project_name in market_merchants:
        key = _point_signature("merchant", item.name, item.city, item.district, item.address)
        merchant_dict[key] = (item, project_name)
    for item, project_name in survey_merchants:
        key = _point_signature("merchant", item.name, item.city, item.district, item.address)
        merchant_dict.setdefault(key, (item, project_name))

    competitor_dict: dict[str, tuple[Any, Optional[str]]] = {}
    for item, project_name in market_competitors:
        key = _point_signature("competitor", item.name, item.city, item.district, item.address)
        competitor_dict[key] = (item, project_name)
    for item, project_name in survey_competitors:
        key = _point_signature("competitor", item.name, item.city, item.district, item.address)
        competitor_dict.setdefault(key, (item, project_name))

    merchant_items = [row[0] for row in merchant_dict.values()]
    competitor_items = [row[0] for row in competitor_dict.values()]
    rent_values = [item.rent_unit_price for item in merchant_items if item.rent_unit_price is not None]
    vacancy_values = [item.vacancy_rate for item in competitor_items if item.vacancy_rate is not None]
    flow_values = [item.daily_flow for item in merchant_items if item.daily_flow is not None]
    district_values = {item.district for item in merchant_items + competitor_items if item.district}

    payload = OverviewMapKpisOut(
        total_points=len(merchant_items) + len(competitor_items),
        merchant_count=len(merchant_items),
        competitor_count=len(competitor_items),
        covered_district_count=len(district_values),
        avg_rent_unit_price=round(sum(rent_values) / len(rent_values), 2) if rent_values else None,
        median_rent_unit_price=round(float(median(rent_values)), 2) if rent_values else None,
        avg_vacancy_rate=round(sum(vacancy_values) / len(vacancy_values), 2) if vacancy_values else None,
        avg_daily_flow=round(sum(flow_values) / len(flow_values), 2) if flow_values else None,
    )

    log_event(
        db,
        action="MAP_QUERY",
        entity_type="overview_map",
        entity_id="kpis",
        user_id=user.id,
        metadata={
            "city": city,
            "district": district,
            "date_from": date_from,
            "date_to": date_to,
            "total_points": payload.total_points,
        },
        ip=request.client.host if request.client else None,
    )
    return payload


@router.get("/points", response_model=OverviewMapPointsResponse)
def get_map_points(
    request: Request,
    city: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    type: str = Query(default="all", pattern="^(all|merchant|competitor)$"),
    keyword: Optional[str] = Query(default=None),
    bbox: Optional[str] = Query(default=None),
    zoom: Optional[int] = Query(default=None, ge=1, le=22),
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    normalized_from = _normalize_date_start(date_from)
    normalized_to = _normalize_date_end(date_to)
    bbox_values = _parse_bbox(bbox)
    search_keyword = keyword.strip() if keyword else None

    points: list[OverviewMapPointOut] = []
    merchant_total = 0
    competitor_total = 0

    if type in {"all", "merchant"}:
        market_merchant_rows = _merchant_query(
            db,
            city=city,
            district=district,
            keyword=search_keyword,
            date_from=normalized_from,
            date_to=normalized_to,
            bbox=bbox_values,
        ).all()
        survey_merchant_rows = _survey_merchant_query(
            db,
            city=city,
            district=district,
            keyword=search_keyword,
            date_from=normalized_from,
            date_to=normalized_to,
            bbox=bbox_values,
        ).all()
        merchant_dict: dict[str, tuple[Any, Optional[str]]] = {}
        for item, project_name in market_merchant_rows:
            key = _point_signature("merchant", item.name, item.city, item.district, item.address)
            merchant_dict[key] = (item, project_name)
        for item, project_name in survey_merchant_rows:
            key = _point_signature("merchant", item.name, item.city, item.district, item.address)
            merchant_dict.setdefault(key, (item, project_name))

        for item, project_name in merchant_dict.values():
            merchant_total += 1
            points.append(
                OverviewMapPointOut(
                    point_id=f"merchant:{item.id}",
                    point_type="merchant",
                    item_id=item.id,
                    project_id=item.project_id,
                    project_name=project_name,
                    name=item.name,
                    city=item.city,
                    district=item.district,
                    address=item.address,
                    longitude=float(item.longitude),
                    latitude=float(item.latitude),
                    rent_unit_price=item.rent_unit_price,
                    vacancy_rate=None,
                    daily_flow=item.daily_flow,
                    created_at=item.created_at,
                )
            )

    if type in {"all", "competitor"}:
        market_competitor_rows = _competitor_query(
            db,
            city=city,
            district=district,
            keyword=search_keyword,
            date_from=normalized_from,
            date_to=normalized_to,
            bbox=bbox_values,
        ).all()
        survey_competitor_rows = _survey_competitor_query(
            db,
            city=city,
            district=district,
            keyword=search_keyword,
            date_from=normalized_from,
            date_to=normalized_to,
            bbox=bbox_values,
        ).all()
        competitor_dict: dict[str, tuple[Any, Optional[str]]] = {}
        for item, project_name in market_competitor_rows:
            key = _point_signature("competitor", item.name, item.city, item.district, item.address)
            competitor_dict[key] = (item, project_name)
        for item, project_name in survey_competitor_rows:
            key = _point_signature("competitor", item.name, item.city, item.district, item.address)
            competitor_dict.setdefault(key, (item, project_name))

        for item, project_name in competitor_dict.values():
            competitor_total += 1
            points.append(
                OverviewMapPointOut(
                    point_id=f"competitor:{item.id}",
                    point_type="competitor",
                    item_id=item.id,
                    project_id=item.project_id,
                    project_name=project_name,
                    name=item.name,
                    city=item.city,
                    district=item.district,
                    address=item.address,
                    longitude=float(item.longitude),
                    latitude=float(item.latitude),
                    rent_unit_price=item.avg_rent_unit_price,
                    vacancy_rate=item.vacancy_rate,
                    daily_flow=None,
                    created_at=item.created_at,
                )
            )

    points.sort(key=lambda row: _safe_parse_datetime(row.created_at), reverse=True)
    total = len(points)
    start = (page - 1) * page_size
    end = start + page_size

    payload = OverviewMapPointsResponse(
        items=points[start:end],
        total=total,
        page=page,
        page_size=page_size,
        aggregates={
            "merchant_count": merchant_total,
            "competitor_count": competitor_total,
            "zoom": zoom or 0,
        },
    )

    log_event(
        db,
        action="MAP_QUERY",
        entity_type="overview_map",
        entity_id="points",
        user_id=user.id,
        metadata={
            "city": city,
            "district": district,
            "type": type,
            "keyword": search_keyword,
            "date_from": date_from,
            "date_to": date_to,
            "bbox": bbox,
            "zoom": zoom,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        ip=request.client.host if request.client else None,
    )
    return payload


@router.get("/point/{point_id}", response_model=OverviewMapPointDetailOut)
def get_map_point_detail(
    point_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if ":" not in point_id:
        raise HTTPException(status_code=400, detail="point_id格式无效")

    point_type, item_id = point_id.split(":", 1)
    point_type = point_type.strip()
    item_id = item_id.strip()

    if point_type == "merchant":
        row = (
            db.query(MarketMerchantItem, ProjectBaseInfo.project_name)
            .outerjoin(ProjectBaseInfo, MarketMerchantItem.project_id == ProjectBaseInfo.project_id)
            .filter(MarketMerchantItem.id == item_id)
            .filter(MarketMerchantItem.deleted == 0)
            .first()
        )
        if not row:
            row = (
                db.query(SurveyMerchantItem, ProjectBaseInfo.project_name)
                .outerjoin(ProjectBaseInfo, SurveyMerchantItem.project_id == ProjectBaseInfo.project_id)
                .filter(SurveyMerchantItem.id == item_id)
                .filter(SurveyMerchantItem.deleted == 0)
                .first()
            )
        if not row:
            raise HTTPException(status_code=404, detail="点位不存在")
        item, project_name = row
        payload = {
            "name": item.name,
            "category": item.category,
            "area_m2": item.area_m2,
            "rent_unit_price": item.rent_unit_price,
            "daily_flow": item.daily_flow,
            "address": item.address,
            "city": item.city,
            "district": item.district,
            "note": item.note,
            "longitude": item.longitude,
            "latitude": item.latitude,
            "created_at": item.created_at,
        }
        project_id = item.project_id
    elif point_type == "competitor":
        row = (
            db.query(MarketCompetitorItem, ProjectBaseInfo.project_name)
            .outerjoin(ProjectBaseInfo, MarketCompetitorItem.project_id == ProjectBaseInfo.project_id)
            .filter(MarketCompetitorItem.id == item_id)
            .filter(MarketCompetitorItem.deleted == 0)
            .first()
        )
        if not row:
            row = (
                db.query(SurveyCompetitorItem, ProjectBaseInfo.project_name)
                .outerjoin(ProjectBaseInfo, SurveyCompetitorItem.project_id == ProjectBaseInfo.project_id)
                .filter(SurveyCompetitorItem.id == item_id)
                .filter(SurveyCompetitorItem.deleted == 0)
                .first()
            )
        if not row:
            raise HTTPException(status_code=404, detail="点位不存在")
        item, project_name = row
        payload = {
            "name": item.name,
            "scale_m2": item.scale_m2,
            "avg_rent_unit_price": item.avg_rent_unit_price,
            "vacancy_rate": item.vacancy_rate,
            "business_type": item.business_type,
            "distance_km": item.distance_km,
            "target_people": item.target_people,
            "address": item.address,
            "city": item.city,
            "district": item.district,
            "longitude": item.longitude,
            "latitude": item.latitude,
            "created_at": item.created_at,
        }
        project_id = item.project_id
    else:
        raise HTTPException(status_code=400, detail="point_id类型无效")

    response = OverviewMapPointDetailOut(
        point_id=f"{point_type}:{item_id}",
        point_type=point_type,
        project_id=project_id,
        project_name=project_name,
        payload=payload,
    )

    log_event(
        db,
        action="MAP_POINT_VIEW",
        entity_type="overview_map_point",
        entity_id=response.point_id,
        user_id=user.id,
        metadata={
            "point_id": response.point_id,
            "point_type": point_type,
            "project_id": project_id,
        },
        ip=request.client.host if request.client else None,
    )

    return response
