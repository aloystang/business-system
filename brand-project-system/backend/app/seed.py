"""初始化 + 种子：管理员 + 新盛真实项目(GCJ-02) + 贴合招商的模拟品牌。
    python -m app.seed
"""
from __future__ import annotations

from .config import get_settings
from .database import Base, SessionLocal, engine
from datetime import date

from .models import (
    Brand, BrandCategory, BrandExpansion, BrandTag, Dictionary, Lease, Merchant, Permission,
    Project, ProjectCost, ProjectLocation, ProjectTag, Receivable, Role, RolePermission,
    Unit, User, UserRole,
)
from .security import hash_password
from .services import classification

ROLES = [
    ("admin", "系统管理员"), ("data_admin", "数据与字典管理员"),
    ("brand_bd", "招商拓展经理"), ("project_mgr", "项目招商经理"),
    ("executive", "管理层/决策者"), ("viewer", "受限查看者"),
]
PERMISSIONS = [
    ("brand:read", "品牌查看", "brand", "read"), ("brand:write", "品牌维护", "brand", "write"),
    ("project:read", "项目查看", "project", "read"), ("project:write", "项目维护", "project", "write"),
    ("map:read", "地图查看", "map", "read"), ("map:sensitive", "敏感项目查看", "map", "sensitive"),
    ("match:read", "匹配查看", "match", "read"), ("match:write", "匹配与候选", "match", "write"),
    ("import:run", "Excel导入", "import", "import"), ("dict:write", "字典规则维护", "dict", "write"),
    ("user:manage", "用户角色权限", "user", "write"), ("log:read", "操作日志", "log", "read"),
]

# 角色 → 权限点矩阵（admin 主角色代码另有直通，不依赖此表）
ALL_PERM_CODES = [p[0] for p in PERMISSIONS]
ROLE_PERMS = {
    "admin": ALL_PERM_CODES,
    "data_admin": ["brand:read", "brand:write", "project:read", "project:write",
                   "dict:write", "import:run", "log:read"],
    "brand_bd": ["brand:read", "brand:write", "project:read", "map:read",
                 "match:read", "match:write"],
    "project_mgr": ["project:read", "project:write", "brand:read", "map:read",
                    "match:read", "match:write"],
    "executive": ["brand:read", "project:read", "map:read", "map:sensitive",
                  "match:read", "log:read"],
    "viewer": ["brand:read", "project:read", "map:read", "match:read"],
}

DICTS = {
    "project_type": ["体育场馆商业", "购物中心", "商业街区", "社区商业", "文旅商业",
                     "交通枢纽商业", "写字楼或公寓配套", "存量改造项目", "其他"],
    "project_status": ["筹备", "招商中", "已开业", "改造中", "暂停", "失效"],
    "geocoding_status": ["自动定位", "人工确认", "人工修正", "定位失败", "待定位"],
    "operating_status": ["正常经营", "暂停营业", "收缩", "已关闭"],
    "info_confidence": ["已确认", "阶段方案", "待确认", "方法参考"],
    "cooperation_mode": ["直租", "联营", "扣点", "保底+提成", "其他"],
}
BRAND_TAGS = ["主力店", "全国连锁", "区域连锁", "本地连锁", "潮流或网红品牌", "首店资源",
              "体育相关品牌", "赛事配套品牌", "生活服务品牌", "其他"]
PROJECT_TAGS = ["优先项目", "重点跟进", "高匹配机会"]

# 三级业态树：{一级: {二级: [三级, ...]}}
CATEGORY_TREE = {
    "零售": {
        "服饰鞋包": ["运动户外", "快时尚", "鞋履箱包"],
        "生活百货": ["综合零售", "家居家纺", "美妆个护"],
        "数码电器": ["手机数码", "家用电器"],
    },
    "餐饮": {
        "正餐": ["中式正餐", "西式正餐", "火锅"],
        "快餐简餐": ["中式快餐", "西式快餐"],
        "饮品甜点": ["咖啡", "茶饮", "烘焙甜品"],
    },
    "文体娱乐": {
        "运动健身": ["健身房", "运动培训", "球类场馆"],
        "文化娱乐": ["影院", "livehouse", "电玩游艺"],
    },
    "亲子教育": {
        "儿童零售": ["母婴用品", "玩具"],
        "儿童成长": ["早教", "儿童游乐", "素质培训"],
    },
    "生活服务": {
        "美容美发": ["美发", "美甲美睫", "美容SPA"],
        "便民服务": ["洗衣", "维修", "通讯营业厅"],
    },
}

settings = get_settings()

# 真实项目取自新盛资产清单；坐标为两江新区一带 GCJ-02 近似值（演示用）。
PROJECTS = [
    # code, name, short, type, status, city, district, address, lng, lat, geostatus,
    #   business_area, target_formats, core_customers, coop_will, grade, sensitive
    ("XS-PRJ-0001", "重庆龙兴足球场", "龙兴足球场", "体育场馆商业", "招商中",
     "重庆市", "两江新区", "重庆两江新区龙兴镇", 106.7315, 29.6902, "人工确认",
     160958, "零售;文体娱乐;餐饮;亲子教育", "球迷;运动家庭", "强", "A", False),
    ("XS-PRJ-0002", "两江悦荟城", "悦荟城", "购物中心", "招商中",
     "重庆市", "两江新区", "重庆两江新区龙兴镇", 106.7208, 29.6688, "自动定位",
     17530, "餐饮;零售;亲子教育;生活服务", "片区家庭", "较强", "B", False),
    ("XS-PRJ-0003", "两江云中街", "云中街", "商业街区", "已开业",
     "重庆市", "两江新区", "重庆两江新区水土街道", 106.6905, 29.7602, "自动定位",
     23898, "餐饮;零售;生活服务", "街区客群", "一般", "B", False),
    ("XS-PRJ-0004", "鱼复星光", "鱼复星光", "社区商业", "招商中",
     "重庆市", "两江新区", "重庆两江新区鱼嘴镇", 106.7788, 29.6205, "自动定位",
     28212, "零售;餐饮;生活服务", "社区家庭", "一般", "C", False),
    ("XS-PRJ-0005", "三洞桥PARK", "三洞桥", "商业街区", "招商中",
     "重庆市", "两江新区", "重庆两江新区江北嘴", 106.5450, 29.6060, "自动定位",
     28638, "餐饮;零售;文体娱乐", "都市客群", "较强", "B", False),
    ("XS-PRJ-0006", "江北嘴网球馆", "网球馆", "体育场馆商业", "招商中",
     "重庆市", "两江新区", "重庆两江新区江北嘴", 106.5480, 29.6080, "自动定位",
     3432, "文体娱乐;餐饮", "运动人群", "较强", "B", False),
    ("XS-PRJ-0007", "h87御临河商业", "御临河", "商业街区", "筹备",
     "重庆市", "两江新区", "重庆两江新区龙兴镇", None, None, "定位失败",
     5584, "餐饮;零售", "", "一般", None, False),
]

# (code, name, short, l1, l2, l3, tags, coop_intent, grade,
#  target_cities, acceptable_types, accept_stadium, area_min, area_max, needs_gas)
BRANDS = [
    ("XS-BRD-0001", "迪卡侬", "迪卡侬", "零售", "服饰鞋包", "运动户外",
     "全国连锁;体育相关品牌;主力店;首店资源", "较强", "A",
     "重庆;成都", "体育场馆商业;购物中心;商业街区", True, 800, 2500, False),
    ("XS-BRD-0002", "超级猩猩", "超级猩猩", "文体娱乐", "运动健身", "健身房",
     "区域连锁;体育相关品牌;潮流或网红品牌", "强", "B",
     "重庆", "体育场馆商业;购物中心", True, 300, 600, False),
    ("XS-BRD-0003", "海底捞", "海底捞", "餐饮", "正餐", "火锅",
     "全国连锁;主力店", "一般", "A",
     "重庆", "购物中心;商业街区", False, 600, 1200, True),
    ("XS-BRD-0004", "孩子王", "孩子王", "亲子教育", "儿童零售", "母婴用品",
     "全国连锁;主力店", "较强", "B",
     "重庆", "购物中心", False, 500, 1500, False),
    ("XS-BRD-0005", "名创优品", "名创优品", "零售", "生活百货", "综合零售",
     "全国连锁", "较强", "B",
     "重庆", "购物中心;商业街区;社区商业", False, 150, 400, False),
    ("XS-BRD-0006", "瑞幸咖啡", "瑞幸", "餐饮", "饮品甜点", "咖啡",
     "全国连锁;首店资源", "强", "A",
     "重庆", "购物中心;商业街区;社区商业;体育场馆商业", True, 40, 120, False),
]


def _seed_category_tree(db) -> None:
    """播三级业态树 brand_categories（一级→二级→三级，逐级 parent_id）。"""
    sort1 = 0
    for l1, subs in CATEGORY_TREE.items():
        sort1 += 1
        n1 = BrandCategory(parent_id=None, level=1, code=f"L1-{sort1:02d}",
                           name=l1, sort_no=sort1)
        db.add(n1); db.flush()
        sort2 = 0
        for l2, leaves in subs.items():
            sort2 += 1
            n2 = BrandCategory(parent_id=n1.id, level=2, code=f"{n1.code}-{sort2:02d}",
                               name=l2, sort_no=sort2)
            db.add(n2); db.flush()
            for sort3, l3 in enumerate(leaves, 1):
                db.add(BrandCategory(parent_id=n2.id, level=3,
                                     code=f"{n2.code}-{sort3:02d}", name=l3, sort_no=sort3))


def _seed_leasing(db) -> None:
    """龙兴足球场(XS-PRJ-0001) 出租经营台账样例：铺位/商户/租约/收费/成本。"""
    p = db.query(Project).filter(Project.project_code == "XS-PRJ-0001").first()
    if not p:
        return
    dkl = db.query(Brand).filter(Brand.brand_code == "XS-BRD-0001").first()
    cjj = db.query(Brand).filter(Brand.brand_code == "XS-BRD-0002").first()

    # 铺位（计租面积/状态）
    units_def = [
        ("1-101", "L1", "在租", 180.0), ("1-102", "L1", "空置", 120.0),
        ("1-103", "L1", "空置", 95.0), ("1-105", "L1", "在租", 220.0),
        ("2-201", "L2", "自营", 320.0), ("2-202", "L2", "空置", 260.0),
        ("B-001", "B1", "空置", 400.0),
    ]
    units = {}
    for code, fl, st, area in units_def:
        u = Unit(unit_code=code, project_id=p.id, floor=fl, status=st,
                 rentable_area_m2=area, building_area_m2=round(area * 1.2, 1),
                 unit_type="商铺", source_system="seed")
        db.add(u); db.flush(); units[code] = u

    # 商户 + 租约 + 收费（账期 2026-08）；乡村基含欠租案例
    #  (商户码, 名, 品牌, 铺位, 业态, 基础租金, 物业费, 水电代收, 租金实收)
    mdef = [
        ("MER-0001", "迪卡侬龙兴运动店", dkl, "1-101", "零售", 54000, 4500, 3200, 54000),
        ("MER-0002", "乡村基龙兴店", None, "1-105", "餐饮", 40000, 3000, 2100, 35000),
        ("MER-0003", "超级猩猩龙兴店", cjj, "2-201", "休闲娱乐", 28000, 2500, 1800, 28000),
    ]
    for i, (mc, name, brand, ucode, fmt, rent, mgmt, util, rent_recv) in enumerate(mdef, 1):
        u = units[ucode]
        m = Merchant(merchant_code=mc, name=name, brand_id=brand.id if brand else None,
                     project_id=p.id, unit_id=u.id, business_format=fmt,
                     open_date=date(2025, 10, 1), operating_status="在营", source_system="seed")
        db.add(m); db.flush()
        lease = Lease(lease_code=f"LEASE-{i:04d}", contract_no=f"HT-LX-2025-{i:03d}",
                      merchant_id=m.id, project_id=p.id, unit_id=u.id,
                      start_date=date(2025, 10, 1), end_date=date(2030, 9, 30),
                      rent_mode="固定租金", base_rent=rent, management_fee=mgmt,
                      deposit=rent * 3, lease_status="生效", source_system="seed")
        db.add(lease); db.flush()
        # 三个费项
        for fee, due_amt, recv_amt in [("租金", rent, rent_recv), ("物业费", mgmt, mgmt),
                                        ("水电代收", util, util)]:
            arrears = round(max(due_amt - recv_amt, 0.0), 2)
            db.add(Receivable(
                receivable_code=f"REC-{i:04d}-{fee}", lease_id=lease.id, project_id=p.id,
                fee_item=fee, period="2026-08", due_date=date(2026, 8, 5),
                amount_due=due_amt, amount_received=recv_amt, arrears=arrears,
                overdue_days=26 if arrears > 0 else 0,
                aging="0-30" if arrears > 0 else "未逾期",
                collect_status="催收中" if arrears > 0 else "已结清",
                owner="王收", source_system="seed"))

    # 项目月度成本（2026-08）
    for ctype, amt in [("物业成本", 18000), ("水电能耗", 9000), ("人力", 25000),
                       ("维修", 4000), ("其他", 3000)]:
        db.add(ProjectCost(project_id=p.id, period="2026-08", cost_type=ctype, amount=amt))


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Role).first():
            for code, name in ROLES:
                db.add(Role(code=code, name=name))
            for code, name, res, act in PERMISSIONS:
                db.add(Permission(code=code, name=name, resource=res, action=act))
            db.flush()
            # 角色→权限点结算表
            role_by_code = {r.code: r.id for r in db.query(Role).all()}
            perm_by_code = {p.code: p.id for p in db.query(Permission).all()}
            for rcode, pcodes in ROLE_PERMS.items():
                for pcode in pcodes:
                    db.add(RolePermission(role_id=role_by_code[rcode],
                                          permission_id=perm_by_code[pcode]))

        if not db.query(User).filter(User.username == settings.admin_username).first():
            admin = User(username=settings.admin_username, display_name="系统管理员",
                         password_hash=hash_password(settings.admin_password), role="admin")
            db.add(admin)
            db.flush()
            admin_role = db.query(Role).filter(Role.code == "admin").first()
            if admin_role:
                db.add(UserRole(user_id=admin.id, role_id=admin_role.id))

        if not db.query(Dictionary).first():
            for dtype, labels in DICTS.items():
                for i, label in enumerate(labels, 1):
                    db.add(Dictionary(dict_type=dtype, code=label, label=label, sort_no=i))
            for i, name in enumerate(BRAND_TAGS, 1):
                db.add(BrandTag(code=name, name=name, sort_no=i))
            for i, name in enumerate(PROJECT_TAGS, 1):
                db.add(ProjectTag(code=name, name=name, sort_no=i))

        if not db.query(BrandCategory).first():
            _seed_category_tree(db)
            db.flush()
            # 回填此前只有一级业态的存量种子品牌
            for row in BRANDS:
                code, l1, l2, l3 = row[0], row[3], row[4], row[5]
                b = db.query(Brand).filter(Brand.brand_code == code).first()
                if b and not b.l2_category:
                    b.l1_category, b.l2_category, b.l3_category = l1, l2, l3

        if not db.query(Project).first():
            for (code, name, short, ptype, status, city, district, addr, lng, lat, gstatus,
                 barea, tfmt, cust, will, grade, sens) in PROJECTS:
                p = Project(project_code=code, project_name=name, project_short_name=short,
                            project_type=ptype, project_status=status, operator="新盛公司",
                            business_area_m2=barea, leasable_area_m2=barea,
                            target_formats=tfmt, core_customers=cust, cooperation_will=will,
                            leasing_stage="招商启动", grade=grade, is_sensitive=sens)
                db.add(p); db.flush()
                db.add(ProjectLocation(project_id=p.id, province="重庆市", city=city,
                                       district=district, address=addr, longitude=lng,
                                       latitude=lat, coordinate_system="GCJ-02",
                                       geocoding_status=gstatus,
                                       geocoding_provider="amap" if lng else None))

        if not db.query(Brand).first():
            for (code, name, short, l1, l2, l3, tags, coop, grade, tcities, atypes, stadium,
                 amin, amax, gas) in BRANDS:
                b = Brand(brand_code=code, brand_name=name, brand_short_name=short,
                          l1_category=l1, l2_category=l2, l3_category=l3, tags=tags,
                          operating_status="正常经营",
                          cooperation_intent=coop, grade=grade, hq_city="—")
                db.add(b); db.flush()
                db.add(BrandExpansion(brand_id=b.id, target_cities=tcities,
                                      acceptable_project_types=atypes,
                                      accept_stadium_commercial=stadium, accept_new_project=True,
                                      area_min=amin, area_max=amax, needs_gas=gas))

        if not db.query(Unit).first():
            _seed_leasing(db)

        # 为每个项目按业态补齐经营台账示例（≥10 铺位 + 商户/租约/收费 + 月度成本），幂等
        db.flush()
        from .seed_ops import seed_operation_samples
        ops_result = seed_operation_samples(db)   # 内部会重分状态并 commit

        db.commit()
        print("✅ 初始化完成：管理员 + 真实项目 + 模拟品牌 + 全项目经营台账示例。")
        print(f"   台账示例：{ops_result}")
        print(f"   登录：{settings.admin_username} / {settings.admin_password}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
