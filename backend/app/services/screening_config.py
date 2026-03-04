from __future__ import annotations

from typing import Any, Optional

LEVELS = [5, 4, 3, 2, 1]
LEVEL_TO_SCORE = {5: 100, 4: 80, 3: 60, 2: 40, 1: 20}

CONCLUSION_BANDS = [
    {"label": "不推荐", "min": None, "max": 60},
    {"label": "一般推荐", "min": 60, "max": 75},
    {"label": "高度推荐", "min": 75, "max": 90},
    {"label": "强烈推荐", "min": 90, "max": None},
]

SCREENING_CONFIG_VERSION = "screening-v2.0.0"

INDICATOR_CONFIG = [
    {
        "key": "city_population",
        "category": "人口情况",
        "name": "城市人口",
        "weight": 5,
        "note": "衡量城市商业基本盘与消费规模",
        "source_field": "city_population_10k",
        "rule_type": "numeric_range",
        "thresholds": [
            {"level": 5, "min": 100, "label": "市区常住人口>=100万"},
            {"level": 4, "min": 90, "label": "市区常住人口90-100万"},
            {"level": 3, "min": 80, "label": "市区常住人口80-90万"},
            {"level": 2, "min": 70, "label": "市区常住人口70-80万"},
            {"level": 1, "min": 60, "label": "市区常住人口60-70万"},
        ],
    },
    {
        "key": "population_5km",
        "category": "人口情况",
        "name": "项目周边 5km 人口",
        "weight": 7,
        "note": "反映主力客群半径内人口支撑",
        "source_field": "population_5km_10k",
        "rule_type": "numeric_range",
        "thresholds": [
            {"level": 5, "min": 50, "label": "5公里半径人口>=50万"},
            {"level": 4, "min": 40, "label": "5公里半径人口40-50万"},
            {"level": 3, "min": 35, "label": "5公里半径人口35-40万"},
            {"level": 2, "min": 30, "label": "5公里半径人口30-35万"},
            {"level": 1, "min": 25, "label": "5公里半径人口25-30万"},
        ],
    },
    {
        "key": "population_3km",
        "category": "人口情况",
        "name": "项目周边 3km 人口",
        "weight": 6,
        "note": "反映近场即时消费与到店基础",
        "source_field": "population_3km_10k",
        "rule_type": "numeric_range",
        "thresholds": [
            {"level": 5, "min": 35, "label": "3公里半径人口>=35万"},
            {"level": 4, "min": 30, "label": "3公里半径人口30-35万"},
            {"level": 3, "min": 25, "label": "3公里半径人口25-30万"},
            {"level": 2, "min": 20, "label": "3公里半径人口20-25万"},
            {"level": 1, "min": 15, "label": "3公里半径人口15-20万"},
        ],
    },
    {
        "key": "city_circle_level",
        "category": "商业环境",
        "name": "城市级别及商圈",
        "weight": 7,
        "note": "体现商圈能级、辐射力与成熟度",
        "source_field": "city_circle_level",
        "rule_type": "enum_map",
        "enum_map": {
            "一线城市核心商圈": 5,
            "二线城市核心商圈/一线城市区域商圈": 4,
            "二线城市区域商圈/三线城市核心商圈": 3,
            "三线城市区域商圈": 2,
            "未形成商圈": 1,
        },
    },
    {
        "key": "competition_market_level",
        "category": "商业环境",
        "name": "市场竞争状况",
        "weight": 6,
        "note": "评估同质项目密度与分流压力",
        "source_field": "competition_market_level",
        "rule_type": "enum_map",
        "enum_map": {
            "3km内无5万㎡以上同业定位商业项目": 5,
            "3km内无8万㎡以上同业定位商业项目": 4,
            "3km内有1个8万㎡同业定位商业项目": 3,
            "3km内有2个8万㎡同业定位商业项目": 2,
            "3km内超过2个8万㎡同业定位商业项目": 1,
        },
    },
    {
        "key": "commercial_rent",
        "category": "商业环境",
        "name": "商业租金",
        "weight": 7,
        "note": "体现区域商业价值与租赁承受能力",
        "source_field": "rent_min,rent_max",
        "rule_type": "derived",
        "derived": "average_rent",
        "thresholds": [
            {"level": 5, "min": 400, "label": "商业租金>=400元/㎡/月"},
            {"level": 4, "min": 300, "label": "商业租金300-400元/㎡/月"},
            {"level": 3, "min": 200, "label": "商业租金200-300元/㎡/月"},
            {"level": 2, "min": 150, "label": "商业租金150-200元/㎡/月"},
            {"level": 1, "min": 100, "label": "商业租金100-150元/㎡/月"},
        ],
    },
    {
        "key": "housing_price",
        "category": "消费力",
        "name": "城市房价",
        "weight": 5,
        "note": "反映地段价值与居民支付能力代理变量",
        "source_field": "housing_price_5km",
        "rule_type": "numeric_range",
        "thresholds": [
            {"level": 5, "min": 20000, "label": "5公里住宅均价>=20000元/㎡"},
            {"level": 4, "min": 15000, "label": "5公里住宅均价>=15000元/㎡"},
            {"level": 3, "min": 10000, "label": "5公里住宅均价>=10000元/㎡"},
            {"level": 2, "min": 8000, "label": "5公里住宅均价>=8000元/㎡"},
            {"level": 1, "min": 6000, "label": "5公里住宅均价>=6000元/㎡"},
        ],
    },
    {
        "key": "disposable_income",
        "category": "消费力",
        "name": "人均可支配收入",
        "weight": 7,
        "note": "反映消费力水平与升级空间",
        "source_field": "disposable_income_10k",
        "rule_type": "numeric_range",
        "thresholds": [
            {"level": 5, "min": 5, "label": "P>=5万元"},
            {"level": 4, "min": 4.5, "label": "P>=4.5万元"},
            {"level": 3, "min": 4, "label": "P>=4万元"},
            {"level": 2, "min": 3.5, "label": "P>=3.5万元"},
            {"level": 1, "min": 3, "label": "P>=3万元"},
        ],
    },
    {
        "key": "regional_function",
        "category": "城市规划",
        "name": "区域功能定位",
        "weight": 5,
        "note": "判断区域产业/居住/办公属性与客群结构",
        "source_field": "regional_function_level",
        "rule_type": "enum_map",
        "enum_map": {
            "城市级大型住宅区": 5,
            "城市级大型商务区": 4,
            "城市次级住宅区": 3,
            "城市次级商务区": 2,
            "以上情况都不属于": 1,
        },
    },
    {
        "key": "commercial_planning",
        "category": "城市规划",
        "name": "商业规划",
        "weight": 5,
        "note": "判断新增供给、规划约束与未来兑现预期",
        "source_field": "commercial_planning_level",
        "rule_type": "enum_map",
        "enum_map": {
            "城市商业区中心核心地点": 5,
            "城市商业区中心非核心地点": 4,
            "城市副商业区中心核心地点": 3,
            "城市副商业区中心非核心地点": 2,
            "受商圈影响较小": 1,
        },
    },
    {
        "key": "rail_access",
        "category": "交通条件",
        "name": "轨道覆盖",
        "weight": 6,
        "note": "衡量轨道可达性与跨区导流能力",
        "source_field": "rail_access_level",
        "rule_type": "enum_map",
        "enum_map": {
            "直接连接轨道交通站点": 5,
            "与轨道交通站点100m": 4,
            "与轨道交通站点200m": 3,
            "200m以外无轨道交通站点": 2,
            "500m以外无轨道交通站点": 1,
        },
    },
    {
        "key": "arterial_access",
        "category": "交通条件",
        "name": "主干道通达",
        "weight": 5,
        "note": "衡量车行可达性与区域通勤效率",
        "source_field": "arterial_access_level",
        "rule_type": "enum_map",
        "enum_map": {
            "有2条城市主干道": 5,
            "有1条城市主干道": 4,
            "与城市主干道50m": 3,
            "与城市主干道100m": 2,
            "与城市主干道>100m": 1,
        },
    },
    {
        "key": "bus_access",
        "category": "交通条件",
        "name": "公交站点",
        "weight": 4,
        "note": "衡量公共交通便利度与到店可达性",
        "source_field": "bus_access_level",
        "rule_type": "enum_map",
        "enum_map": {
            "5条以上公交站点在项目1公里范围内": 5,
            "3条以上公交站点在项目1公里范围内": 4,
            "2条以上公交站点在项目1公里范围内": 3,
            "1条以上公交站点在项目1公里范围内": 2,
            "公交站点在项目1公里以外": 1,
        },
    },
    {
        "key": "operation_retrofit_potential",
        "category": "资产属性",
        "name": "经营与改造潜力",
        "weight": 10,
        "note": "低投入也能提升的运营与空间优化空间",
        "source_field": "operation_retrofit_potential_level",
        "rule_type": "enum_map",
        "enum_map": {
            "低投入可快速提升": 5,
            "低投入可阶段提升": 4,
            "中等投入可提升": 3,
            "高投入方可改善": 2,
            "短期改善空间有限": 1,
        },
    },
    {
        "key": "asset_rights_complexity",
        "category": "资产属性",
        "name": "资产与权属复杂度",
        "weight": 15,
        "note": "权属/决策链复杂度对盘活落地的影响",
        "source_field": "asset_rights_complexity_level",
        "rule_type": "enum_map",
        "enum_map": {
            "权属清晰决策链短": 5,
            "权属较清晰协同可控": 4,
            "存在多方协同": 3,
            "权属较复杂审批链长": 2,
            "权属复杂落地难度高": 1,
        },
    },
]

INDICATOR_BY_KEY = {item["key"]: item for item in INDICATOR_CONFIG}


def _validate_config() -> None:
    total_weight = sum(item["weight"] for item in INDICATOR_CONFIG)
    if total_weight != 100:
        raise ValueError(f"Indicator weight sum must be 100, got {total_weight}")


_validate_config()


def _derive_average_rent(project: Any) -> Optional[float]:
    rent_min = getattr(project, "rent_min", None)
    rent_max = getattr(project, "rent_max", None)
    if rent_min is None and rent_max is None:
        return None
    if rent_min is None:
        return float(rent_max)
    if rent_max is None:
        return float(rent_min)
    return (float(rent_min) + float(rent_max)) / 2


def evaluate_numeric_threshold(value: float, thresholds: list[dict[str, Any]]) -> int:
    for threshold in sorted(thresholds, key=lambda item: item["level"], reverse=True):
        if value >= threshold["min"]:
            return int(threshold["level"])
    return 1


def evaluate_indicator_auto(indicator: dict[str, Any], project: Any) -> tuple[Optional[int], Optional[Any]]:
    rule_type = indicator["rule_type"]

    if rule_type == "numeric_range":
        raw_value = getattr(project, indicator["source_field"], None)
        if raw_value is None:
            return None, None
        value = float(raw_value)
        return evaluate_numeric_threshold(value, indicator["thresholds"]), value

    if rule_type == "derived":
        if indicator.get("derived") == "average_rent":
            value = _derive_average_rent(project)
            if value is None:
                return None, None
            return evaluate_numeric_threshold(value, indicator["thresholds"]), value
        return None, None

    if rule_type == "enum_map":
        raw_value = getattr(project, indicator["source_field"], None)
        if not raw_value:
            return None, None
        enum_map = indicator["enum_map"]
        level = enum_map.get(str(raw_value))
        if level is None:
            return None, raw_value
        return int(level), raw_value

    return None, None


def level_to_score(level: int) -> int:
    return LEVEL_TO_SCORE[int(level)]


def conclusion_from_total(total_score: float) -> str:
    if total_score >= 90:
        return "强烈推荐"
    if total_score >= 75:
        return "高度推荐"
    if total_score >= 60:
        return "一般推荐"
    return "不推荐"


def get_screening_config_payload() -> dict[str, Any]:
    categories: dict[str, list[dict[str, Any]]] = {}
    for indicator in INDICATOR_CONFIG:
        categories.setdefault(indicator["category"], []).append(
            {
                "key": indicator["key"],
                "name": indicator["name"],
                "weight": indicator["weight"],
                "note": indicator["note"],
                "source_field": indicator["source_field"],
                "rule_type": indicator["rule_type"],
                "thresholds": indicator.get("thresholds", []),
                "enum_map": indicator.get("enum_map", {}),
            }
        )

    ordered_categories = [
        {"name": "人口情况", "indicators": categories.get("人口情况", [])},
        {"name": "商业环境", "indicators": categories.get("商业环境", [])},
        {"name": "消费力", "indicators": categories.get("消费力", [])},
        {"name": "城市规划", "indicators": categories.get("城市规划", [])},
        {"name": "交通条件", "indicators": categories.get("交通条件", [])},
        {"name": "资产属性", "indicators": categories.get("资产属性", [])},
    ]

    return {
        "version": SCREENING_CONFIG_VERSION,
        "levels": LEVELS,
        "level_score_map": LEVEL_TO_SCORE,
        "conclusion_bands": CONCLUSION_BANDS,
        "categories": ordered_categories,
    }
