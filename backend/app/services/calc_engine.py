from __future__ import annotations

from typing import Any

from ..models import ProjectBaseInfo
from .calc_config import get_calc_runtime_defaults


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _round2(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _round4(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _normalize_curve(values: list[Any], years: int, lower: float, upper: float) -> list[float]:
    normalized = [_clamp(_to_float(item, 0.0), lower, upper) for item in values]
    if not normalized:
        normalized = [0.0]
    if len(normalized) < years:
        normalized.extend([normalized[-1]] * (years - len(normalized)))
    if len(normalized) > years:
        normalized = normalized[:years]
    return normalized


def _resolve_area(project: ProjectBaseInfo, defaults: dict[str, Any]) -> float:
    rentable_area = _to_float(project.rentable_area, 0.0)
    if rentable_area > 0:
        return rentable_area
    total_area = _to_float(project.total_area, 0.0)
    return total_area * _to_float(defaults.get("rentable_area_ratio_default"), 0.7)


def _resolve_rent_base(
    project: ProjectBaseInfo,
    defaults: dict[str, Any],
    overrides: dict[str, Any],
) -> tuple[float, str]:
    if overrides.get("rent_base") is not None:
        return _to_float(overrides.get("rent_base")), "override"

    rent_min = project.rent_min
    rent_max = project.rent_max
    if rent_min is not None and rent_max is not None:
        return (_to_float(rent_min) + _to_float(rent_max)) / 2, "project_avg_rent"
    if rent_min is not None:
        return _to_float(rent_min), "project_rent_min"
    if rent_max is not None:
        return _to_float(rent_max), "project_rent_max"
    return _to_float(defaults.get("rent_base_default"), 100.0), "default"


def _resolve_occupancy_curve(
    project: ProjectBaseInfo,
    defaults: dict[str, Any],
    overrides: dict[str, Any],
    years: int,
) -> list[float]:
    if overrides.get("occupancy_curve") is not None:
        return _normalize_curve(list(overrides.get("occupancy_curve") or []), years, 0.0, 1.0)

    base_curve = _normalize_curve(list(defaults.get("occupancy_curve") or []), years, 0.0, 1.0)
    if project.vacancy_rate is None:
        return base_curve

    stabilized = _clamp(1 - (_to_float(project.vacancy_rate) / 100), 0.0, 1.0)
    adjusted = list(base_curve)
    for idx in range(min(3, years), years):
        adjusted[idx] = stabilized
    return adjusted


def _resolve_growth_curve(defaults: dict[str, Any], overrides: dict[str, Any], years: int) -> list[float]:
    if overrides.get("rent_growth_curve") is not None:
        return _normalize_curve(list(overrides.get("rent_growth_curve") or []), years, -0.5, 1.0)
    return _normalize_curve(list(defaults.get("rent_growth_curve") or []), years, -0.5, 1.0)


def _build_runtime_params(
    project: ProjectBaseInfo,
    defaults: dict[str, Any],
    overrides: dict[str, Any] | None,
    years: int,
) -> dict[str, Any]:
    effective_overrides = overrides or {}
    rent_base, rent_base_source = _resolve_rent_base(project, defaults, effective_overrides)
    occupancy_curve = _resolve_occupancy_curve(project, defaults, effective_overrides, years)
    rent_growth_curve = _resolve_growth_curve(defaults, effective_overrides, years)

    leasing_commission_months = _to_float(
        effective_overrides.get("leasing_commission_months"),
        _to_float(defaults.get("leasing_commission_months"), 2.0),
    )
    operation_commission_rate = _to_float(
        effective_overrides.get("operation_commission_rate"),
        _to_float(defaults.get("operation_commission_rate"), 0.08),
    )

    area = _resolve_area(project, defaults)
    return {
        "years": years,
        "rentable_area_used": area,
        "rent_base": rent_base,
        "rent_base_source": rent_base_source,
        "occupancy_curve": occupancy_curve,
        "rent_growth_curve": rent_growth_curve,
        "leasing_commission_months": leasing_commission_months,
        "operation_commission_rate": operation_commission_rate,
    }


def _build_external_result(
    defaults: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    years = runtime["years"]
    area = runtime["rentable_area_used"]
    rent_curve = runtime["rent_growth_curve"]
    occ_curve = runtime["occupancy_curve"]
    rent_value = runtime["rent_base"]

    operation_monthly_fee_wan = _to_float(defaults.get("operation_monthly_fee_wan"), 12.0)
    marketing_fee_year1_2_wan = _to_float(defaults.get("marketing_fee_year1_2_wan"), 150.0)
    marketing_fee_stable_wan = _to_float(defaults.get("marketing_fee_stable_wan"), 120.0)
    venue_rate = _to_float(defaults.get("venue_leasing_rate"), 0.005)
    ad_rate = _to_float(defaults.get("ad_leasing_rate"), 0.005)
    venue_ad_start_year_index = int(_to_float(defaults.get("venue_ad_start_year_index"), 4))
    parking_slots = _to_float(defaults.get("parking_slots"), 769)
    parking_fee_year1 = _to_float(defaults.get("parking_fee_year1_yuan_day"), 15.0)
    parking_fee_stable = _to_float(defaults.get("parking_fee_stable_yuan_day"), 20.0)
    parking_year1_factor = _to_float(defaults.get("parking_year1_factor"), 0.5)
    consultant_fee_yearly_wan = _to_float(defaults.get("consultant_fee_yearly_wan"), 0.0)

    yearly: list[dict[str, Any]] = []
    cached_year2_commission = 0.0
    for idx in range(years):
        if idx > 0:
            rent_value = rent_value * (1 + rent_curve[idx])
        occupancy = occ_curve[idx]
        operating_area = area * occupancy
        rental_income = rent_value * operating_area * 12 / 10000

        venue_income = rental_income * venue_rate if (idx + 1) >= venue_ad_start_year_index else 0.0
        ad_income = rental_income * ad_rate if (idx + 1) >= venue_ad_start_year_index else 0.0
        parking_income = (
            parking_fee_year1 * parking_slots * 365 / 10000 * parking_year1_factor
            if idx == 0
            else parking_fee_stable * parking_slots * 365 / 10000
        )
        total_revenue = rental_income + venue_income + ad_income + parking_income

        if idx == 0:
            leasing_commission_income = (
                area * occ_curve[0] * runtime["rent_base"] * runtime["leasing_commission_months"] / 10000
            )
        elif idx == 1:
            leasing_commission_income = (
                max(area * occ_curve[1] - area * occ_curve[0], 0)
                * runtime["rent_base"]
                * runtime["leasing_commission_months"]
                / 10000
            )
            cached_year2_commission = leasing_commission_income
        elif idx in (2, 3):
            leasing_commission_income = cached_year2_commission
        else:
            leasing_commission_income = 0.0

        operation_monthly_income = operation_monthly_fee_wan * 12
        operation_commission_income = total_revenue * runtime["operation_commission_rate"]
        consultant_income = consultant_fee_yearly_wan

        mgmt_cost = (
            consultant_income
            + leasing_commission_income
            + operation_monthly_income
            + operation_commission_income
        )
        marketing_cost = marketing_fee_year1_2_wan if idx in (0, 1) else marketing_fee_stable_wan
        total_cost = mgmt_cost + marketing_cost
        gross_profit = total_revenue - total_cost
        gross_margin = gross_profit / total_revenue if total_revenue else None

        yearly.append(
            {
                "year_index": idx + 1,
                "year_label": f"第{idx + 1}年",
                "revenue": _round2(total_revenue),
                "cost": _round2(total_cost),
                "gross_profit": _round2(gross_profit),
                "gross_margin": _round4(gross_margin),
                "tax": None,
                "_leasing_commission_income": leasing_commission_income,
                "_operation_monthly_income": operation_monthly_income,
                "_operation_commission_income": operation_commission_income,
            }
        )

    total_revenue = sum(_to_float(item.get("revenue")) for item in yearly)
    total_cost = sum(_to_float(item.get("cost")) for item in yearly)
    gross_profit = total_revenue - total_cost
    gross_margin = gross_profit / total_revenue if total_revenue else None

    return {
        "summary": {
            "total_revenue": _round2(total_revenue),
            "total_cost": _round2(total_cost),
            "gross_profit": _round2(gross_profit),
            "gross_margin": _round4(gross_margin),
            "tax_after_profit": _round2(gross_profit),
        },
        "yearly": yearly,
    }


def _build_internal_result(
    defaults: dict[str, Any],
    runtime: dict[str, Any],
    external_yearly: list[dict[str, Any]],
) -> dict[str, Any]:
    tax_rate = _to_float(defaults.get("internal_tax_rate"), 0.06)
    hr_base = _to_float(defaults.get("hr_base_annual_cost_wan"), 107.52)
    hr_growth = _to_float(defaults.get("hr_growth_rate"), 0.02)
    admin_annual = _to_float(defaults.get("admin_annual_cost_wan"), 15.0)

    yearly: list[dict[str, Any]] = []
    for idx, external_row in enumerate(external_yearly):
        leasing_income = _to_float(external_row.get("_leasing_commission_income"), 0.0)
        op_monthly_income = _to_float(external_row.get("_operation_monthly_income"), 0.0)
        op_comm_income = _to_float(external_row.get("_operation_commission_income"), 0.0)
        revenue_before_tax = leasing_income + op_monthly_income + op_comm_income
        tax = revenue_before_tax * tax_rate
        revenue_after_tax = revenue_before_tax - tax

        hr_cost = hr_base * ((1 + hr_growth) ** idx)
        admin_cost = admin_annual
        total_cost = hr_cost + admin_cost

        gross_profit = revenue_before_tax - total_cost
        gross_margin = gross_profit / revenue_before_tax if revenue_before_tax else None
        tax_after_profit = revenue_after_tax - total_cost

        yearly.append(
            {
                "year_index": idx + 1,
                "year_label": f"第{idx + 1}年",
                "revenue": _round2(revenue_before_tax),
                "cost": _round2(total_cost),
                "gross_profit": _round2(gross_profit),
                "gross_margin": _round4(gross_margin),
                "tax": _round2(tax),
                "_tax_after_profit": tax_after_profit,
                "_hr_cost": hr_cost,
                "_admin_cost": admin_cost,
            }
        )

    total_revenue = sum(_to_float(item.get("revenue")) for item in yearly)
    total_cost = sum(_to_float(item.get("cost")) for item in yearly)
    gross_profit = total_revenue - total_cost
    gross_margin = gross_profit / total_revenue if total_revenue else None
    tax_after_profit = sum(_to_float(item.get("_tax_after_profit")) for item in yearly)

    return {
        "summary": {
            "total_revenue": _round2(total_revenue),
            "total_cost": _round2(total_cost),
            "gross_profit": _round2(gross_profit),
            "gross_margin": _round4(gross_margin),
            "tax_after_profit": _round2(tax_after_profit),
        },
        "yearly": yearly,
    }


def _public_yearly(yearly: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "year_index": int(item["year_index"]),
            "year_label": item["year_label"],
            "revenue": _round2(_to_float(item.get("revenue"))),
            "cost": _round2(_to_float(item.get("cost"))),
            "gross_profit": _round2(_to_float(item.get("gross_profit"))),
            "gross_margin": _round4(item.get("gross_margin")),
            "tax": _round2(item.get("tax")) if item.get("tax") is not None else None,
        }
        for item in yearly
    ]


def compute_dual_calculation(
    project: ProjectBaseInfo,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = get_calc_runtime_defaults()
    years = int(config["planning_years"])
    defaults = dict(config["defaults"])
    runtime = _build_runtime_params(project, defaults, overrides, years)

    external_raw = _build_external_result(defaults, runtime)
    internal_raw = _build_internal_result(defaults, runtime, external_raw["yearly"])

    params_used = {
        "planning_years": years,
        "rent_base": _round4(runtime["rent_base"]),
        "rent_base_source": runtime["rent_base_source"],
        "rentable_area_used": _round2(runtime["rentable_area_used"]),
        "occupancy_curve": [_round4(v) for v in runtime["occupancy_curve"]],
        "rent_growth_curve": [_round4(v) for v in runtime["rent_growth_curve"]],
        "leasing_commission_months": _round4(runtime["leasing_commission_months"]),
        "operation_commission_rate": _round4(runtime["operation_commission_rate"]),
        "invest_cost_default_wan": _round2(_to_float(defaults.get("invest_cost_default_wan"), 0.0)),
        "internal_tax_rate": _round4(_to_float(defaults.get("internal_tax_rate"), 0.06)),
    }

    external = {
        "summary": external_raw["summary"],
        "yearly": _public_yearly(external_raw["yearly"]),
        "params_used": params_used,
        "source": "auto_from_collection",
        "calc_basis": "owner_v1",
    }
    internal = {
        "summary": internal_raw["summary"],
        "yearly": _public_yearly(internal_raw["yearly"]),
        "params_used": params_used,
        "source": "auto_from_collection",
        "calc_basis": "huarun_v1",
    }

    return {
        "config_version": config["calc_config_version"],
        "params_used": params_used,
        "external": external,
        "internal": internal,
        "external_raw": external_raw,
        "internal_raw": internal_raw,
    }
