"""品牌×项目 匹配引擎：硬门槛 + 八维加权 + 资料覆盖率。

规则口径 = match_rule_versions v1.0（2026-09-04 锁定）。
每维 0/25/50/75/100，缺资料记 None（不按 0，计入覆盖率）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import Brand, Project

RULE_VERSION = "v1.0"
WEIGHTS: dict[str, float] = {
    "format": 0.20,
    "property_condition": 0.20,
    "city_region": 0.15,
    "positioning_customer": 0.15,
    "project_type": 0.10,
    "business_condition": 0.10,
    "expansion_plan": 0.05,
    "cooperation_will": 0.05,
}
GRADE_TIERS = [("优先推进", 85), ("重点储备", 70), ("持续观察", 55), ("暂不匹配", 0)]
COVERAGE_MIN = 60.0
ADJUST_CAP = 10.0
HARD_GATES = ["品牌不接受项目区域或类型", "核心物业条件无法满足"]


@dataclass
class MatchResult:
    dims: dict[str, int | None]
    hard_gate_triggered: bool = False
    hard_gate_reason: str | None = None
    weighted_score: float | None = None
    data_coverage_rate: float = 0.0
    is_formal: bool = True
    match_grade: str = "暂不匹配"
    satisfied: list[str] = field(default_factory=list)
    unsatisfied: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    rule_version: str = RULE_VERSION


def _split(csv: str | None) -> list[str]:
    return [x.strip() for x in (csv or "").split(";") if x.strip()]


def _grade_of(score: float) -> str:
    for name, floor in GRADE_TIERS:
        if score >= floor:
            return name
    return "暂不匹配"


# ---------- 各维度打分（返回 0/25/50/75/100 或 None=缺资料） ----------

def _dim_format(b: Brand, p: Project) -> int | None:
    fmt = b.l1_category
    targets = _split(p.target_formats)
    if not fmt or not targets:
        return None
    if fmt in targets:
        return 100
    # 二级业态或近似
    if b.l2_category and any(b.l2_category in t or t in (b.l2_category or "") for t in targets):
        return 75
    return 25


def _dim_city_region(b: Brand, p: Project) -> int | None:
    cities = _split(b.expansion.target_cities) if b.expansion else []
    city = p.location.city if p.location else None
    if not cities or not city:
        return None
    return 100 if any(c in city or city in c for c in cities) else 25


def _dim_project_type(b: Brand, p: Project) -> int | None:
    types = _split(b.expansion.acceptable_project_types) if b.expansion else []
    if not types:
        return None
    return 100 if p.project_type in types else 0


def _dim_positioning(b: Brand, p: Project) -> int | None:
    # 简化：品牌业态与项目核心客群/定位的契合，用目标业态命中近似
    if not p.core_customers or not b.l1_category:
        return None
    return 75  # 有资料时给中上（真实实现按客群标签匹配，这里演示口径）


def _dim_property(b: Brand, p: Project) -> int | None:
    if not b.expansion or (b.expansion.area_min is None and b.expansion.area_max is None):
        return None
    area = p.leasable_area_m2 or p.business_area_m2
    if area is None:
        return None
    lo, hi = b.expansion.area_min or 0, b.expansion.area_max or 1e12
    # 项目级演示：可招商体量能否容纳品牌需求区间
    return 75 if area >= lo else 25


def _dim_business(b: Brand, p: Project) -> int | None:
    if not p.cooperation_will and not (b.expansion and b.expansion.rent_tolerance):
        return None
    return 50  # 商务条件默认中性，待细化


def _dim_expansion_plan(b: Brand, p: Project) -> int | None:
    cities = _split(b.expansion.target_cities) if b.expansion else []
    city = p.location.city if p.location else None
    if not cities or not city:
        return None
    return 75 if any(c in city or city in c for c in cities) else 50


def _dim_cooperation_will(b: Brand, p: Project) -> int | None:
    m = {"强": 100, "较强": 75, "一般": 50, "弱": 25}
    bw = m.get(b.cooperation_intent or "")
    pw = m.get(p.cooperation_will or "")
    vals = [v for v in (bw, pw) if v is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals) / 25) * 25


def compute(brand: Brand, project: Project) -> MatchResult:
    dims: dict[str, int | None] = {
        "format": _dim_format(brand, project),
        "property_condition": _dim_property(brand, project),
        "city_region": _dim_city_region(brand, project),
        "positioning_customer": _dim_positioning(brand, project),
        "project_type": _dim_project_type(brand, project),
        "business_condition": _dim_business(brand, project),
        "expansion_plan": _dim_expansion_plan(brand, project),
        "cooperation_will": _dim_cooperation_will(brand, project),
    }
    res = MatchResult(dims=dims)

    # 1) 硬门槛
    exp = brand.expansion
    if exp:
        acc_types = _split(exp.acceptable_project_types)
        if acc_types and project.project_type not in acc_types:
            res.hard_gate_triggered = True
            res.hard_gate_reason = f"{HARD_GATES[0]}（不接受 {project.project_type}）"
        if project.project_type == "体育场馆商业" and exp.accept_stadium_commercial is False:
            res.hard_gate_triggered = True
            res.hard_gate_reason = f"{HARD_GATES[0]}（品牌明确不接受体育场馆商业）"
        # 核心物业：需燃气但项目无法满足（演示：项目非餐饮友好时略过，实际按铺位条件）
    if res.hard_gate_triggered:
        res.match_grade = "暂不匹配"
        res.weighted_score = 0.0
        res.data_coverage_rate = round(
            sum(1 for v in dims.values() if v is not None) / len(dims) * 100, 1)
        res.unsatisfied.append(res.hard_gate_reason or "硬门槛")
        return res

    # 2) 加权（缺失维度不计 0；权重重新归一到有资料的维度）
    present = {k: v for k, v in dims.items() if v is not None}
    total_w = sum(WEIGHTS[k] for k in present) or 1.0
    weighted = sum(v * WEIGHTS[k] for k, v in present.items()) / total_w
    res.weighted_score = round(weighted, 2)

    # 3) 覆盖率
    res.data_coverage_rate = round(len(present) / len(dims) * 100, 1)
    res.is_formal = res.data_coverage_rate >= COVERAGE_MIN

    # 4) 定级
    res.match_grade = _grade_of(res.weighted_score)

    for k, v in dims.items():
        label = {
            "format": "业态", "property_condition": "物业条件", "city_region": "城市区域",
            "positioning_customer": "定位客群", "project_type": "项目类型",
            "business_condition": "商务条件", "expansion_plan": "拓展计划",
            "cooperation_will": "合作意愿",
        }[k]
        if v is None:
            res.pending.append(label)
        elif v >= 75:
            res.satisfied.append(label)
        elif v <= 25:
            res.unsatisfied.append(label)
    return res
