from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import (
    CalcAssetOwner,
    CalcInternalOperation,
    CalcMerchant,
    MarketCompetitorItem,
    MarketMerchantItem,
    ProjectBaseInfo,
    SurveyCompetitorItem,
    SurveyMerchantItem,
    SurveySubmission,
    ProjectScreeningDetail,
    ProjectScreeningResult,
)
from ..services.audit import log_event
from ..services.calc_engine import compute_dual_calculation
from ..services.geocode_amap import MAX_GEOCODE_PER_SUBMISSION, geocode_address
from ..services.market import create_market_submission
from ..services.screening_config import (
    INDICATOR_BY_KEY,
    INDICATOR_CONFIG,
    SCREENING_CONFIG_VERSION,
    conclusion_from_total,
    evaluate_indicator_auto,
    level_to_score,
)
from ..services.snapshot import create_project_snapshot
from ..schemas import (
    CalcAssetOwnerOut,
    CalcAssetOwnerRequest,
    CalcAutoRequest,
    CalcAutoResponse,
    CalcSummaryOut,
    CalcInternalOperationOut,
    CalcInternalOperationRequest,
    CalcYearlyOut,
    CalcMerchantOut,
    CalcMerchantRequest,
    ProjectBaseInfoCreate,
    ProjectBaseInfoOut,
    ProjectBaseInfoUpdate,
    SurveyCompetitionRowOut,
    SurveyMerchantRowOut,
    ScreeningIndicatorOut,
    ProjectScreeningResultOut,
    ScreeningCalcRequest,
)

router = APIRouter(prefix="/api/projects", tags=["project-base"])

ALLOWED_ASSET_DISTRIBUTION = {"集中", "分散", "混合"}
ALLOWED_OWNERSHIP = {"甲方", "第三方", "混合"}
ALLOWED_COMPETITION = {"强", "中", "弱"}


def _generate_project_id(db: Session) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    base = f"PRJ-{stamp}"
    suffix = 1
    project_id = base
    while db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == project_id).first():
        suffix += 1
        project_id = f"{base}-{suffix}"
    return project_id


def _round2(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _validate_enums(asset_distribution: str, ownership_structure: str, competition_level: str) -> None:
    if asset_distribution not in ALLOWED_ASSET_DISTRIBUTION:
        raise HTTPException(status_code=400, detail="asset_distribution invalid")
    if ownership_structure not in ALLOWED_OWNERSHIP:
        raise HTTPException(status_code=400, detail="ownership_structure invalid")
    if competition_level not in ALLOWED_COMPETITION:
        raise HTTPException(status_code=400, detail="competition_level invalid")


def _validate_ranges(vacancy_rate: Optional[float]) -> None:
    if vacancy_rate is None:
        return
    if vacancy_rate < 0 or vacancy_rate > 100:
        raise HTTPException(status_code=400, detail="vacancy_rate must be 0-100")


def _require_confirmed(db: Session, project_id: str) -> ProjectBaseInfo:
    entity = db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == project_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Project not found")
    if entity.is_confirmed != 1:
        raise HTTPException(status_code=400, detail="Project not confirmed")
    return entity


def _normalize_occupancy(value: float) -> float:
    if value < 0:
        raise HTTPException(status_code=400, detail="target_occupancy must be >= 0")
    if value > 1:
        return value / 100
    return value


def _next_calc_version(db: Session, model, project_id: str) -> int:
    latest_version = (
        db.query(func.max(model.calc_version)).filter(model.project_id == project_id).scalar()
    )
    return (latest_version or 0) + 1


def _next_auto_calc_version(db: Session, project_id: str) -> int:
    latest_asset = (
        db.query(func.max(CalcAssetOwner.calc_version))
        .filter(CalcAssetOwner.project_id == project_id)
        .scalar()
    ) or 0
    latest_internal = (
        db.query(func.max(CalcInternalOperation.calc_version))
        .filter(CalcInternalOperation.project_id == project_id)
        .scalar()
    ) or 0
    return max(int(latest_asset), int(latest_internal)) + 1


def _json_load(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _normalize_yearly_rows(value: Any) -> list[CalcYearlyOut]:
    if not isinstance(value, list):
        return []
    rows: list[CalcYearlyOut] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        rows.append(
            CalcYearlyOut(
                year_index=int(row.get("year_index", 0) or 0),
                year_label=str(row.get("year_label", "")),
                revenue=row.get("revenue"),
                cost=row.get("cost"),
                gross_profit=row.get("gross_profit"),
                gross_margin=row.get("gross_margin"),
                tax=row.get("tax"),
            )
        )
    return rows


def _to_asset_out(entity: CalcAssetOwner) -> CalcAssetOwnerOut:
    details = _json_load(entity.details_json)
    params = _json_load(entity.params_json)
    summary_payload = details.get("summary") if isinstance(details, dict) else None
    yearly_payload = details.get("yearly") if isinstance(details, dict) else None
    summary = CalcSummaryOut(**summary_payload) if isinstance(summary_payload, dict) else None
    yearly = _normalize_yearly_rows(yearly_payload)
    if summary is None:
        gross_profit = (
            (entity.annual_rent_income or 0) - (entity.invest_cost or 0)
            if entity.annual_rent_income is not None and entity.invest_cost is not None
            else None
        )
        summary = CalcSummaryOut(
            total_revenue=_round2(entity.annual_rent_income),
            total_cost=_round2(entity.invest_cost),
            gross_profit=_round2(gross_profit),
            gross_margin=_round2(entity.roi),
            tax_after_profit=_round2(gross_profit),
        )
    return CalcAssetOwnerOut(
        id=entity.id,
        project_id=entity.project_id,
        target_rent=entity.target_rent or 0,
        target_occupancy=entity.target_occupancy or 0,
        annual_rent_income=entity.annual_rent_income,
        invest_cost=entity.invest_cost or 0,
        roi=entity.roi,
        payback_year=entity.payback_year,
        calc_version=entity.calc_version,
        created_at=entity.created_at,
        summary=summary,
        yearly=yearly,
        params_used=params if isinstance(params, dict) else None,
        source="auto_from_collection" if entity.calc_basis in {"owner_v1", "huarun_v1"} else "manual_input",
        calc_basis=entity.calc_basis,
    )


def _to_internal_out(entity: CalcInternalOperation) -> CalcInternalOperationOut:
    details = _json_load(entity.details_json)
    params = _json_load(entity.params_json)
    summary_payload = details.get("summary") if isinstance(details, dict) else None
    yearly_payload = details.get("yearly") if isinstance(details, dict) else None
    summary = CalcSummaryOut(**summary_payload) if isinstance(summary_payload, dict) else None
    yearly = _normalize_yearly_rows(yearly_payload)
    if summary is None:
        summary = CalcSummaryOut(
            total_revenue=_round2(entity.total_income),
            total_cost=_round2(entity.total_cost),
            gross_profit=_round2(entity.total_profit),
            gross_margin=_round2(entity.profit_margin),
            tax_after_profit=_round2(entity.total_profit),
        )
    return CalcInternalOperationOut(
        id=entity.id,
        project_id=entity.project_id,
        service_fee_rate=entity.service_fee_rate or 0,
        manage_fee_rate=entity.manage_fee_rate or 0,
        annual_rent_for_calc=entity.annual_rent_for_calc,
        service_income=entity.service_income,
        manage_income=entity.manage_income,
        staff_cost=entity.staff_cost or 0,
        other_cost=entity.other_cost or 0,
        total_income=entity.total_income,
        total_cost=entity.total_cost,
        total_profit=entity.total_profit,
        profit_margin=entity.profit_margin,
        calc_version=entity.calc_version,
        created_at=entity.created_at,
        summary=summary,
        yearly=yearly,
        params_used=params if isinstance(params, dict) else None,
        source="auto_from_collection" if entity.calc_basis in {"owner_v1", "huarun_v1"} else "manual_input",
        calc_basis=entity.calc_basis,
    )


def _run_auto_calc_and_persist(
    db: Session,
    project: ProjectBaseInfo,
    overrides: Optional[dict[str, Any]] = None,
) -> tuple[int, CalcAssetOwner, CalcInternalOperation]:
    calculation = compute_dual_calculation(project, overrides=overrides)
    calc_version = _next_auto_calc_version(db, project.project_id)
    now = datetime.utcnow().isoformat(timespec="seconds")

    external_summary = calculation["external"]["summary"]
    external_yearly = calculation["external"]["yearly"]
    params_used = calculation["external"]["params_used"]
    invest_cost = float(params_used.get("invest_cost_default_wan", 0) or 0)
    annual_income = float(external_yearly[0]["revenue"]) if external_yearly else 0.0
    roi = None if invest_cost == 0 else annual_income / invest_cost
    payback_year = None if annual_income == 0 else invest_cost / annual_income

    asset = CalcAssetOwner(
        id=f"{project.project_id}-asset-v{calc_version}",
        project_id=project.project_id,
        target_rent=float(params_used.get("rent_base") or 0),
        target_occupancy=float((params_used.get("occupancy_curve") or [0])[0] or 0),
        annual_rent_income=annual_income,
        invest_cost=invest_cost,
        roi=roi,
        payback_year=payback_year,
        details_json=json.dumps(
            {
                "summary": external_summary,
                "yearly": external_yearly,
            },
            ensure_ascii=False,
        ),
        params_json=json.dumps(params_used, ensure_ascii=False),
        calc_basis=calculation["external"]["calc_basis"],
        calc_version=calc_version,
        created_at=now,
    )
    db.add(asset)

    internal_summary = calculation["internal"]["summary"]
    internal_yearly = calculation["internal"]["yearly"]
    year1 = internal_yearly[0] if internal_yearly else {"revenue": 0, "cost": 0}
    staff_cost = 0.0
    other_cost = 0.0
    raw_internal = calculation.get("internal_raw", {})
    raw_yearly = raw_internal.get("yearly", []) if isinstance(raw_internal, dict) else []
    if raw_yearly and isinstance(raw_yearly[0], dict):
        staff_cost = float(raw_yearly[0].get("_hr_cost", 0) or 0)
        other_cost = float(raw_yearly[0].get("_admin_cost", 0) or 0)

    internal = CalcInternalOperation(
        id=f"{project.project_id}-internal-v{calc_version}",
        project_id=project.project_id,
        service_fee_rate=float(params_used.get("operation_commission_rate") or 0),
        manage_fee_rate=0.0,
        annual_rent_for_calc=float(year1.get("revenue") or 0),
        service_income=float(year1.get("revenue") or 0),
        manage_income=float(year1.get("cost") or 0),
        staff_cost=staff_cost,
        other_cost=other_cost,
        total_income=float(internal_summary.get("total_revenue") or 0),
        total_cost=float(internal_summary.get("total_cost") or 0),
        total_profit=float(internal_summary.get("gross_profit") or 0),
        profit_margin=internal_summary.get("gross_margin"),
        details_json=json.dumps(
            {
                "summary": internal_summary,
                "yearly": internal_yearly,
            },
            ensure_ascii=False,
        ),
        params_json=json.dumps(params_used, ensure_ascii=False),
        calc_basis=calculation["internal"]["calc_basis"],
        calc_version=calc_version,
        created_at=now,
    )
    db.add(internal)
    db.flush()
    return calc_version, asset, internal


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _to_opt_text(value: Any) -> Optional[str]:
    text = _clean_text(value)
    return text or None


def _supplement_project_from_market(db: Session, project: ProjectBaseInfo) -> dict[str, Any]:
    if not project.city or not project.district:
        return {}
    now = datetime.utcnow()
    date_floor = now.replace(year=now.year - 1).isoformat(timespec="seconds")
    merchants = (
        db.query(MarketMerchantItem)
        .filter(MarketMerchantItem.deleted == 0)
        .filter(MarketMerchantItem.city == project.city, MarketMerchantItem.district == project.district)
        .filter(MarketMerchantItem.created_at >= date_floor)
        .all()
    )
    competitors = (
        db.query(MarketCompetitorItem)
        .filter(MarketCompetitorItem.deleted == 0)
        .filter(MarketCompetitorItem.city == project.city, MarketCompetitorItem.district == project.district)
        .filter(MarketCompetitorItem.created_at >= date_floor)
        .all()
    )
    result: dict[str, Any] = {}
    if merchants:
        avg_rent = sum(float(item.rent_unit_price or 0) for item in merchants) / len(merchants)
        result["rent_min"] = _round2(avg_rent)
        result["rent_max"] = _round2(avg_rent)
    if competitors:
        count = len(competitors)
        if count <= 0:
            result["competition_market_level"] = "3km内无5万㎡以上同业定位商业项目"
        elif count == 1:
            result["competition_market_level"] = "3km内有1个8万㎡同业定位商业项目"
        elif count == 2:
            result["competition_market_level"] = "3km内有2个8万㎡同业定位商业项目"
        else:
            result["competition_market_level"] = "3km内超过2个8万㎡同业定位商业项目"
    return result


def _next_submission_version(db: Session, project_id: str) -> int:
    latest = (
        db.query(func.max(SurveySubmission.version))
        .filter(SurveySubmission.project_id == project_id)
        .scalar()
    )
    return int(latest or 0) + 1


def _has_any_value(row: dict[str, Any]) -> bool:
    for value in row.values():
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip():
                return True
            continue
        return True
    return False


def _validate_required(row: dict[str, Any], required_fields: list[str], row_name: str, index: int) -> None:
    missing = [field for field in required_fields if not _clean_text(row.get(field))]
    if missing:
        fields_text = "、".join(missing)
        raise HTTPException(
            status_code=400,
            detail=f"{row_name}第{index + 1}行缺少必填字段：{fields_text}",
        )


def _normalize_survey_rows(
    merchant_rows: Optional[list[dict[str, Any]]],
    competition_rows: Optional[list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    merchants = merchant_rows or []
    competitors = competition_rows or []

    normalized_merchants: list[dict[str, Any]] = []
    for idx, row in enumerate(merchants):
        raw = dict(row)
        if not _has_any_value(raw):
            continue
        _validate_required(
            raw,
            [
                "name",
                "category",
                "area_m2",
                "rent_unit_price",
                "daily_flow",
                "address",
                "city",
                "district",
            ],
            "商家调研",
            idx,
        )
        longitude_raw = raw.get("longitude")
        latitude_raw = raw.get("latitude")
        has_longitude = _clean_text(longitude_raw) != ""
        has_latitude = _clean_text(latitude_raw) != ""
        if has_longitude != has_latitude:
            raise HTTPException(
                status_code=400,
                detail=f"商家调研第{idx + 1}行经纬度需同时填写",
            )
        longitude = float(longitude_raw) if has_longitude else None
        latitude = float(latitude_raw) if has_latitude else None

        normalized_merchants.append(
            {
                "name": _clean_text(raw.get("name")),
                "category": _clean_text(raw.get("category")),
                "area_m2": float(raw.get("area_m2")),
                "rent_unit_price": float(raw.get("rent_unit_price")),
                "daily_flow": int(float(raw.get("daily_flow"))),
                "address": _clean_text(raw.get("address")),
                "city": _clean_text(raw.get("city")),
                "district": _clean_text(raw.get("district")),
                "note": _to_opt_text(raw.get("note")),
                "longitude": longitude,
                "latitude": latitude,
            }
        )

    normalized_competitors: list[dict[str, Any]] = []
    for idx, row in enumerate(competitors):
        raw = dict(row)
        if not _has_any_value(raw):
            continue
        _validate_required(
            raw,
            [
                "name",
                "scale_m2",
                "avg_rent_unit_price",
                "vacancy_rate",
                "business_type",
                "distance_km",
                "target_people",
                "address",
                "city",
                "district",
            ],
            "竞争关系",
            idx,
        )
        longitude_raw = raw.get("longitude")
        latitude_raw = raw.get("latitude")
        has_longitude = _clean_text(longitude_raw) != ""
        has_latitude = _clean_text(latitude_raw) != ""
        if has_longitude != has_latitude:
            raise HTTPException(
                status_code=400,
                detail=f"竞争关系第{idx + 1}行经纬度需同时填写",
            )
        longitude = float(longitude_raw) if has_longitude else None
        latitude = float(latitude_raw) if has_latitude else None

        normalized_competitors.append(
            {
                "name": _clean_text(raw.get("name")),
                "scale_m2": float(raw.get("scale_m2")),
                "avg_rent_unit_price": float(raw.get("avg_rent_unit_price")),
                "vacancy_rate": float(raw.get("vacancy_rate")),
                "business_type": _clean_text(raw.get("business_type")),
                "distance_km": float(raw.get("distance_km")),
                "target_people": _clean_text(raw.get("target_people")),
                "address": _clean_text(raw.get("address")),
                "city": _clean_text(raw.get("city")),
                "district": _clean_text(raw.get("district")),
                "longitude": longitude,
                "latitude": latitude,
            }
        )

    return normalized_merchants, normalized_competitors


def _save_survey_submission(
    db: Session,
    *,
    project: ProjectBaseInfo,
    created_by: int,
    merchant_rows: Optional[list[dict[str, Any]]],
    competition_rows: Optional[list[dict[str, Any]]],
    ip: Optional[str],
) -> Optional[dict[str, Any]]:
    merchants, competitors = _normalize_survey_rows(merchant_rows, competition_rows)
    if not merchants and not competitors:
        return None
    if len(merchants) + len(competitors) > MAX_GEOCODE_PER_SUBMISSION:
        raise HTTPException(
            status_code=400,
            detail=f"单次提交最多 {MAX_GEOCODE_PER_SUBMISSION} 条调研点位",
        )

    version = _next_submission_version(db, project.project_id)
    now = datetime.utcnow().isoformat(timespec="seconds")
    submission_id = f"{project.project_id}-survey-v{version}"
    submission = SurveySubmission(
        id=submission_id,
        project_id=project.project_id,
        version=version,
        city=project.city,
        district=project.district,
        created_by=created_by,
        created_at=now,
    )
    db.add(submission)
    db.flush()

    merchant_items: list[SurveyMerchantItem] = []
    for idx, row in enumerate(merchants):
        has_manual_point = row.get("longitude") is not None and row.get("latitude") is not None
        item = SurveyMerchantItem(
            id=f"{submission_id}-m-{idx + 1}",
            submission_id=submission_id,
            project_id=project.project_id,
            name=row["name"],
            category=row["category"],
            area_m2=row["area_m2"],
            rent_unit_price=row["rent_unit_price"],
            daily_flow=row["daily_flow"],
            address=row["address"],
            city=row["city"],
            district=row["district"],
            note=row["note"],
            longitude=row.get("longitude"),
            latitude=row.get("latitude"),
            geocode_status="success" if has_manual_point else "pending",
            geocode_message="manual_pick" if has_manual_point else None,
            geocoded_at=now if has_manual_point else None,
            created_at=now,
        )
        db.add(item)
        merchant_items.append(item)

    competitor_items: list[SurveyCompetitorItem] = []
    for idx, row in enumerate(competitors):
        has_manual_point = row.get("longitude") is not None and row.get("latitude") is not None
        item = SurveyCompetitorItem(
            id=f"{submission_id}-c-{idx + 1}",
            submission_id=submission_id,
            project_id=project.project_id,
            name=row["name"],
            scale_m2=row["scale_m2"],
            avg_rent_unit_price=row["avg_rent_unit_price"],
            vacancy_rate=row["vacancy_rate"],
            business_type=row["business_type"],
            distance_km=row["distance_km"],
            target_people=row["target_people"],
            address=row["address"],
            city=row["city"],
            district=row["district"],
            longitude=row.get("longitude"),
            latitude=row.get("latitude"),
            geocode_status="success" if has_manual_point else "pending",
            geocode_message="manual_pick" if has_manual_point else None,
            geocoded_at=now if has_manual_point else None,
            created_at=now,
        )
        db.add(item)
        competitor_items.append(item)
    db.flush()

    geocoded_count = sum(1 for item in merchant_items if item.geocode_status == "success") + sum(
        1 for item in competitor_items if item.geocode_status == "success"
    )
    geocode_failed = 0
    needs_key_count = 0
    skipped_count = 0

    for item in merchant_items:
        if item.geocode_status != "pending":
            continue
        full_address = f"{item.city or ''}{item.district or ''}{item.address or ''}".strip()
        geo = geocode_address(db, full_address)
        status = geo.get("status") or "failed"
        if status == "success":
            geocoded_count += 1
        elif status == "needs_key":
            needs_key_count += 1
        elif status == "skipped":
            skipped_count += 1
        else:
            geocode_failed += 1
        item.longitude = geo.get("longitude")
        item.latitude = geo.get("latitude")
        item.geocode_status = status
        item.geocode_message = str(geo.get("message") or "")[:255] or None
        item.geocoded_at = now

    for item in competitor_items:
        if item.geocode_status != "pending":
            continue
        full_address = f"{item.city or ''}{item.district or ''}{item.address or ''}".strip()
        geo = geocode_address(db, full_address)
        status = geo.get("status") or "failed"
        if status == "success":
            geocoded_count += 1
        elif status == "needs_key":
            needs_key_count += 1
        elif status == "skipped":
            skipped_count += 1
        else:
            geocode_failed += 1
        item.longitude = geo.get("longitude")
        item.latitude = geo.get("latitude")
        item.geocode_status = status
        item.geocode_message = str(geo.get("message") or "")[:255] or None
        item.geocoded_at = now

    log_event(
        db,
        action="SURVEY_SUBMISSION_SAVE",
        entity_type="survey_submission",
        entity_id=submission_id,
        user_id=created_by,
        metadata={
            "project_id": project.project_id,
            "submission_id": submission_id,
            "version": version,
            "merchant_count": len(merchants),
            "competitor_count": len(competitors),
        },
        ip=ip,
    )
    log_event(
        db,
        action="SURVEY_GEOCODE",
        entity_type="survey_submission",
        entity_id=submission_id,
        user_id=created_by,
        metadata={
            "project_id": project.project_id,
            "submission_id": submission_id,
            "success_count": geocoded_count,
            "failed_count": geocode_failed,
            "needs_key_count": needs_key_count,
            "skipped_count": skipped_count,
            "item_count": len(merchants) + len(competitors),
        },
        ip=ip,
    )
    competitor_summary = "，".join(
        [row["name"] for row in competitors if _clean_text(row.get("name"))]
    )

    # 同步进入城市数据池（market_*），用于业务全览与独立查询
    create_market_submission(
        db,
        source_mode="project",
        project_id=project.project_id,
        city=project.city,
        district=project.district,
        created_by=created_by,
        merchant_rows=merchants,
        competitor_rows=competitors,
        enforce_uniqueness=False,
    )

    return {
        "submission_id": submission_id,
        "version": version,
        "merchant_count": len(merchants),
        "competitor_count": len(competitors),
        "geocoded_count": geocoded_count,
        "geocode_failed": geocode_failed,
        "needs_key_count": needs_key_count,
        "competitor_summary": competitor_summary or None,
    }


def _get_latest_survey_rows(
    db: Session,
    project_id: str,
) -> tuple[list[SurveyMerchantRowOut], list[SurveyCompetitionRowOut]]:
    submission = (
        db.query(SurveySubmission)
        .filter(SurveySubmission.project_id == project_id)
        .filter(SurveySubmission.deleted == 0)
        .order_by(SurveySubmission.version.desc())
        .first()
    )
    if not submission:
        return [], []

    merchants = (
        db.query(SurveyMerchantItem)
        .filter(SurveyMerchantItem.submission_id == submission.id)
        .filter(SurveyMerchantItem.deleted == 0)
        .order_by(SurveyMerchantItem.id.asc())
        .all()
    )
    competitors = (
        db.query(SurveyCompetitorItem)
        .filter(SurveyCompetitorItem.submission_id == submission.id)
        .filter(SurveyCompetitorItem.deleted == 0)
        .order_by(SurveyCompetitorItem.id.asc())
        .all()
    )

    merchant_rows = [
        SurveyMerchantRowOut(
            name=item.name,
            category=item.category,
            area_m2=item.area_m2,
            rent_unit_price=item.rent_unit_price,
            daily_flow=item.daily_flow,
            address=item.address,
            city=item.city,
            district=item.district,
            note=item.note,
            longitude=item.longitude,
            latitude=item.latitude,
            geocode_status=item.geocode_status,
            geocode_message=item.geocode_message,
            geocoded_at=item.geocoded_at,
            created_at=item.created_at,
        )
        for item in merchants
    ]
    competition_rows = [
        SurveyCompetitionRowOut(
            name=item.name,
            scale_m2=item.scale_m2,
            avg_rent_unit_price=item.avg_rent_unit_price,
            vacancy_rate=item.vacancy_rate,
            business_type=item.business_type,
            distance_km=item.distance_km,
            target_people=item.target_people,
            address=item.address,
            city=item.city,
            district=item.district,
            longitude=item.longitude,
            latitude=item.latitude,
            geocode_status=item.geocode_status,
            geocode_message=item.geocode_message,
            geocoded_at=item.geocoded_at,
            created_at=item.created_at,
        )
        for item in competitors
    ]
    return merchant_rows, competition_rows


def _to_out(
    entity: ProjectBaseInfo,
    calc_warning: Optional[str] = None,
    merchant_rows: Optional[list[SurveyMerchantRowOut]] = None,
    competition_rows: Optional[list[SurveyCompetitionRowOut]] = None,
) -> ProjectBaseInfoOut:
    return ProjectBaseInfoOut(
        project_id=entity.project_id,
        project_name=entity.project_name,
        city=entity.city,
        district=entity.district,
        location_desc=entity.location_desc,
        total_area=_round2(entity.total_area),
        rentable_area=_round2(entity.rentable_area),
        core_area=_round2(entity.core_area),
        asset_distribution=entity.asset_distribution,
        ownership_structure=entity.ownership_structure,
        vacancy_rate=_round2(entity.vacancy_rate),
        rent_min=_round2(entity.rent_min),
        rent_max=_round2(entity.rent_max),
        main_business_type=entity.main_business_type,
        competitor_list=entity.competitor_list,
        competition_level=entity.competition_level,
        city_population_10k=_round2(entity.city_population_10k),
        population_5km_10k=_round2(entity.population_5km_10k),
        population_3km_10k=_round2(entity.population_3km_10k),
        city_circle_level=entity.city_circle_level,
        competition_market_level=entity.competition_market_level,
        housing_price_5km=_round2(entity.housing_price_5km),
        disposable_income_10k=_round2(entity.disposable_income_10k),
        regional_function_level=entity.regional_function_level,
        commercial_planning_level=entity.commercial_planning_level,
        rail_access_level=entity.rail_access_level,
        arterial_access_level=entity.arterial_access_level,
        bus_access_level=entity.bus_access_level,
        operation_retrofit_potential_level=entity.operation_retrofit_potential_level,
        asset_rights_complexity_level=entity.asset_rights_complexity_level,
        remark=entity.remark,
        is_confirmed=entity.is_confirmed,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        calc_warning=calc_warning,
        merchant_rows=merchant_rows if merchant_rows is not None else [],
        competition_rows=competition_rows if competition_rows is not None else [],
    )


def _load_screening_indicators(db: Session, result_id: str) -> list[ScreeningIndicatorOut]:
    rows = (
        db.query(ProjectScreeningDetail)
        .filter(ProjectScreeningDetail.result_id == result_id)
        .all()
    )
    row_by_key = {row.indicator_key: row for row in rows}
    indicators: list[ScreeningIndicatorOut] = []
    for cfg in INDICATOR_CONFIG:
        row = row_by_key.get(cfg["key"])
        if not row:
            continue
        indicators.append(
            ScreeningIndicatorOut(
                key=row.indicator_key,
                category=row.category,
                name=row.indicator_name,
                level=row.level,
                mapped_score=row.mapped_score,
                weight=float(row.weight),
                weighted_score=round(float(row.weighted_score), 2),
                note=row.note or "",
                source_field=row.source_field,
                source_value=row.source_value,
                manual_override=row.manual_override,
            )
        )
    return indicators


def _to_screening_out(db: Session, result: ProjectScreeningResult) -> ProjectScreeningResultOut:
    breakdown = None
    if result.data_source_breakdown:
        try:
            parsed = json.loads(result.data_source_breakdown)
            if isinstance(parsed, dict):
                breakdown = {
                    str(key): int(value)
                    for key, value in parsed.items()
                    if isinstance(value, (int, float, str))
                }
        except Exception:
            breakdown = None
    return ProjectScreeningResultOut(
        id=result.id,
        project_id=result.project_id,
        total_score=round(float(result.total_score or 0), 1),
        conclusion=result.conclusion,
        risk_note=result.risk_note,
        overall_summary=result.overall_summary,
        score_version=result.score_version,
        data_source_breakdown=breakdown,
        calc_version=result.calc_version,
        created_at=result.created_at,
        indicators=_load_screening_indicators(db, result.id),
    )


@router.post("", response_model=ProjectBaseInfoOut)
def create_project(
    payload: ProjectBaseInfoCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not payload.project_name or not payload.city or not payload.district or payload.total_area is None:
        raise HTTPException(status_code=400, detail="project_name/city/district/total_area required")
    _validate_enums(payload.asset_distribution, payload.ownership_structure, payload.competition_level)
    _validate_ranges(payload.vacancy_rate)

    project_id = payload.project_id or _generate_project_id(db)
    now = datetime.utcnow().isoformat(timespec="seconds")

    merchant_payload = [row.model_dump() for row in (payload.merchant_rows or [])]
    competition_payload = [row.model_dump() for row in (payload.competition_rows or [])]
    competitor_summary = "，".join(
        [
            _clean_text(row.get("name"))
            for row in competition_payload
            if _clean_text(row.get("name"))
        ]
    )

    entity = ProjectBaseInfo(
        project_id=project_id,
        project_name=payload.project_name,
        city=payload.city,
        district=payload.district,
        location_desc=payload.location_desc,
        total_area=_round2(payload.total_area),
        rentable_area=_round2(payload.rentable_area),
        core_area=_round2(payload.core_area),
        asset_distribution=payload.asset_distribution,
        ownership_structure=payload.ownership_structure,
        vacancy_rate=_round2(payload.vacancy_rate),
        rent_min=_round2(payload.rent_min),
        rent_max=_round2(payload.rent_max),
        main_business_type=payload.main_business_type,
        competitor_list=competitor_summary or payload.competitor_list,
        competition_level=payload.competition_level,
        city_population_10k=_round2(payload.city_population_10k),
        population_5km_10k=_round2(payload.population_5km_10k),
        population_3km_10k=_round2(payload.population_3km_10k),
        city_circle_level=payload.city_circle_level,
        competition_market_level=payload.competition_market_level,
        housing_price_5km=_round2(payload.housing_price_5km),
        disposable_income_10k=_round2(payload.disposable_income_10k),
        regional_function_level=payload.regional_function_level,
        commercial_planning_level=payload.commercial_planning_level,
        rail_access_level=payload.rail_access_level,
        arterial_access_level=payload.arterial_access_level,
        bus_access_level=payload.bus_access_level,
        operation_retrofit_potential_level=payload.operation_retrofit_potential_level,
        asset_rights_complexity_level=payload.asset_rights_complexity_level,
        remark=payload.remark,
        is_confirmed=payload.is_confirmed or 0,
        created_at=now,
        updated_at=now,
    )
    db.add(entity)
    survey_info = _save_survey_submission(
        db,
        project=entity,
        created_by=user.id,
        merchant_rows=merchant_payload,
        competition_rows=competition_payload,
        ip=request.client.host if request.client else None,
    )
    if survey_info and survey_info.get("competitor_summary"):
        entity.competitor_list = survey_info.get("competitor_summary")
    db.commit()
    db.refresh(entity)
    merchant_rows, competition_rows = _get_latest_survey_rows(db, entity.project_id)

    log_event(
        db,
        action="BASE_PROJECT_CREATE",
        entity_type="project_base_info",
        entity_id=entity.project_id,
        user_id=user.id,
        metadata={
            "project_id": entity.project_id,
            "survey_submission_id": survey_info.get("submission_id") if survey_info else None,
        },
        ip=request.client.host if request.client else None,
    )

    return _to_out(
        entity,
        merchant_rows=merchant_rows,
        competition_rows=competition_rows,
    )


@router.get("", response_model=list[ProjectBaseInfoOut])
def list_projects(
    confirmed: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(ProjectBaseInfo)
    if confirmed is not None:
        query = query.filter(ProjectBaseInfo.is_confirmed == confirmed)
    items = query.order_by(ProjectBaseInfo.created_at.desc()).all()
    return [_to_out(item) for item in items]


@router.get("/{project_id}", response_model=ProjectBaseInfoOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entity = db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == project_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Project not found")
    merchant_rows, competition_rows = _get_latest_survey_rows(db, project_id)
    return _to_out(
        entity,
        merchant_rows=merchant_rows,
        competition_rows=competition_rows,
    )


@router.put("/{project_id}", response_model=ProjectBaseInfoOut)
def update_project(
    project_id: str,
    payload: ProjectBaseInfoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entity = db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == project_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Project not found")

    data = payload.model_dump(exclude_unset=True)
    merchant_payload = data.pop("merchant_rows", None)
    competition_payload = data.pop("competition_rows", None)

    competitor_summary = None
    if isinstance(competition_payload, list):
        competitor_summary = "，".join(
            [
                _clean_text(row.get("name"))
                for row in competition_payload
                if isinstance(row, dict) and _clean_text(row.get("name"))
            ]
        )
        data["competitor_list"] = competitor_summary or None

    if "asset_distribution" in data:
        _validate_enums(data.get("asset_distribution", entity.asset_distribution), entity.ownership_structure, entity.competition_level)
    if "ownership_structure" in data:
        _validate_enums(entity.asset_distribution, data.get("ownership_structure", entity.ownership_structure), entity.competition_level)
    if "competition_level" in data:
        _validate_enums(entity.asset_distribution, entity.ownership_structure, data.get("competition_level", entity.competition_level))
    if "vacancy_rate" in data:
        _validate_ranges(data.get("vacancy_rate"))

    numeric_fields = {
        "total_area",
        "rentable_area",
        "core_area",
        "rent_min",
        "rent_max",
        "vacancy_rate",
        "city_population_10k",
        "population_5km_10k",
        "population_3km_10k",
        "housing_price_5km",
        "disposable_income_10k",
    }
    for key, value in data.items():
        if key in numeric_fields and value is not None:
            setattr(entity, key, _round2(value))
        else:
            setattr(entity, key, value)

    survey_info = None
    if isinstance(merchant_payload, list) or isinstance(competition_payload, list):
        survey_info = _save_survey_submission(
            db,
            project=entity,
            created_by=user.id,
            merchant_rows=merchant_payload if isinstance(merchant_payload, list) else None,
            competition_rows=competition_payload if isinstance(competition_payload, list) else None,
            ip=request.client.host if request.client else None,
        )
        if survey_info and survey_info.get("competitor_summary"):
            entity.competitor_list = survey_info.get("competitor_summary")

    entity.updated_at = datetime.utcnow().isoformat(timespec="seconds")
    db.commit()
    db.refresh(entity)
    merchant_rows, competition_rows = _get_latest_survey_rows(db, entity.project_id)

    log_event(
        db,
        action="BASE_PROJECT_UPDATE",
        entity_type="project_base_info",
        entity_id=entity.project_id,
        user_id=user.id,
        metadata={
            "project_id": entity.project_id,
            "survey_submission_id": survey_info.get("submission_id") if survey_info else None,
        },
        ip=request.client.host if request.client else None,
    )

    return _to_out(
        entity,
        merchant_rows=merchant_rows,
        competition_rows=competition_rows,
    )


@router.post("/{project_id}/confirm", response_model=ProjectBaseInfoOut)
def confirm_project(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entity = db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == project_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Project not found")
    entity.is_confirmed = 1
    entity.updated_at = datetime.utcnow().isoformat(timespec="seconds")
    db.commit()
    db.refresh(entity)

    calc_warning: Optional[str] = None
    try:
        calc_version, auto_asset, auto_internal = _run_auto_calc_and_persist(db, entity, overrides=None)
        db.commit()
        log_event(
            db,
            action="CALC_AUTO",
            entity_type="calc_dual",
            entity_id=f"{entity.project_id}-v{calc_version}",
            user_id=user.id,
            metadata={
                "project_id": entity.project_id,
                "calc_version": calc_version,
                "trigger": "confirm",
            },
            ip=request.client.host if request.client else None,
        )
        snapshot_auto = create_project_snapshot(
            db,
            project_id=entity.project_id,
            snapshot_type="calc_auto",
            payload={
                "project_id": entity.project_id,
                "calc_version": calc_version,
                "external": _to_asset_out(auto_asset).model_dump(),
                "internal": _to_internal_out(auto_internal).model_dump(),
                "trigger": "confirm",
            },
            created_by=user.id,
        )
        log_event(
            db,
            action="PROJECT_SNAPSHOT_CREATE",
            entity_type="project_snapshot",
            entity_id=snapshot_auto.id,
            user_id=user.id,
            metadata={"project_id": entity.project_id, "snapshot_type": "calc_auto", "version": snapshot_auto.version},
            ip=request.client.host if request.client else None,
        )
    except Exception as exc:
        db.rollback()
        calc_warning = f"自动测算未完成：{exc}"

    log_event(
        db,
        action="BASE_PROJECT_CONFIRM",
        entity_type="project_base_info",
        entity_id=entity.project_id,
        user_id=user.id,
        metadata={"project_id": entity.project_id},
        ip=request.client.host if request.client else None,
    )
    snapshot = create_project_snapshot(
        db,
        project_id=entity.project_id,
        snapshot_type="collect_confirmed",
        payload=_to_out(entity).model_dump(),
        created_by=user.id,
    )
    log_event(
        db,
        action="PROJECT_SNAPSHOT_CREATE",
        entity_type="project_snapshot",
        entity_id=snapshot.id,
        user_id=user.id,
        metadata={"project_id": entity.project_id, "snapshot_type": "collect_confirmed", "version": snapshot.version},
        ip=request.client.host if request.client else None,
    )

    merchant_rows, competition_rows = _get_latest_survey_rows(db, entity.project_id)
    return _to_out(
        entity,
        calc_warning=calc_warning,
        merchant_rows=merchant_rows,
        competition_rows=competition_rows,
    )


@router.post("/{project_id}/screening/calc", response_model=ProjectScreeningResultOut)
def calc_screening(
    project_id: str,
    request: Request,
    payload: ScreeningCalcRequest = Body(default_factory=ScreeningCalcRequest),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entity = _require_confirmed(db, project_id)
    pool_values = _supplement_project_from_market(db, entity)
    state_fields: set[str] = set()
    for cfg in INDICATOR_CONFIG:
        for field in str(cfg.get("source_field") or "").split(","):
            name = field.strip()
            if name:
                state_fields.add(name)
    state = {field: getattr(entity, field, None) for field in state_fields}
    state.update(pool_values)
    pooled_entity = SimpleNamespace(**state)

    manual_scores = payload.manual_scores or {}
    for key, value in manual_scores.items():
        if key not in INDICATOR_BY_KEY:
            raise HTTPException(status_code=400, detail=f"unknown indicator key: {key}")
        if value not in (1, 2, 3, 4, 5):
            raise HTTPException(status_code=400, detail=f"manual score must be 1-5: {key}")

    indicator_rows: list[dict[str, Any]] = []
    missing_fields: list[str] = []
    total_score = 0.0
    data_source_breakdown = {"project": 0, "pool": 0, "manual": 0}

    for indicator in INDICATOR_CONFIG:
        key = indicator["key"]
        auto_level, source_value = evaluate_indicator_auto(indicator, entity)
        manual_level = manual_scores.get(key)
        if manual_level is not None:
            level = int(manual_level)
            manual_override = True
            source_kind = "manual"
        elif auto_level is not None:
            level = int(auto_level)
            manual_override = False
            source_kind = "project"
        else:
            pool_level, pool_value = evaluate_indicator_auto(indicator, pooled_entity)
            if pool_level is None:
                missing_fields.append(indicator["name"])
                continue
            level = int(pool_level)
            source_value = pool_value
            manual_override = False
            source_kind = "pool"

        mapped_score = level_to_score(level)
        weight = float(indicator["weight"])
        weighted_score = round(mapped_score * weight / 100, 2)
        total_score += weighted_score
        data_source_breakdown[source_kind] = data_source_breakdown.get(source_kind, 0) + 1
        indicator_rows.append(
            {
                "key": key,
                "category": indicator["category"],
                "name": indicator["name"],
                "level": level,
                "mapped_score": mapped_score,
                "weight": weight,
                "weighted_score": weighted_score,
                "note": indicator["note"],
                "source_field": indicator["source_field"],
                "source_value": source_value,
                "manual_override": manual_override,
                "source_kind": source_kind,
            }
        )

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "自动评分缺少必填字段，请补充后再存档",
                "missing_fields": missing_fields,
            },
        )

    total_score = round(total_score, 1)
    conclusion = conclusion_from_total(total_score)
    calc_version = _next_calc_version(db, ProjectScreeningResult, project_id)
    now = datetime.utcnow().isoformat(timespec="seconds")
    result = ProjectScreeningResult(
        id=f"{project_id}-v{calc_version}",
        project_id=project_id,
        total_score=total_score,
        conclusion=conclusion,
        risk_note=payload.risk_note,
        overall_summary="整体总结将由模型生成，主要呈现项目综合评价依据、优势与风险提示，约 300 字以内。",
        score_version=SCREENING_CONFIG_VERSION,
        data_source_breakdown=json.dumps(data_source_breakdown, ensure_ascii=False),
        calc_version=calc_version,
        created_at=now,
    )
    db.add(result)
    db.flush()

    for row in indicator_rows:
        db.add(
            ProjectScreeningDetail(
                id=f"{result.id}-{row['key']}",
                result_id=result.id,
                project_id=project_id,
                indicator_key=row["key"],
                category=row["category"],
                indicator_name=row["name"],
                level=row["level"],
                mapped_score=row["mapped_score"],
                weight=row["weight"],
                weighted_score=row["weighted_score"],
                note=row["note"],
                source_field=row["source_field"],
                source_value=None if row["source_value"] is None else str(row["source_value"]),
                manual_override=row["manual_override"],
            )
        )
    db.commit()
    db.refresh(result)

    log_event(
        db,
        action="SCREENING_CALC",
        entity_type="project_screening_result",
        entity_id=result.id,
        user_id=user.id,
        metadata={
            "project_id": project_id,
            "calc_version": calc_version,
            "total_score": total_score,
            "conclusion": conclusion,
        },
        ip=request.client.host if request.client else None,
    )
    snapshot = create_project_snapshot(
        db,
        project_id=project_id,
        snapshot_type="screening_calc",
        payload=_to_screening_out(db, result).model_dump(),
        created_by=user.id,
    )
    log_event(
        db,
        action="PROJECT_SNAPSHOT_CREATE",
        entity_type="project_snapshot",
        entity_id=snapshot.id,
        user_id=user.id,
        metadata={"project_id": project_id, "snapshot_type": "screening_calc", "version": snapshot.version},
        ip=request.client.host if request.client else None,
    )

    return _to_screening_out(db, result)


@router.get("/{project_id}/screening/latest", response_model=ProjectScreeningResultOut)
def latest_screening(
    project_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    result = (
        db.query(ProjectScreeningResult)
        .filter(ProjectScreeningResult.project_id == project_id)
        .order_by(ProjectScreeningResult.calc_version.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Screening result not found")

    return _to_screening_out(db, result)


@router.get("/{project_id}/export/json")
def export_project_json(
    project_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    screening = (
        db.query(ProjectScreeningResult)
        .filter(ProjectScreeningResult.project_id == project_id)
        .order_by(ProjectScreeningResult.calc_version.desc())
        .first()
    )
    asset_owner = (
        db.query(CalcAssetOwner)
        .filter(CalcAssetOwner.project_id == project_id)
        .order_by(CalcAssetOwner.calc_version.desc())
        .first()
    )
    internal = (
        db.query(CalcInternalOperation)
        .filter(CalcInternalOperation.project_id == project_id)
        .order_by(CalcInternalOperation.calc_version.desc())
        .first()
    )
    merchant = (
        db.query(CalcMerchant)
        .filter(CalcMerchant.project_id == project_id)
        .order_by(CalcMerchant.calc_version.desc())
        .first()
    )

    return {
        "project": _to_out(project).model_dump(),
        "screening_latest": _to_screening_out(db, screening).model_dump() if screening else None,
        "calc_asset_owner_latest": _to_asset_out(asset_owner).model_dump() if asset_owner else None,
        "calc_internal_latest": _to_internal_out(internal).model_dump() if internal else None,
        "calc_merchant_latest": CalcMerchantOut(
            id=merchant.id,
            project_id=merchant.project_id,
            shop_area=merchant.shop_area,
            shop_rent=merchant.shop_rent,
            daily_flow=merchant.daily_flow,
            avg_ticket=merchant.avg_ticket,
            annual_revenue=merchant.annual_revenue,
            annual_cost=merchant.annual_cost,
            break_even_rent=merchant.break_even_rent,
            calc_version=merchant.calc_version,
            created_at=merchant.created_at,
        ).model_dump()
        if merchant
        else None,
    }


@router.post("/{project_id}/calc/auto", response_model=CalcAutoResponse)
def calc_auto(
    project_id: str,
    request: Request,
    payload: CalcAutoRequest = Body(default_factory=CalcAutoRequest),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = _require_confirmed(db, project_id)
    overrides = payload.overrides.model_dump(exclude_none=True) if payload.overrides else None
    calc_version, asset, internal = _run_auto_calc_and_persist(db, project, overrides=overrides)
    db.commit()
    db.refresh(asset)
    db.refresh(internal)

    log_event(
        db,
        action="CALC_AUTO",
        entity_type="calc_dual",
        entity_id=f"{project_id}-v{calc_version}",
        user_id=user.id,
        metadata={
            "project_id": project_id,
            "calc_version": calc_version,
            "trigger": "manual",
        },
        ip=request.client.host if request.client else None,
    )

    external_out = _to_asset_out(asset)
    internal_out = _to_internal_out(internal)
    snapshot = create_project_snapshot(
        db,
        project_id=project_id,
        snapshot_type="calc_auto",
        payload={
            "project_id": project_id,
            "calc_version": calc_version,
            "external": external_out.model_dump(),
            "internal": internal_out.model_dump(),
        },
        created_by=user.id,
    )
    log_event(
        db,
        action="PROJECT_SNAPSHOT_CREATE",
        entity_type="project_snapshot",
        entity_id=snapshot.id,
        user_id=user.id,
        metadata={"project_id": project_id, "snapshot_type": "calc_auto", "version": snapshot.version},
        ip=request.client.host if request.client else None,
    )

    return CalcAutoResponse(
        project_id=project_id,
        calc_version=calc_version,
        external={
            "summary": external_out.summary,
            "yearly": external_out.yearly,
            "params_used": external_out.params_used or {},
            "source": external_out.source or "auto_from_collection",
            "calc_basis": external_out.calc_basis or "owner_v1",
        },
        internal={
            "summary": internal_out.summary,
            "yearly": internal_out.yearly,
            "params_used": internal_out.params_used or {},
            "source": internal_out.source or "auto_from_collection",
            "calc_basis": internal_out.calc_basis or "huarun_v1",
        },
    )


@router.post("/{project_id}/calc/asset_owner", response_model=CalcAssetOwnerOut)
def calc_asset_owner(
    project_id: str,
    payload: CalcAssetOwnerRequest,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = _require_confirmed(db, project_id)

    occupancy = _normalize_occupancy(payload.target_occupancy)
    area = project.rentable_area if project.rentable_area is not None else project.total_area or 0
    annual_rent_income = area * payload.target_rent * 12 * occupancy

    roi = None if payload.invest_cost == 0 else annual_rent_income / payload.invest_cost
    payback_year = None if annual_rent_income == 0 else payload.invest_cost / annual_rent_income

    calc_version = _next_calc_version(db, CalcAssetOwner, project_id)
    now = datetime.utcnow().isoformat(timespec="seconds")
    summary = {
        "total_revenue": _round2(annual_rent_income),
        "total_cost": _round2(payload.invest_cost),
        "gross_profit": _round2((annual_rent_income - payload.invest_cost) if payload.invest_cost is not None else None),
        "gross_margin": _round2(roi),
        "tax_after_profit": _round2((annual_rent_income - payload.invest_cost) if payload.invest_cost is not None else None),
    }
    yearly = [
        {
            "year_index": 1,
            "year_label": "第1年",
            "revenue": _round2(annual_rent_income),
            "cost": _round2(payload.invest_cost),
            "gross_profit": _round2((annual_rent_income - payload.invest_cost) if payload.invest_cost is not None else None),
            "gross_margin": _round2(roi),
            "tax": None,
        }
    ]
    record = CalcAssetOwner(
        id=f"{project_id}-asset-v{calc_version}",
        project_id=project_id,
        target_rent=payload.target_rent,
        target_occupancy=occupancy,
        annual_rent_income=annual_rent_income,
        invest_cost=payload.invest_cost,
        roi=roi,
        payback_year=payback_year,
        details_json=json.dumps({"summary": summary, "yearly": yearly}, ensure_ascii=False),
        params_json=json.dumps(
            {
                "target_rent": payload.target_rent,
                "target_occupancy": occupancy,
                "invest_cost": payload.invest_cost,
            },
            ensure_ascii=False,
        ),
        calc_basis="legacy_manual",
        calc_version=calc_version,
        created_at=now,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_event(
        db,
        action="CALC_ASSET_OWNER",
        entity_type="calc_asset_owner",
        entity_id=record.id,
        user_id=user.id,
        metadata={"project_id": project_id, "calc_version": calc_version},
        ip=request.client.host if request.client else None,
    )

    return _to_asset_out(record)


@router.post("/{project_id}/calc/internal", response_model=CalcInternalOperationOut)
def calc_internal(
    project_id: str,
    payload: CalcInternalOperationRequest,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    project = _require_confirmed(db, project_id)

    rent_min = project.rent_min
    rent_max = project.rent_max
    if rent_min is not None and rent_max is not None:
        avg_rent = (rent_min + rent_max) / 2
    elif rent_min is not None:
        avg_rent = rent_min
    elif rent_max is not None:
        avg_rent = rent_max
    else:
        avg_rent = 0

    if project.vacancy_rate is None:
        occupancy = 1
    else:
        occupancy = 1 - (project.vacancy_rate / 100)

    area = project.rentable_area if project.rentable_area is not None else project.total_area or 0
    annual_rent_for_calc = area * avg_rent * 12 * occupancy

    service_income = annual_rent_for_calc * payload.service_fee_rate
    manage_income = annual_rent_for_calc * payload.manage_fee_rate
    total_income = service_income + manage_income
    total_cost = payload.staff_cost + payload.other_cost
    total_profit = total_income - total_cost
    profit_margin = None if total_income == 0 else total_profit / total_income

    calc_version = _next_calc_version(db, CalcInternalOperation, project_id)
    now = datetime.utcnow().isoformat(timespec="seconds")
    summary = {
        "total_revenue": _round2(total_income),
        "total_cost": _round2(total_cost),
        "gross_profit": _round2(total_profit),
        "gross_margin": _round2(profit_margin),
        "tax_after_profit": _round2(total_profit),
    }
    yearly = [
        {
            "year_index": 1,
            "year_label": "第1年",
            "revenue": _round2(total_income),
            "cost": _round2(total_cost),
            "gross_profit": _round2(total_profit),
            "gross_margin": _round2(profit_margin),
            "tax": None,
        }
    ]
    record = CalcInternalOperation(
        id=f"{project_id}-internal-v{calc_version}",
        project_id=project_id,
        service_fee_rate=payload.service_fee_rate,
        manage_fee_rate=payload.manage_fee_rate,
        annual_rent_for_calc=annual_rent_for_calc,
        service_income=service_income,
        manage_income=manage_income,
        staff_cost=payload.staff_cost,
        other_cost=payload.other_cost,
        total_income=total_income,
        total_cost=total_cost,
        total_profit=total_profit,
        profit_margin=profit_margin,
        details_json=json.dumps({"summary": summary, "yearly": yearly}, ensure_ascii=False),
        params_json=json.dumps(
            {
                "service_fee_rate": payload.service_fee_rate,
                "manage_fee_rate": payload.manage_fee_rate,
                "staff_cost": payload.staff_cost,
                "other_cost": payload.other_cost,
            },
            ensure_ascii=False,
        ),
        calc_basis="legacy_manual",
        calc_version=calc_version,
        created_at=now,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_event(
        db,
        action="CALC_INTERNAL",
        entity_type="calc_internal_operation",
        entity_id=record.id,
        user_id=user.id,
        metadata={"project_id": project_id, "calc_version": calc_version},
        ip=request.client.host if request.client else None,
    )

    return _to_internal_out(record)


@router.post("/{project_id}/calc/merchant", response_model=CalcMerchantOut)
def calc_merchant(
    project_id: str,
    payload: CalcMerchantRequest,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _require_confirmed(db, project_id)

    annual_revenue = payload.daily_flow * payload.avg_ticket * 365
    if payload.shop_area == 0:
        break_even_rent = None
    else:
        break_even_rent = (annual_revenue - payload.annual_cost) / (payload.shop_area * 12)

    calc_version = _next_calc_version(db, CalcMerchant, project_id)
    now = datetime.utcnow().isoformat(timespec="seconds")
    record = CalcMerchant(
        id=f"{project_id}-merchant-v{calc_version}",
        project_id=project_id,
        shop_area=payload.shop_area,
        shop_rent=payload.shop_rent,
        daily_flow=payload.daily_flow,
        avg_ticket=payload.avg_ticket,
        annual_revenue=annual_revenue,
        annual_cost=payload.annual_cost,
        break_even_rent=break_even_rent,
        calc_version=calc_version,
        created_at=now,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_event(
        db,
        action="CALC_MERCHANT",
        entity_type="calc_merchant",
        entity_id=record.id,
        user_id=user.id,
        metadata={"project_id": project_id, "calc_version": calc_version},
        ip=request.client.host if request.client else None,
    )

    return CalcMerchantOut(
        id=record.id,
        project_id=record.project_id,
        shop_area=record.shop_area,
        shop_rent=record.shop_rent,
        daily_flow=record.daily_flow,
        avg_ticket=record.avg_ticket,
        annual_revenue=record.annual_revenue,
        annual_cost=record.annual_cost,
        break_even_rent=record.break_even_rent,
        calc_version=record.calc_version,
        created_at=record.created_at,
    )


@router.get(
    "/{project_id}/calc/{calc_type}/latest",
    response_model=CalcAssetOwnerOut | CalcInternalOperationOut | CalcMerchantOut,
)
def latest_calc(
    project_id: str,
    calc_type: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if calc_type == "asset_owner":
        result = (
            db.query(CalcAssetOwner)
            .filter(CalcAssetOwner.project_id == project_id)
            .order_by(CalcAssetOwner.calc_version.desc())
            .first()
        )
        if not result:
            raise HTTPException(status_code=404, detail="Calc result not found")
        return _to_asset_out(result)
    if calc_type == "internal":
        result = (
            db.query(CalcInternalOperation)
            .filter(CalcInternalOperation.project_id == project_id)
            .order_by(CalcInternalOperation.calc_version.desc())
            .first()
        )
        if not result:
            raise HTTPException(status_code=404, detail="Calc result not found")
        return _to_internal_out(result)
    if calc_type == "merchant":
        result = (
            db.query(CalcMerchant)
            .filter(CalcMerchant.project_id == project_id)
            .order_by(CalcMerchant.calc_version.desc())
            .first()
        )
        if not result:
            raise HTTPException(status_code=404, detail="Calc result not found")
        return CalcMerchantOut(
            id=result.id,
            project_id=result.project_id,
            shop_area=result.shop_area,
            shop_rent=result.shop_rent,
            daily_flow=result.daily_flow,
            avg_ticket=result.avg_ticket,
            annual_revenue=result.annual_revenue,
            annual_cost=result.annual_cost,
            break_even_rent=result.break_even_rent,
            calc_version=result.calc_version,
            created_at=result.created_at,
        )
    raise HTTPException(status_code=400, detail="calc_type must be asset_owner|internal|merchant")
