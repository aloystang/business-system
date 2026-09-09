"""业态构成与调改测算：现有业态分布 + 逐铺位调改计划 → 调改后预测（租金/坪效/出租率/NOI）。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Lease, Merchant, ProjectCost, Unit, UnitAdjustmentPlan
from .classification import build_format_index

_RENTED = ("在租", "自营")
_VACANT_LABEL = "空置"
_UNLABELED = "未标注"


def _round(x: float | None) -> float:
    return round(float(x or 0.0), 2)


def _unit_context(db: Session, project_id: int):
    """返回 (units, 每铺现租金 dict, 每铺现业态 dict)。"""
    units = db.query(Unit).filter(Unit.project_id == project_id).all()
    rent_by_unit: dict[int, float] = {}
    for ll in db.query(Lease).filter(Lease.project_id == project_id,
                                     Lease.lease_status == "生效").all():
        if ll.unit_id is not None:
            rent_by_unit[ll.unit_id] = rent_by_unit.get(ll.unit_id, 0.0) + (ll.base_rent or 0.0)
    fmt_by_unit: dict[int, str] = {}
    for m in db.query(Merchant).filter(Merchant.project_id == project_id).all():
        if m.unit_id is not None:
            fmt_by_unit[m.unit_id] = m.business_format or _UNLABELED
    return units, rent_by_unit, fmt_by_unit


def _bucket_add(agg: dict, key: str, units: int, area: float, rent: float) -> None:
    b = agg.setdefault(key, {"format": key, "units": 0, "area": 0.0, "rent": 0.0})
    b["units"] += units
    b["area"] = _round(b["area"] + area)
    b["rent"] = _round(b["rent"] + rent)


_FLOOR_ORDER = {"B3": -3, "B2": -2, "B1": -1}


def _floor_key(f: str | None) -> int:
    f = f or ""
    if f in _FLOOR_ORDER:
        return _FLOOR_ORDER[f]
    if f[:1] in ("L", "F") and f[1:].isdigit():
        return int(f[1:])
    return 99


def unit_layout(db: Session, project_id: int) -> dict:
    """2.5D 铺位沙盘数据源：逐铺位一条（含现租户/业态/租金 + 调改计划），已按楼层排序。"""
    units = db.query(Unit).filter(Unit.project_id == project_id).all()
    merch = {m.unit_id: m for m in db.query(Merchant).filter(
        Merchant.project_id == project_id).all() if m.unit_id is not None}
    rent_by_unit: dict[int, float] = {}
    for ll in db.query(Lease).filter(Lease.project_id == project_id,
                                     Lease.lease_status == "生效").all():
        if ll.unit_id is not None:
            rent_by_unit[ll.unit_id] = rent_by_unit.get(ll.unit_id, 0.0) + (ll.base_rent or 0.0)
    plans = {p.unit_id: p for p in db.query(UnitAdjustmentPlan).filter(
        UnitAdjustmentPlan.project_id == project_id).all()}

    rows = []
    for u in units:
        occ = u.status in _RENTED
        m = merch.get(u.id)
        p = plans.get(u.id)
        area = u.rentable_area_m2 or 0.0
        rows.append({
            "unit_id": u.id, "unit_code": u.unit_code, "floor": u.floor or "L1",
            "area": _round(area), "status": u.status,
            "tenant": (m.name if (m and occ) else None),
            "format": (m.business_format if (m and occ) else None),
            "rent": _round(rent_by_unit.get(u.id, 0.0)),
            "plan": ({"action": p.action, "to_format": p.to_format,
                      "target_brand_id": p.target_brand_id,
                      "expected_rent": _round(p.expected_rent) if p.expected_rent is not None
                      else (_round((p.expected_rent_psm or 0.0) * area)
                            if p.expected_rent_psm is not None else None),
                      "plan_status": p.plan_status,
                      "plan_date": p.plan_date.isoformat() if p.plan_date else None} if p else None),
        })
    rows.sort(key=lambda r: (_floor_key(r["floor"]), r["unit_code"]))
    floors = sorted({r["floor"] for r in rows}, key=_floor_key)
    return {"project_id": project_id, "floors": floors, "units": rows}


def current_mix(db: Session, project_id: int) -> dict:
    """现有业态构成：按业态汇总铺位数/计租面积/月租金 + 占比；空置单列；并按一级业态归总。"""
    units, rent_by_unit, fmt_by_unit = _unit_context(db, project_id)
    by_fmt: dict[str, dict] = {}
    vacant = {"units": 0, "area": 0.0}
    total_units = len(units)
    total_area = 0.0
    for u in units:
        area = u.rentable_area_m2 or 0.0
        total_area += area
        if u.status not in _RENTED:
            vacant["units"] += 1
            vacant["area"] = _round(vacant["area"] + area)
            continue
        fmt = fmt_by_unit.get(u.id, _UNLABELED)
        _bucket_add(by_fmt, fmt, 1, area, rent_by_unit.get(u.id, 0.0))

    rows = sorted(by_fmt.values(), key=lambda r: r["rent"], reverse=True)
    rent_total = _round(sum(r["rent"] for r in rows))
    rented_units = sum(r["units"] for r in rows)
    for r in rows:
        r["unit_pct"] = round(r["units"] / rented_units, 4) if rented_units else 0.0
        r["rent_pct"] = round(r["rent"] / rent_total, 4) if rent_total else 0.0

    # 一级业态归总（业态树）
    idx = build_format_index(db)
    by_l1: dict[str, dict] = {}
    for r in rows:
        _bucket_add(by_l1, idx.get(r["format"], r["format"]), r["units"], r["area"], r["rent"])

    return {
        "project_id": project_id,
        "totals": {"unit_total": total_units, "area_total": _round(total_area),
                   "rented_units": rented_units, "vacant_units": vacant["units"],
                   "occupancy_rate": round(rented_units / total_units, 4) if total_units else 0.0,
                   "rent_total": rent_total},
        "by_format": rows,
        "by_l1": sorted(by_l1.values(), key=lambda r: r["rent"], reverse=True),
        "vacant": {"units": vacant["units"], "area": _round(vacant["area"])},
    }


def _planned_rent(plan: UnitAdjustmentPlan | None, area: float, current_rent: float,
                  occupied: bool) -> float:
    if plan is not None:
        if plan.expected_rent is not None:
            return plan.expected_rent or 0.0
        if plan.expected_rent_psm is not None:
            return _round((plan.expected_rent_psm or 0.0) * area)
    return current_rent if occupied else 0.0


def _planned_occupied(plan: UnitAdjustmentPlan | None, occupied: bool) -> bool:
    if plan is not None and plan.action in ("新招商", "置换", "改造", "升级", "合并", "拆分"):
        return True
    return occupied


def plan_summary(db: Session, project_id: int) -> dict:
    """逐铺位调改计划 + 调改后预测（对比现状）。"""
    units, rent_by_unit, fmt_by_unit = _unit_context(db, project_id)
    plans = {p.unit_id: p for p in db.query(UnitAdjustmentPlan).filter(
        UnitAdjustmentPlan.project_id == project_id).all()}
    unit_by_id = {u.id: u for u in units}

    items = []
    cur_rent_total = plan_rent_total = 0.0
    cur_rented = plan_rented = 0
    cur_area_rented = plan_area_rented = 0.0
    planned_by_fmt: dict[str, dict] = {}
    for u in units:
        area = u.rentable_area_m2 or 0.0
        occ = u.status in _RENTED
        cur_rent = rent_by_unit.get(u.id, 0.0)
        cur_fmt = fmt_by_unit.get(u.id) if occ else None
        p = plans.get(u.id)
        p_occ = _planned_occupied(p, occ)
        p_rent = _planned_rent(p, area, cur_rent, occ)
        p_fmt = (p.to_format if p and p.to_format else cur_fmt)
        cur_rent_total += cur_rent
        plan_rent_total += p_rent
        if occ:
            cur_rented += 1; cur_area_rented += area
        if p_occ:
            plan_rented += 1; plan_area_rented += area
            _bucket_add(planned_by_fmt, p_fmt or _UNLABELED, 1, area, p_rent)
        if p is not None:
            items.append({
                "unit_id": u.id, "unit_code": u.unit_code, "floor": u.floor,
                "area": _round(area), "status": u.status,
                "action": p.action, "from_format": p.from_format or cur_fmt,
                "to_format": p.to_format, "target_brand_id": p.target_brand_id,
                "expected_rent": _round(p_rent), "current_rent": _round(cur_rent),
                "plan_status": p.plan_status, "plan_date": p.plan_date.isoformat()
                if p.plan_date else None, "reason": p.reason, "owner": p.owner,
            })

    total_units = len(units)
    cost_total = db.query(ProjectCost.amount).filter(
        ProjectCost.project_id == project_id).all()
    monthly_cost = _round(sum(c[0] or 0.0 for c in cost_total))
    summary = {
        "unit_total": total_units, "plan_items": len(items),
        "current": {
            "occupancy_rate": round(cur_rented / total_units, 4) if total_units else 0.0,
            "rent_total": _round(cur_rent_total),
            "rent_psm": _round(cur_rent_total / cur_area_rented) if cur_area_rented else 0.0,
            "noi": _round(cur_rent_total - monthly_cost),
        },
        "planned": {
            "occupancy_rate": round(plan_rented / total_units, 4) if total_units else 0.0,
            "rent_total": _round(plan_rent_total),
            "rent_psm": _round(plan_rent_total / plan_area_rented) if plan_area_rented else 0.0,
            "noi": _round(plan_rent_total - monthly_cost),
        },
        "delta": {
            "rent_total": _round(plan_rent_total - cur_rent_total),
            "noi": _round(plan_rent_total - cur_rent_total),   # 成本不变假设
            "occupancy_pts": round((plan_rented - cur_rented) / total_units, 4)
            if total_units else 0.0,
        },
        "monthly_cost": monthly_cost,
    }
    return {"project_id": project_id, "items": items,
            "planned_by_format": sorted(planned_by_fmt.values(),
                                        key=lambda r: r["rent"], reverse=True),
            "summary": summary}
