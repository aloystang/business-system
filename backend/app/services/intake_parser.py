from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

FIELD_MAP = {
    "项目名称": "name",
    "名称": "name",
    "城市": "city",
    "行政区": "district",
    "项目位置描述": "location_desc",
    "位置描述": "location_desc",
    "总建筑面积": "total_area_m2",
    "可出租面积": "rentable_area_m2",
    "核心区块面积": "core_area_m2",
    "分布形态": "distribution_form",
    "权属结构": "ownership_structure",
    "当前空置率": "vacancy_rate",
    "空置率": "vacancy_rate",
    "租金区间": "rent_range",
    "主要业态类型": "primary_business_types",
    "周边竞品列表": "competitors",
    "竞品列表": "competitors",
    "竞品竞争强度": "competition_intensity",
    "竞争强度": "competition_intensity",
    "自由补充说明": "notes",
    "补充说明": "notes",
}

NUMERIC_FIELDS = {"total_area_m2", "rentable_area_m2", "core_area_m2"}
PERCENT_FIELDS = {"vacancy_rate"}
LIST_FIELDS = {"competitors", "primary_business_types"}


def _normalize_key(key: str) -> str | None:
    key = key.strip()
    return FIELD_MAP.get(key)


def _parse_number(value: str) -> float | None:
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _normalize_value(key: str, value: str) -> Any:
    value = value.strip()
    if key in NUMERIC_FIELDS:
        return _parse_number(value)
    if key in PERCENT_FIELDS:
        number = _parse_number(value)
        return number
    if key in LIST_FIELDS:
        parts = re.split(r"[、,，;；]\s*", value)
        return ", ".join([p.strip() for p in parts if p.strip()])
    return value


def parse_raw_text(raw_text: str) -> Tuple[Dict[str, Any], List[str]]:
    parsed: Dict[str, Any] = {}
    unknown_lines: List[str] = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    for line in lines:
        if ":" in line:
            key_part, value_part = line.split(":", 1)
        elif "：" in line:
            key_part, value_part = line.split("：", 1)
        else:
            unknown_lines.append(line)
            continue

        key = _normalize_key(key_part)
        if not key:
            unknown_lines.append(line)
            continue
        parsed[key] = _normalize_value(key, value_part)

    return parsed, unknown_lines
