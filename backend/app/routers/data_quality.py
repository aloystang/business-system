from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import MarketCompetitorItem, MarketMerchantItem
from ..schemas import DataQualityDistrictOut, DataQualityOverviewOut
from ..services.audit import log_event

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])


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
    required = [item.name, item.category, item.area_m2, item.rent_unit_price, item.daily_flow, item.address, item.city, item.district]
    return sum(1 for value in required if value is not None and str(value).strip() != "") / len(required)


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
    return sum(1 for value in required if value is not None and str(value).strip() != "") / len(required)


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


def _calc_quality(merchants: list[MarketMerchantItem], competitors: list[MarketCompetitorItem]) -> DataQualityOverviewOut:
    total = len(merchants) + len(competitors)
    if total == 0:
        return DataQualityOverviewOut(
            completeness_score=0.0,
            geo_accuracy_score=0.0,
            dedupe_health_score=100.0,
            freshness_score=0.0,
            overall_score=0.0,
            sample_count=0,
        )

    completeness_values = [_completeness_for_merchant(item) for item in merchants] + [_completeness_for_competitor(item) for item in competitors]
    geo_ok = sum(
        1
        for item in merchants + competitors
        if item.geocode_status == "success" and item.longitude is not None and item.latitude is not None
    )
    freshness_values = [_freshness_score(item.created_at) for item in merchants + competitors]
    signatures = [item.signature for item in merchants] + [item.signature for item in competitors]
    dedupe_ratio = len(set(signatures)) / len(signatures) if signatures else 1.0

    completeness = (sum(completeness_values) / len(completeness_values)) * 100
    geo_accuracy = (geo_ok / total) * 100
    dedupe = dedupe_ratio * 100
    freshness = (sum(freshness_values) / len(freshness_values)) * 100
    overall = completeness * 0.35 + geo_accuracy * 0.25 + dedupe * 0.25 + freshness * 0.15
    return DataQualityOverviewOut(
        completeness_score=round(completeness, 1),
        geo_accuracy_score=round(geo_accuracy, 1),
        dedupe_health_score=round(dedupe, 1),
        freshness_score=round(freshness, 1),
        overall_score=round(overall, 1),
        sample_count=total,
    )


@router.get("/overview", response_model=DataQualityOverviewOut)
def get_data_quality_overview(
    city: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    merchants_query = db.query(MarketMerchantItem).filter(MarketMerchantItem.deleted == 0)
    competitors_query = db.query(MarketCompetitorItem).filter(MarketCompetitorItem.deleted == 0)
    if city:
        merchants_query = merchants_query.filter(MarketMerchantItem.city == city)
        competitors_query = competitors_query.filter(MarketCompetitorItem.city == city)
    merchants = merchants_query.all()
    competitors = competitors_query.all()
    result = _calc_quality(merchants, competitors)
    log_event(
        db,
        action="DATA_QUALITY_SCORE",
        entity_type="data_quality",
        entity_id="overview",
        user_id=user.id,
        metadata={"city": city, "sample_count": result.sample_count, "overall_score": result.overall_score},
        ip=None,
    )
    return result


@router.get("/by-district", response_model=list[DataQualityDistrictOut])
def get_data_quality_by_district(
    city: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    merchants_query = db.query(MarketMerchantItem).filter(MarketMerchantItem.deleted == 0)
    competitors_query = db.query(MarketCompetitorItem).filter(MarketCompetitorItem.deleted == 0)
    if city:
        merchants_query = merchants_query.filter(MarketMerchantItem.city == city)
        competitors_query = competitors_query.filter(MarketCompetitorItem.city == city)
    merchants = merchants_query.all()
    competitors = competitors_query.all()

    districts = sorted(set([item.district for item in merchants if item.district] + [item.district for item in competitors if item.district]))
    rows: list[DataQualityDistrictOut] = []
    for district in districts:
        district_merchants = [item for item in merchants if item.district == district]
        district_competitors = [item for item in competitors if item.district == district]
        quality = _calc_quality(district_merchants, district_competitors)
        rows.append(
            DataQualityDistrictOut(
                district=district,
                completeness_score=quality.completeness_score,
                geo_accuracy_score=quality.geo_accuracy_score,
                dedupe_health_score=quality.dedupe_health_score,
                freshness_score=quality.freshness_score,
                overall_score=quality.overall_score,
                sample_count=quality.sample_count,
            )
        )
    return rows
