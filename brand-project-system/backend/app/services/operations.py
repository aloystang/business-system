"""经营台账聚合：单项目经营情况 + 多项目组合总览（财务/领导视角）。

口径：
- 出租率 =（在租+自营）铺位 / 铺位总数；面积出租率 = 已租计租面积 / 总计租面积。
- 收入(应收=权责口径)、收入(实收=现金口径)，按费项拆分。
- 成本按成本类型（物业成本/水电能耗/人力/维修/其他）。
- NOI(经营利润, 现金口径) = 实收收入 − 成本；收缴率 = 实收 / 应收。
- 水电为代收代付：收入侧「水电代收」与成本侧「水电能耗」在 NOI 中自然对冲。
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Lease, Project, ProjectCost, Receivable, Unit

_RENTED = ("在租", "自营")


def _round(x: float | None) -> float:
    return round(x or 0.0, 2)


def _occupancy(db: Session, project_id: int) -> dict:
    by_status = dict(
        db.query(Unit.status, func.count()).filter(
            Unit.project_id == project_id).group_by(Unit.status).all())
    total = sum(by_status.values())
    rented = by_status.get("在租", 0) + by_status.get("自营", 0)
    total_area = db.query(func.coalesce(func.sum(Unit.rentable_area_m2), 0.0)).filter(
        Unit.project_id == project_id).scalar() or 0.0
    rented_area = db.query(func.coalesce(func.sum(Unit.rentable_area_m2), 0.0)).filter(
        Unit.project_id == project_id, Unit.status.in_(_RENTED)).scalar() or 0.0
    return {
        "unit_total": total, "by_status": by_status, "rented": rented,
        "vacant": by_status.get("空置", 0),
        "occupancy_rate": round(rented / total, 4) if total else 0.0,
        "area_total": _round(total_area), "area_rented": _round(rented_area),
        "area_occupancy_rate": round(rented_area / total_area, 4) if total_area else 0.0,
    }


def _revenue(db: Session, project_id: int, period: str | None) -> dict:
    q = db.query(Receivable.fee_item,
                 func.coalesce(func.sum(Receivable.amount_due), 0.0),
                 func.coalesce(func.sum(Receivable.amount_received), 0.0),
                 func.coalesce(func.sum(Receivable.arrears), 0.0)).filter(
        Receivable.project_id == project_id)
    if period:
        q = q.filter(Receivable.period == period)
    by_item_due, by_item_recv = {}, {}
    due = recv = arrears = 0.0
    for item, d, r, a in q.group_by(Receivable.fee_item).all():
        by_item_due[item] = _round(d); by_item_recv[item] = _round(r)
        due += d; recv += r; arrears += a
    # 账龄分布（欠租）
    aging = dict(db.query(Receivable.aging, func.coalesce(func.sum(Receivable.arrears), 0.0))
                 .filter(Receivable.project_id == project_id, Receivable.arrears > 0)
                 .group_by(Receivable.aging).all())
    return {
        "revenue_due_total": _round(due), "revenue_received_total": _round(recv),
        "revenue_due_by_item": by_item_due, "revenue_received_by_item": by_item_recv,
        "rent_received": by_item_recv.get("租金", 0.0),
        "mgmt_fee_received": by_item_recv.get("物业费", 0.0),
        "collect_rate": round(recv / due, 4) if due else 0.0,
        "arrears_total": _round(arrears),
        "arrears_by_aging": {k: _round(v) for k, v in aging.items() if k},
    }


def _cost(db: Session, project_id: int, period: str | None) -> dict:
    q = db.query(ProjectCost.cost_type,
                 func.coalesce(func.sum(ProjectCost.amount), 0.0)).filter(
        ProjectCost.project_id == project_id)
    if period:
        q = q.filter(ProjectCost.period == period)
    by_type = {t: _round(a) for t, a in q.group_by(ProjectCost.cost_type).all()}
    return {"cost_total": _round(sum(by_type.values())), "cost_by_type": by_type}


def _lease_risk(db: Session, project_id: int) -> dict:
    today = date.today()
    soon = today + timedelta(days=90)
    active = db.query(func.count()).filter(
        Lease.project_id == project_id, Lease.lease_status == "生效").scalar() or 0
    expiring = db.query(func.count()).filter(
        Lease.project_id == project_id, Lease.lease_status == "生效",
        Lease.end_date.isnot(None), Lease.end_date <= soon,
        Lease.end_date >= today).scalar() or 0
    return {"active_leases": active, "expiring_90d": expiring}


def project_operations(db: Session, project_id: int, period: str | None = None) -> dict:
    occ = _occupancy(db, project_id)
    rev = _revenue(db, project_id, period)
    cost = _cost(db, project_id, period)
    noi = _round(rev["revenue_received_total"] - cost["cost_total"])
    # 租金坪效（元/㎡/月）：租金实收 / 已租计租面积（period 内）
    ppsm = 0.0
    if occ["area_rented"] and rev["rent_received"]:
        ppsm = round(rev["rent_received"] / occ["area_rented"], 1)
    return {
        "project_id": project_id, "period": period or "全部",
        "occupancy": occ, "revenue": rev, "cost": cost,
        "noi": noi,
        "noi_margin": round(noi / rev["revenue_received_total"], 4)
        if rev["revenue_received_total"] else 0.0,
        "rent_psm_month": ppsm,
        "lease": _lease_risk(db, project_id),
    }


def portfolio_operations(db: Session, period: str | None = None) -> dict:
    """多项目组合总览（首页 · 领导视角）。"""
    projects = db.query(Project).filter(Project.is_deleted.is_(False)).all()
    rows = []
    tot = {"revenue_due": 0.0, "revenue_recv": 0.0, "cost": 0.0, "noi": 0.0,
           "arrears": 0.0, "units": 0, "rented": 0}
    rev_struct, cost_struct = {}, {}
    for p in projects:
        op = project_operations(db, p.id, period)
        rows.append({
            "project_id": p.id, "project_code": p.project_code, "project_name": p.project_name,
            "occupancy_rate": op["occupancy"]["occupancy_rate"],
            "unit_total": op["occupancy"]["unit_total"],
            "revenue_received": op["revenue"]["revenue_received_total"],
            "cost": op["cost"]["cost_total"], "noi": op["noi"],
            "collect_rate": op["revenue"]["collect_rate"],
            "arrears": op["revenue"]["arrears_total"],
            "rent_psm_month": op["rent_psm_month"],
        })
        tot["revenue_due"] += op["revenue"]["revenue_due_total"]
        tot["revenue_recv"] += op["revenue"]["revenue_received_total"]
        tot["cost"] += op["cost"]["cost_total"]
        tot["noi"] += op["noi"]
        tot["arrears"] += op["revenue"]["arrears_total"]
        tot["units"] += op["occupancy"]["unit_total"]
        tot["rented"] += op["occupancy"]["rented"]
        for k, v in op["revenue"]["revenue_received_by_item"].items():
            rev_struct[k] = _round(rev_struct.get(k, 0.0) + v)
        for k, v in op["cost"]["cost_by_type"].items():
            cost_struct[k] = _round(cost_struct.get(k, 0.0) + v)

    rows.sort(key=lambda r: r["noi"], reverse=True)
    kpi = {
        "project_count": len(projects), "unit_total": tot["units"],
        "occupancy_rate": round(tot["rented"] / tot["units"], 4) if tot["units"] else 0.0,
        "revenue_received": _round(tot["revenue_recv"]),
        "cost": _round(tot["cost"]), "noi": _round(tot["noi"]),
        "collect_rate": round(tot["revenue_recv"] / tot["revenue_due"], 4)
        if tot["revenue_due"] else 0.0,
        "arrears": _round(tot["arrears"]),
    }
    return {
        "period": period or "全部", "kpi": kpi, "projects": rows,
        "revenue_structure": rev_struct, "cost_structure": cost_struct,
        "arrears_top": sorted(rows, key=lambda r: r["arrears"], reverse=True)[:5],
    }
