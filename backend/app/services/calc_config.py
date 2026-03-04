from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


BASE_DIR = Path(__file__).resolve().parent.parent
CALC_DEFAULTS_PATH = BASE_DIR / "rules" / "calc_defaults.yaml"


def _ensure_keys(payload: dict[str, Any], keys: list[str]) -> None:
    for key in keys:
        if key not in payload:
            raise RuntimeError(f"calc defaults missing key: {key}")


@lru_cache(maxsize=1)
def load_calc_defaults() -> dict[str, Any]:
    if not CALC_DEFAULTS_PATH.exists():
        raise RuntimeError(f"calc defaults file not found: {CALC_DEFAULTS_PATH}")

    with CALC_DEFAULTS_PATH.open("r", encoding="utf-8") as fp:
        payload = yaml.safe_load(fp) or {}

    _ensure_keys(payload, ["calc_config_version", "planning_years", "defaults", "advanced_params"])
    _ensure_keys(
        payload["defaults"],
        [
            "rent_base_default",
            "rentable_area_ratio_default",
            "occupancy_curve",
            "rent_growth_curve",
            "leasing_commission_months",
            "operation_commission_rate",
            "operation_monthly_fee_wan",
            "marketing_fee_year1_2_wan",
            "marketing_fee_stable_wan",
            "venue_leasing_rate",
            "ad_leasing_rate",
            "venue_ad_start_year_index",
            "parking_slots",
            "parking_fee_year1_yuan_day",
            "parking_fee_stable_yuan_day",
            "parking_year1_factor",
            "internal_tax_rate",
            "hr_base_annual_cost_wan",
            "hr_growth_rate",
            "admin_annual_cost_wan",
            "invest_cost_default_wan",
        ],
    )
    return payload


def get_calc_runtime_defaults() -> dict[str, Any]:
    payload = load_calc_defaults()
    return {
        "calc_config_version": payload["calc_config_version"],
        "planning_years": int(payload["planning_years"]),
        "defaults": dict(payload["defaults"]),
    }


def get_calc_config_payload() -> dict[str, Any]:
    payload = load_calc_defaults()
    defaults = dict(payload["defaults"])
    params = []
    for param in payload["advanced_params"]:
        item = dict(param)
        key = item.get("key")
        if key in defaults:
            item["default"] = defaults[key]
        params.append(item)
    return {
        "calc_config_version": payload["calc_config_version"],
        "planning_years": int(payload["planning_years"]),
        "defaults": defaults,
        "advanced_params": params,
    }
