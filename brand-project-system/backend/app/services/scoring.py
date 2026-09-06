"""五维评分：合计与等级（规则 v1.0，S≥90/A80-89/B70-79/C<70，可配置）。"""
from __future__ import annotations

RULE_VERSION = "v1.0"
MAX_PER_DIM = 20
GRADE_TIERS = [("S", 90), ("A", 80), ("B", 70), ("C", 0)]

BRAND_DIMS = [
    "score_market_influence", "score_tenant_capability", "score_growth_potential",
    "score_credit", "score_cooperation_will",
]
PROJECT_DIMS = [
    "score_location_traffic", "score_scale_condition", "score_positioning_customer",
    "score_operation_resource", "score_cooperation_opportunity",
]


def grade_for(total: int) -> str:
    for name, floor in GRADE_TIERS:
        if total >= floor:
            return name
    return "C"


def total_and_grade(dim_values: list[int]) -> tuple[int, str]:
    """校验每维 0..20，返回 (合计, 等级)。越界抛 ValueError。"""
    for v in dim_values:
        if v is None or not (0 <= v <= MAX_PER_DIM):
            raise ValueError(f"评分维度须为 0..{MAX_PER_DIM} 的整数，得到 {v}")
    total = sum(dim_values)
    return total, grade_for(total)
