"""业态构成与调改测算：现有业态分布 + 逐铺位调改计划 → 调改后预测（租金/坪效/出租率/NOI）
   + 按季度、跟随租约到期的分批调改路线图。"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from ..models import Lease, Merchant, ProjectCost, Unit, UnitAdjustmentPlan
from .classification import build_format_index

_RENTED = ("在租", "自营")
_VACANT_LABEL = "空置"
_UNLABELED = "未标注"


def _quarter(d: date) -> str:
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def _quarter_key(q: str) -> tuple[int, int]:
    y, n = q.split("Q")
    return (int(y), int(n))


def _active_lease_end(db: Session, project_id: int) -> dict[int, date]:
    """每个铺位现行(生效)租约的到期日；同铺多约取最晚。"""
    out: dict[int, date] = {}
    for ll in db.query(Lease).filter(Lease.project_id == project_id,
                                     Lease.lease_status == "生效").all():
        if ll.unit_id is not None and ll.end_date is not None:
            cur = out.get(ll.unit_id)
            if cur is None or ll.end_date > cur:
                out[ll.unit_id] = ll.end_date
    return out


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
    lease_end = _active_lease_end(db, project_id)

    rows = []
    for u in units:
        occ = u.status in _RENTED
        m = merch.get(u.id)
        p = plans.get(u.id)
        area = u.rentable_area_m2 or 0.0
        end = lease_end.get(u.id)
        rows.append({
            "unit_id": u.id, "unit_code": u.unit_code, "floor": u.floor or "L1",
            "area": _round(area), "status": u.status,
            "tenant": (m.name if (m and occ) else None),
            "format": (m.business_format if (m and occ) else None),
            "rent": _round(rent_by_unit.get(u.id, 0.0)),
            "lease_end": end.isoformat() if end else None,
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


def adjustment_roadmap(db: Session, project_id: int, today: date | None = None) -> dict:
    """按季度、跟随租约到期的分批调改路线图（当前口径：等到期自然调整）。

    每个有调改计划的铺位，其“最早可执行季度”取自：
      - 空置铺 → 立即（今季）；
      - 在租铺 → 现租约到期日所在季度（到期才动）。
    输出：分批(batches) + 累积出租率/租金曲线 + 各季度到期窗口(expiry_windows)。
    """
    today = today or date.today()
    units, rent_by_unit, fmt_by_unit = _unit_context(db, project_id)
    unit_by_id = {u.id: u for u in units}
    lease_end = _active_lease_end(db, project_id)
    plans = {p.unit_id: p for p in db.query(UnitAdjustmentPlan).filter(
        UnitAdjustmentPlan.project_id == project_id).all()}
    total_units = len(units)
    base_occupied = sum(1 for u in units if u.status in _RENTED)

    # 分批：有计划的铺位 → 归入“最早可执行季度”
    buckets: dict[str, list] = {}
    for uid, p in plans.items():
        u = unit_by_id.get(uid)
        if not u:
            continue
        occ = u.status in _RENTED
        when = today if not occ else (lease_end.get(uid) or (p.plan_date or today))
        q = _quarter(when)
        area = u.rentable_area_m2 or 0.0
        cur_rent = rent_by_unit.get(uid, 0.0)
        exp_rent = (p.expected_rent if p.expected_rent is not None
                    else (p.expected_rent_psm or 0.0) * area if p.expected_rent_psm is not None
                    else cur_rent)
        buckets.setdefault(q, []).append({
            "unit_id": uid, "unit_code": u.unit_code, "floor": u.floor,
            "action": p.action, "from_format": p.from_format or fmt_by_unit.get(uid),
            "to_format": p.to_format, "current_rent": _round(cur_rent),
            "expected_rent": _round(exp_rent), "rent_delta": _round(exp_rent - cur_rent),
            "lease_end": lease_end.get(uid).isoformat() if lease_end.get(uid) else None,
            "fills_vacancy": not occ,
        })

    batches, cum_rent, cum_new_occ = [], 0.0, 0
    for q in sorted(buckets, key=_quarter_key):
        items = buckets[q]
        rent_delta = _round(sum(i["rent_delta"] for i in items))
        area_freed = _round(sum((unit_by_id[i["unit_id"]].rentable_area_m2 or 0.0) for i in items))
        cum_rent = _round(cum_rent + rent_delta)
        cum_new_occ += sum(1 for i in items if i["fills_vacancy"])
        batches.append({
            "quarter": q, "unit_count": len(items), "area_freed": area_freed,
            "rent_delta": rent_delta, "cum_rent_delta": cum_rent,
            "cum_occupancy_rate": round((base_occupied + cum_new_occ) / total_units, 4)
            if total_units else 0.0,
            "units": items,
        })

    # 到期窗口：所有在租铺位按到期季度分布（含未规划的 → 未来可调机会）
    win: dict[str, dict] = {}
    for u in units:
        if u.status not in _RENTED:
            continue
        end = lease_end.get(u.id)
        if not end:
            continue
        q = _quarter(end)
        w = win.setdefault(q, {"quarter": q, "expiring_units": 0, "expiring_area": 0.0,
                               "planned": 0})
        w["expiring_units"] += 1
        w["expiring_area"] = _round(w["expiring_area"] + (u.rentable_area_m2 or 0.0))
        if u.id in plans:
            w["planned"] += 1
    expiry_windows = [win[q] for q in sorted(win, key=_quarter_key)]

    return {
        "project_id": project_id, "policy": "等到期自然调整",
        "summary": {
            "planned_units": sum(len(v) for v in buckets.values()),
            "batch_count": len(batches),
            "first_quarter": batches[0]["quarter"] if batches else None,
            "last_quarter": batches[-1]["quarter"] if batches else None,
            "total_rent_delta": batches[-1]["cum_rent_delta"] if batches else 0.0,
            "current_occupancy_rate": round(base_occupied / total_units, 4) if total_units else 0.0,
        },
        "batches": batches,
        "expiry_windows": expiry_windows,
    }


# ---------- 提前置换 vs 等到期：成本收益对比（估算，假设参数可覆盖） ----------

# 默认假设（无真实历史解约案例时的估算口径，返回体里会原样带出，前端应标注"估算"）
_DEFAULT_TERMINATION_MONTHS = 3.0   # 解约补偿 = 现租金 × N 月
_DEFAULT_FREE_RENT_MONTHS = 2.0     # 提前置换后给新租户的免租期（月）
_DEFAULT_FITOUT_PSM = 400.0         # 装修/改造一次性成本（元/㎡）
_DEFAULT_HORIZON_MONTHS = 24        # 对比考察期（月）


def early_swap_tradeoff(
    db: Session, project_id: int, unit_id: int,
    termination_months: float | None = None, free_rent_months: float | None = None,
    fitout_cost_psm: float | None = None, horizon_months: int | None = None,
) -> dict:
    """对比同一铺位「等到期自然调整」vs「提前置换」在考察期内的净现金对比。

    仅估算，用于辅助判断"哪些铺值得花钱提前动"；口径：
    - 等到期：到期前收现租，到期后收新租（计划的 expected_rent），无额外成本；
    - 提前置换：即刻起按新租收，但要扣：解约补偿(现租金×N月) + 免租期(新租金×N月) + 装修(面积×单价)。
    """
    termination_months = _DEFAULT_TERMINATION_MONTHS if termination_months is None else termination_months
    free_rent_months = _DEFAULT_FREE_RENT_MONTHS if free_rent_months is None else free_rent_months
    fitout_cost_psm = _DEFAULT_FITOUT_PSM if fitout_cost_psm is None else fitout_cost_psm
    horizon_months = _DEFAULT_HORIZON_MONTHS if horizon_months is None else horizon_months

    unit = db.get(Unit, unit_id)
    if not unit or unit.project_id != project_id:
        raise ValueError("铺位不存在或不属于该项目")
    plan = db.query(UnitAdjustmentPlan).filter(UnitAdjustmentPlan.unit_id == unit_id).first()
    if not plan:
        raise ValueError("该铺位暂无调改计划，无法测算")
    area = unit.rentable_area_m2 or 0.0
    _, rent_by_unit, _ = _unit_context(db, project_id)
    current_rent = rent_by_unit.get(unit_id, 0.0)
    expected_rent = (plan.expected_rent if plan.expected_rent is not None
                    else (plan.expected_rent_psm or 0.0) * area)

    occupied = unit.status in _RENTED
    lease_end = _active_lease_end(db, project_id).get(unit_id)
    if not occupied or lease_end is None:
        return {
            "unit_id": unit_id, "unit_code": unit.unit_code, "applicable": False,
            "reason": "该铺位当前空置，无在租租约可提前解约——直接招商即可，无需对比。",
        }

    today = date.today()
    months_to_expiry = max(0.0, (lease_end.year - today.year) * 12
                           + (lease_end.month - today.month)
                           + (lease_end.day - today.day) / 30.0)
    months_to_expiry = min(months_to_expiry, horizon_months)

    wait_net = (current_rent * months_to_expiry
               + expected_rent * max(0.0, horizon_months - months_to_expiry))
    termination_cost = current_rent * termination_months
    free_rent_cost = expected_rent * free_rent_months
    fitout_cost = area * fitout_cost_psm
    early_net = (expected_rent * horizon_months
                - termination_cost - free_rent_cost - fitout_cost)
    delta = _round(early_net - wait_net)

    return {
        "unit_id": unit_id, "unit_code": unit.unit_code, "applicable": True,
        "assumptions": {
            "termination_months": termination_months, "free_rent_months": free_rent_months,
            "fitout_cost_psm": fitout_cost_psm, "horizon_months": horizon_months,
            "note": "解约补偿/免租期/装修单价为估算假设（无真实历史解约案例），可按项目实际经验调整。",
        },
        "inputs": {"current_rent": _round(current_rent), "expected_rent": _round(expected_rent),
                   "area": _round(area), "lease_end": lease_end.isoformat(),
                   "months_to_expiry": round(months_to_expiry, 1)},
        "wait": {"label": "等到期自然调整", "net_cash_over_horizon": _round(wait_net),
                "one_time_cost": 0.0},
        "early": {"label": "提前置换", "net_cash_over_horizon": _round(early_net),
                 "one_time_cost": _round(termination_cost + free_rent_cost + fitout_cost),
                 "cost_breakdown": {"解约补偿": _round(termination_cost),
                                    "免租期损失": _round(free_rent_cost),
                                    "装修改造": _round(fitout_cost)}},
        "recommendation": "提前置换更划算" if delta > 0 else "建议等到期",
        "net_benefit_of_early": delta,
    }
