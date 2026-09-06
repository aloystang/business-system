"""业态 / 状态口径：统一校验与自动重分。

设计要点（对齐甲方沟通）：
- 品牌业态是一棵三级树（brand_categories）。品牌落位时校验 l1/l2/l3 是否为
  树上一条合法路径；树为空时不阻断（视为未启用分类校验）。
- 项目类型 / 状态是字典枚举（dictionaries），写入时按字典校验。
- 项目状态支持“数据驱动自动重分”：有生效租约或在营商户 → 已开业；
  否则回落招商中；筹备/改造中/暂停/失效 等人工状态不被自动覆盖。
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import BrandCategory, Dictionary, Lease, Merchant, Project, Unit

# 有活动即视为“已开业”的判定口径
_ACTIVE_LEASE_STATUS = "生效"
_ACTIVE_MERCHANT_STATUS = "在营"
_ACTIVE_UNIT_STATUS = ("在租", "自营")

# 自动重分只在这两个状态之间流动，其余人工状态（筹备/改造中/暂停/失效）保持不动
STATUS_OPERATING = "已开业"
STATUS_LEASING = "招商中"
_AUTO_MANAGED_STATUSES = {STATUS_OPERATING, STATUS_LEASING}


class ClassificationError(ValueError):
    """业态/状态口径校验失败。"""


# ---------- 字典枚举校验 ----------

def validate_dict_value(db: Session, dict_type: str, value: str | None) -> None:
    """value 必须是 dictionaries 里该类型的有效 code；字典该类型为空时不阻断。"""
    if value is None or value == "":
        return
    total = db.query(Dictionary).filter(
        Dictionary.dict_type == dict_type, Dictionary.is_active.is_(True)).count()
    if total == 0:
        return  # 该字典未启用，跳过校验
    exists = db.query(Dictionary).filter(
        Dictionary.dict_type == dict_type, Dictionary.code == value,
        Dictionary.is_active.is_(True)).first()
    if not exists:
        raise ClassificationError(f"{dict_type} 取值非法：{value}（不在字典枚举内）")


def validate_project_type(db: Session, project_type: str | None) -> None:
    validate_dict_value(db, "project_type", project_type)


def validate_project_status(db: Session, project_status: str | None) -> None:
    validate_dict_value(db, "project_status", project_status)


# ---------- 品牌三级业态树校验 ----------

def build_format_index(db: Session) -> dict[str, str]:
    """业态名 → 其一级(L1)根业态名 的映射，供匹配引擎按树归类。"""
    nodes = db.query(BrandCategory).filter(BrandCategory.is_active.is_(True)).all()
    by_id = {n.id: n for n in nodes}

    def root_name(n) -> str:
        seen = set()
        while n.parent_id and n.parent_id in by_id and n.id not in seen:
            seen.add(n.id)
            n = by_id[n.parent_id]
        return n.name

    return {n.name: root_name(n) for n in nodes}


def _find_category(db: Session, name: str, level: int, parent_id: int | None):
    q = db.query(BrandCategory).filter(
        BrandCategory.name == name, BrandCategory.level == level,
        BrandCategory.is_active.is_(True))
    if parent_id is not None:
        q = q.filter(BrandCategory.parent_id == parent_id)
    return q.first()


def validate_brand_category(db: Session, l1: str | None, l2: str | None,
                            l3: str | None) -> None:
    """校验 l1/l2/l3 为业态树上一条合法路径（逐级父子）。

    - 树为空 → 不阻断（视为未启用业态校验）。
    - 只校验已提供的层级；但不允许“跳级”（给了 l3 却缺 l2、给了 l2 却缺 l1）。
    """
    if db.query(BrandCategory).filter(BrandCategory.is_active.is_(True)).count() == 0:
        return

    if l3 and not l2 or l2 and not l1:
        raise ClassificationError("业态层级不完整：三级业态必须自 一级→二级→三级 逐级填写")

    if not l1:
        return
    n1 = _find_category(db, l1, 1, None)
    if not n1:
        raise ClassificationError(f"一级业态非法：{l1}")
    if not l2:
        return
    n2 = _find_category(db, l2, 2, n1.id)
    if not n2:
        raise ClassificationError(f"二级业态非法：{l2}（不属于 {l1}）")
    if not l3:
        return
    n3 = _find_category(db, l3, 3, n2.id)
    if not n3:
        raise ClassificationError(f"三级业态非法：{l3}（不属于 {l2}）")


# ---------- 项目状态自动重分 ----------

def _has_operation(db: Session, project_id: int) -> bool:
    active_lease = db.query(func.count(Lease.id)).filter(
        Lease.project_id == project_id, Lease.lease_status == _ACTIVE_LEASE_STATUS).scalar()
    if active_lease:
        return True
    active_merchant = db.query(func.count(Merchant.id)).filter(
        Merchant.project_id == project_id,
        Merchant.operating_status == _ACTIVE_MERCHANT_STATUS).scalar()
    if active_merchant:
        return True
    active_unit = db.query(func.count(Unit.id)).filter(
        Unit.project_id == project_id, Unit.status.in_(_ACTIVE_UNIT_STATUS)).scalar()
    return bool(active_unit)


def derive_project_status(db: Session, project: Project) -> str:
    """按经营数据推导项目应有状态。人工特殊状态保持不动。"""
    if project.project_status not in _AUTO_MANAGED_STATUSES:
        return project.project_status
    return STATUS_OPERATING if _has_operation(db, project.id) else STATUS_LEASING


# ---------- 项目类型（业态）细分口径 ----------
# 名称关键词优先，其次面积兜底；命中不了则保持原类型（保守，不乱改）。
_TYPE_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("场馆", "球场", "球馆", "训练场", "网球", "体育"), "体育场馆商业"),
    (("影视城", "文旅", "索道", "景区"), "文旅商业"),
    (("写字楼", "办公", "创谷", "大厦"), "写字楼或公寓配套"),
    (("购物中心", "mall", "MALL"), "购物中心"),
    (("外街", "风情街", "商业街", "步行街", "街区", "PARK", "巷"), "商业街区"),
    (("底商", "社区", "邻里", "商铺", "能量仓", "公园里"), "社区商业"),
]
_AREA_MALL_MIN = 30000.0   # ≥3万㎡ 视为购物中心（体量兜底）
_AREA_COMMUNITY_MAX = 3000.0   # ≤3000㎡ 视为社区商业（体量兜底）


def derive_project_type(name: str, area: float | None, current: str) -> str:
    """按名称关键词 + 面积兜底细分业态；无把握时保持原值。"""
    n = name or ""
    for kws, ptype in _TYPE_KEYWORDS:
        if any(k in n for k in kws):
            # “广场/城”类含糊词不进关键词表，避免误判
            return ptype
    a = area or 0.0
    if a >= _AREA_MALL_MIN:
        return "购物中心"
    if 0 < a <= _AREA_COMMUNITY_MAX:
        return "社区商业"
    return current


def recompute_project_types(db: Session, only_imported: bool = True,
                            apply: bool = False) -> list[dict]:
    """按细分口径重算项目业态。only_imported 时仅动 asset_list* 来源；
    apply=False 只返回建议(dry-run)，True 才落库(不自动 commit)。"""
    q = db.query(Project).filter(Project.is_deleted.is_(False))
    if only_imported:
        q = q.filter(Project.source_system.like("asset_list%"))
    changes: list[dict] = []
    for p in q.all():
        new_type = derive_project_type(p.project_name, p.business_area_m2, p.project_type)
        if new_type != p.project_type:
            changes.append({"project_code": p.project_code, "project_name": p.project_name,
                            "area": p.business_area_m2, "from": p.project_type, "to": new_type})
            if apply:
                p.project_type = new_type
    return changes


def recompute_all_statuses(db: Session) -> list[dict]:
    """批量按经营数据重分项目状态，返回发生变化的明细（不自动 commit）。"""
    changes: list[dict] = []
    for p in db.query(Project).filter(Project.is_deleted.is_(False)).all():
        new_status = derive_project_status(db, p)
        if new_status != p.project_status:
            changes.append({"project_code": p.project_code, "project_name": p.project_name,
                            "from": p.project_status, "to": new_status})
            p.project_status = new_status
    return changes
