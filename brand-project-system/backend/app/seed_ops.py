"""按项目业态生成"出租经营台账"示例数据：每个项目≥10个铺位 + 商户/租约/收费 + 月度成本。

用途：让每个项目的经营台账(出租率/收入/NOI/收缴/欠租)都有可展示的示例数字。
幂等：按 unit_code 前缀判重，已达标的项目跳过；可反复运行。
    python -m app.seed_ops
"""
from __future__ import annotations

import random
from datetime import date

from .database import SessionLocal


def _add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, min(d.day, 28))


# 让示例租约到期日打散在未来 ~8 个季度（12~32 个月），路线图才有分批层次
def _staggered_end(start: date, key: int) -> date:
    return _add_months(start, 12 + (key * 5) % 21)
from .models import (
    Lease, Merchant, Project, ProjectCost, Receivable, Unit, UnitAdjustmentPlan,
)
from .services import classification

MIN_UNITS = 12          # 每个项目至少铺位数（≥10 的要求）
PERIOD = "2026-09"
_SRC = "ops_sample"

# 业态 → (计租均价 元/㎡/月, 单铺面积区间, 商户样例[(名称, 业态)])
CATEGORY = {
    "体育场馆商业": (160, (100, 500), [
        ("迪卡侬运动仓店", "运动户外"), ("安踏超级旗舰", "服饰鞋包"), ("李宁运动生活", "服饰鞋包"),
        ("超级猩猩健身", "运动健身"), ("乐刻运动", "运动健身"), ("尤尼克斯羽球馆", "球类场馆"),
        ("星巴克臻选", "咖啡"), ("必胜客欢乐餐厅", "西式正餐"), ("蜜雪冰城", "茶饮"),
        ("华莱士", "中式快餐"), ("运动康复中心", "生活服务"), ("赛事主题餐吧", "西式正餐"),
    ]),
    "购物中心": (220, (50, 800), [
        ("优衣库", "快时尚"), ("名创优品", "综合零售"), ("海底捞火锅", "火锅"),
        ("西西弗书店", "文化娱乐"), ("喜茶", "茶饮"), ("星巴克", "咖啡"),
        ("孩子王", "母婴用品"), ("屈臣氏", "美妆个护"), ("华为授权体验店", "手机数码"),
        ("小米之家", "手机数码"), ("肯德基", "西式快餐"), ("周大福", "鞋履箱包"),
    ]),
    "商业街区": (150, (60, 300), [
        ("星巴克", "咖啡"), ("喜茶", "茶饮"), ("瑞幸咖啡", "咖啡"), ("外婆家", "中式正餐"),
        ("费大厨", "中式正餐"), ("鲜花小铺", "生活服务"), ("潮玩集合店", "综合零售"),
        ("精酿啤酒馆", "西式正餐"), ("烘焙工坊", "烘焙甜品"), ("茶颜悦色", "茶饮"),
        ("理发造型", "美发"), ("文创集市", "文化娱乐"),
    ]),
    "社区商业": (90, (40, 220), [
        ("永辉超市mini", "综合零售"), ("美宜佳便利店", "综合零售"), ("菜鸟驿站", "便民服务"),
        ("社区药房", "生活服务"), ("百果园", "综合零售"), ("张亮麻辣烫", "中式快餐"),
        ("正新鸡排", "中式快餐"), ("干洗生活馆", "洗衣"), ("宠物生活馆", "生活服务"),
        ("早餐工坊", "中式快餐"), ("理发店", "美发"), ("水果店", "综合零售"),
    ]),
    "写字楼或公寓配套": (120, (30, 150), [
        ("瑞幸咖啡", "咖啡"), ("星巴克", "咖啡"), ("7-11便利店", "综合零售"),
        ("沙拉轻食", "西式快餐"), ("便当食堂", "中式快餐"), ("健身工作室", "运动健身"),
        ("图文快印", "便民服务"), ("银行网点", "便民服务"), ("茶饮吧", "茶饮"),
        ("水果便利", "综合零售"), ("轻食沙拉", "西式快餐"), ("咖啡自习室", "咖啡"),
    ]),
    "文旅商业": (130, (50, 300), [
        ("非遗文创工坊", "文化娱乐"), ("城市礼物纪念品", "综合零售"), ("山城茶馆", "茶饮"),
        ("民宿前台", "生活服务"), ("特色咖啡馆", "咖啡"), ("江湖菜馆", "中式正餐"),
        ("手作体验店", "文化娱乐"), ("网红打卡甜品", "烘焙甜品"), ("汉服体验馆", "文化娱乐"),
        ("山城小吃集", "中式快餐"), ("精品书吧", "文化娱乐"), ("文旅直播间", "文化娱乐"),
    ]),
}
_DEFAULT = ("商业街区", CATEGORY["商业街区"])


def _cfg(ptype: str):
    return CATEGORY.get(ptype, _DEFAULT[1])


def _floor_of(i: int) -> str:
    return ["B1", "L1", "L1", "L2", "L2", "L3"][i % 6]


def generate_for_project(db, p: Project, rng: random.Random) -> int:
    existing = db.query(Unit).filter(Unit.project_id == p.id).count()
    need = MIN_UNITS - existing
    if need <= 0:
        return 0
    psm, (amin, amax), tenants = _cfg(p.project_type)
    occ = rng.uniform(0.6, 0.85)
    n_rented_target = max(1, round(need * occ))
    created = 0
    for i in range(need):
        area = round(rng.uniform(amin, amax), 1)
        code = f"{p.project_code}-U{existing + i + 1:02d}"
        leased = i < n_rented_target
        status = "自营" if (leased and i == 0) else ("在租" if leased else "空置")
        u = Unit(unit_code=code, project_id=p.id, floor=_floor_of(i), status=status,
                 unit_type="商铺", rentable_area_m2=area,
                 building_area_m2=round(area * 1.2, 1), source_system=_SRC)
        db.add(u); db.flush()
        created += 1
        if status == "空置":
            continue
        name, fmt = tenants[i % len(tenants)]
        seq = existing + i + 1
        m = Merchant(merchant_code=f"MER-{p.project_code}-{seq:02d}", name=f"{name}·{p.project_short_name or p.project_name}",
                     project_id=p.id, unit_id=u.id, business_format=fmt,
                     open_date=date(2025, 6, 1), operating_status="在营", source_system=_SRC)
        db.add(m); db.flush()
        base_rent = round(area * psm, 0)
        mgmt = round(area * 22, 0)
        util = round(area * 8, 0)
        lease = Lease(lease_code=f"LS-{p.project_code}-{seq:02d}",
                      contract_no=f"HT-{p.project_code}-{seq:03d}", merchant_id=m.id,
                      project_id=p.id, unit_id=u.id, start_date=date(2025, 6, 1),
                      end_date=_staggered_end(date(2025, 6, 1), seq + (p.id * 3)),
                      rent_mode="固定租金", base_rent=base_rent,
                      management_fee=mgmt, deposit=base_rent * 3, lease_status="生效",
                      source_system=_SRC)
        db.add(lease); db.flush()
        # 约 1/6 的租户本期有部分欠租
        has_arrear = (i % 6 == 2)
        for fee, due in [("租金", base_rent), ("物业费", mgmt), ("水电代收", util)]:
            recv = round(due * 0.6, 0) if (has_arrear and fee == "租金") else due
            arr = round(due - recv, 2)
            db.add(Receivable(
                receivable_code=f"REC-{p.project_code}-{seq:02d}-{fee}", lease_id=lease.id,
                project_id=p.id, fee_item=fee, period=PERIOD, due_date=date(2026, 9, 5),
                amount_due=due, amount_received=recv, arrears=arr,
                overdue_days=25 if arr > 0 else 0, aging="0-30" if arr > 0 else "未逾期",
                collect_status="催收中" if arr > 0 else "已结清", owner="招商运营部",
                source_system=_SRC))

    # 月度成本（按已招商铺位计租面积估算，NOI 落在合理区间）
    if not db.query(ProjectCost).filter(ProjectCost.project_id == p.id,
                                        ProjectCost.period == PERIOD).first():
        rented_area = db.query(Unit).filter(
            Unit.project_id == p.id, Unit.status.in_(["在租", "自营"])).all()
        base = sum((u.rentable_area_m2 or 0) for u in rented_area)
        for ctype, rate in [("物业成本", 12), ("水电能耗", 9), ("人力", 14),
                            ("维修", 4), ("其他", 3)]:
            db.add(ProjectCost(project_id=p.id, period=PERIOD, cost_type=ctype,
                               amount=round(base * rate, 0), remark=_SRC))
    return created


def _seed_adjustment_samples(db, p: Project, rng: random.Random) -> int:
    """给项目造几条业态调改计划示例（空置→新招商 / 在租→置换 / 改造升级）。幂等。"""
    if db.query(UnitAdjustmentPlan).filter(UnitAdjustmentPlan.project_id == p.id).first():
        return 0
    psm, _area, tenants = _cfg(p.project_type)
    units = db.query(Unit).filter(Unit.project_id == p.id).all()
    vacant = [u for u in units if u.status == "空置"]
    rented = [u for u in units if u.status in ("在租", "自营")]
    made = 0

    def _fmt(i: int) -> str:
        return tenants[i % len(tenants)][1]

    if vacant:
        u = vacant[0]
        db.add(UnitAdjustmentPlan(
            project_id=p.id, unit_id=u.id, action="新招商", from_format=None,
            to_format=_fmt(1), expected_rent_psm=round(psm * 1.05, 1),
            plan_status="审批中", plan_date=date(2026, 12, 31), owner="招商运营部",
            reason="空置铺位引入目标业态填补"))
        made += 1
    if len(rented) >= 1:
        u = rented[-1]
        db.add(UnitAdjustmentPlan(
            project_id=p.id, unit_id=u.id, action="置换", from_format=None,
            to_format=_fmt(3), expected_rent_psm=round(psm * 1.15, 1),
            plan_status="草案", plan_date=date(2027, 3, 31), owner="招商运营部",
            reason="低效商户置换为更高坪效业态"))
        made += 1
    if len(rented) >= 2:
        u = rented[-2]
        db.add(UnitAdjustmentPlan(
            project_id=p.id, unit_id=u.id, action="改造", from_format=None,
            to_format=_fmt(5), expected_rent_psm=round(psm * 1.10, 1),
            plan_status="已定", plan_date=date(2026, 11, 30), owner="工程部",
            reason="铺位改造升级，提升租金坪效"))
        made += 1
    return made


def restagger_lease_expiries(db) -> int:
    """把存量示例租约里"到期日都一样"的情况打散，供路线图分批演示。仅动 ops_sample/seed 来源。"""
    changed = 0
    leases = db.query(Lease).filter(Lease.lease_status == "生效").all()
    for ll in leases:
        start = ll.start_date or date(2025, 6, 1)
        new_end = _staggered_end(start, (ll.id or 0) + (ll.project_id or 0) * 3)
        if ll.end_date != new_end:
            ll.end_date = new_end
            changed += 1
    db.commit()
    return changed


def seed_operation_samples(db) -> dict:
    projects = db.query(Project).filter(Project.is_deleted.is_(False)).all()
    total_units = 0
    touched = 0
    plans = 0
    for p in projects:
        rng = random.Random(f"ops-{p.project_code}")   # 确定性
        n = generate_for_project(db, p, rng)
        if n:
            touched += 1
            total_units += n
        db.flush()
        plans += _seed_adjustment_samples(db, p, rng)
    classification.recompute_all_statuses(db)   # 有活动的项目→已开业
    db.commit()
    return {"projects_touched": touched, "units_created": total_units,
            "adjustment_plans": plans, "project_total": len(projects)}


if __name__ == "__main__":
    db = SessionLocal()
    try:
        result = seed_operation_samples(db)
        print(f"✅ 台账示例生成完成：{result}")
    finally:
        db.close()
