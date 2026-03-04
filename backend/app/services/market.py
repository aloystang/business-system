from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import (
    MarketCompetitorItem,
    MarketMerchantItem,
    MarketSubmission,
)
from .geocode_amap import MAX_GEOCODE_PER_SUBMISSION, geocode_address


def normalize_signature(*parts: Any) -> str:
    def _norm(value: Any) -> str:
        return (
            str(value or "")
            .strip()
            .lower()
            .replace(" ", "")
            .replace("，", "")
            .replace(",", "")
            .replace("。", "")
            .replace(".", "")
            .replace(";", "")
            .replace("；", "")
            .replace("-", "")
            .replace("_", "")
            .replace("/", "")
        )

    return "|".join(_norm(part) for part in parts)


def build_item_signature(*, name: Any, city: Any, district: Any, address: Any) -> str:
    return normalize_signature(name, city, district, address)


def ensure_unique_signature(db: Session, *, point_type: str, signature: str) -> None:
    if point_type == "merchant":
        existed = (
            db.query(MarketMerchantItem.id)
            .filter(MarketMerchantItem.signature == signature)
            .filter(MarketMerchantItem.deleted == 0)
            .first()
        )
    else:
        existed = (
            db.query(MarketCompetitorItem.id)
            .filter(MarketCompetitorItem.signature == signature)
            .filter(MarketCompetitorItem.deleted == 0)
            .first()
        )
    if existed:
        raise HTTPException(status_code=409, detail=f"{point_type}存在重复记录，请检查名称和地址")


def _next_submission_version(db: Session, city: str, district: str, project_id: Optional[str]) -> int:
    query = db.query(MarketSubmission).filter(MarketSubmission.city == city, MarketSubmission.district == district)
    if project_id:
        query = query.filter(MarketSubmission.project_id == project_id)
    else:
        query = query.filter(MarketSubmission.project_id.is_(None))
    latest = query.order_by(MarketSubmission.version.desc()).first()
    return int(latest.version if latest else 0) + 1


def create_market_submission(
    db: Session,
    *,
    source_mode: str,
    city: str,
    district: str,
    created_by: int,
    project_id: Optional[str] = None,
    merchant_rows: Optional[Iterable[dict[str, Any]]] = None,
    competitor_rows: Optional[Iterable[dict[str, Any]]] = None,
    enforce_uniqueness: bool = True,
) -> tuple[MarketSubmission, int, int]:
    merchant_rows = list(merchant_rows or [])
    competitor_rows = list(competitor_rows or [])
    total_count = len(merchant_rows) + len(competitor_rows)
    if total_count == 0:
        raise HTTPException(status_code=400, detail="至少提交1条数据")
    if total_count > MAX_GEOCODE_PER_SUBMISSION:
        raise HTTPException(status_code=400, detail=f"单次提交最多 {MAX_GEOCODE_PER_SUBMISSION} 条")

    version = _next_submission_version(db, city, district, project_id)
    now = datetime.utcnow().isoformat(timespec="seconds")
    pid = project_id or "standalone"
    sid = f"{pid}-market-v{version}-{now.replace(':', '').replace('-', '').replace('T', '')}"
    submission = MarketSubmission(
        id=sid,
        version=version,
        source_mode=source_mode,
        project_id=project_id,
        city=city,
        district=district,
        created_by=created_by,
        created_at=now,
        deleted=0,
    )
    db.add(submission)
    db.flush()

    merchant_count = 0
    competitor_count = 0

    for idx, row in enumerate(merchant_rows, start=1):
        signature = build_item_signature(
            name=row.get("name"),
            city=row.get("city") or city,
            district=row.get("district") or district,
            address=row.get("address"),
        )
        if enforce_uniqueness:
            ensure_unique_signature(db, point_type="merchant", signature=signature)
        longitude = row.get("longitude")
        latitude = row.get("latitude")
        has_manual = longitude is not None and latitude is not None
        geocode_status = "success" if has_manual else "pending"
        geocode_message = "manual_pick" if has_manual else None
        if not has_manual:
            full_address = f"{row.get('city') or city}{row.get('district') or district}{row.get('address') or ''}"
            geo = geocode_address(db, full_address)
            longitude = geo.get("longitude")
            latitude = geo.get("latitude")
            geocode_status = geo.get("status") or "failed"
            geocode_message = str(geo.get("message") or "")[:255] or None

        item = MarketMerchantItem(
            id=f"{sid}-m-{idx}",
            submission_id=sid,
            project_id=project_id,
            name=str(row.get("name") or "").strip(),
            category=str(row.get("category") or "").strip(),
            area_m2=float(row.get("area_m2")),
            rent_unit_price=float(row.get("rent_unit_price")),
            daily_flow=int(row.get("daily_flow")),
            address=str(row.get("address") or "").strip(),
            city=str(row.get("city") or city).strip(),
            district=str(row.get("district") or district).strip(),
            note=str(row.get("note") or "").strip() or None,
            longitude=longitude,
            latitude=latitude,
            geocode_status=geocode_status,
            geocode_message=geocode_message,
            geocoded_at=now,
            signature=signature,
            created_at=now,
            deleted=0,
        )
        db.add(item)
        merchant_count += 1

    for idx, row in enumerate(competitor_rows, start=1):
        signature = build_item_signature(
            name=row.get("name"),
            city=row.get("city") or city,
            district=row.get("district") or district,
            address=row.get("address"),
        )
        if enforce_uniqueness:
            ensure_unique_signature(db, point_type="competitor", signature=signature)
        longitude = row.get("longitude")
        latitude = row.get("latitude")
        has_manual = longitude is not None and latitude is not None
        geocode_status = "success" if has_manual else "pending"
        geocode_message = "manual_pick" if has_manual else None
        if not has_manual:
            full_address = f"{row.get('city') or city}{row.get('district') or district}{row.get('address') or ''}"
            geo = geocode_address(db, full_address)
            longitude = geo.get("longitude")
            latitude = geo.get("latitude")
            geocode_status = geo.get("status") or "failed"
            geocode_message = str(geo.get("message") or "")[:255] or None

        item = MarketCompetitorItem(
            id=f"{sid}-c-{idx}",
            submission_id=sid,
            project_id=project_id,
            name=str(row.get("name") or "").strip(),
            scale_m2=float(row.get("scale_m2")),
            avg_rent_unit_price=float(row.get("avg_rent_unit_price")),
            vacancy_rate=float(row.get("vacancy_rate")),
            business_type=str(row.get("business_type") or "").strip(),
            distance_km=float(row.get("distance_km")),
            target_people=str(row.get("target_people") or "").strip(),
            address=str(row.get("address") or "").strip(),
            city=str(row.get("city") or city).strip(),
            district=str(row.get("district") or district).strip(),
            longitude=longitude,
            latitude=latitude,
            geocode_status=geocode_status,
            geocode_message=geocode_message,
            geocoded_at=now,
            signature=signature,
            created_at=now,
            deleted=0,
        )
        db.add(item)
        competitor_count += 1
    db.flush()
    return submission, merchant_count, competitor_count
