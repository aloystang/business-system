"""出租经营域 Schema：铺位/商户/租约/收费/成本/铺位匹配/商户评估。"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


# ---------- 铺位 ----------
class UnitIn(BaseModel):
    unit_code: str
    project_id: int
    building: str | None = None
    floor: str | None = None
    name: str | None = None
    unit_type: str | None = None
    building_area_m2: float | None = None
    rentable_area_m2: float | None = None
    frontage_m: float | None = None
    depth_m: float | None = None
    height_m: float | None = None
    power_kw: float | None = None
    has_water: bool | None = None
    has_drainage: bool | None = None
    has_grease_trap: bool | None = None
    has_exhaust: bool | None = None
    has_gas: bool | None = None
    external_unit: str | None = None
    loading: str | None = None
    streetfront: str | None = None
    display_face: str | None = None
    fire_zone: str | None = None
    status: str = "空置"
    grade: str | None = None


class UnitOut(UnitIn):
    id: int
    model_config = {"from_attributes": True}


class UnitStatusIn(BaseModel):
    status: str            # 空置/在租/自营/装修


# ---------- 商户 ----------
class MerchantIn(BaseModel):
    merchant_code: str
    name: str
    brand_id: int | None = None
    project_id: int
    unit_id: int | None = None
    contract_entity: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    business_format: str | None = None
    open_date: date | None = None
    operating_status: str = "在营"


class MerchantOut(MerchantIn):
    id: int
    latest_assessment: str | None = None
    model_config = {"from_attributes": True}


# ---------- 租约 ----------
class LeaseIn(BaseModel):
    lease_code: str
    contract_no: str | None = None
    merchant_id: int
    project_id: int
    unit_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    rent_mode: str | None = None
    base_rent: float | None = None
    sales_commission_pct: float | None = None
    management_fee: float | None = None
    deposit: float | None = None
    free_rent_days: int | None = None
    increment_rule: str | None = None
    renewal_status: str | None = None
    alert_days: int = 90
    lease_status: str = "生效"


class LeaseOut(LeaseIn):
    id: int
    model_config = {"from_attributes": True}


# ---------- 收费欠租 ----------
class ReceivableIn(BaseModel):
    receivable_code: str
    lease_id: int
    project_id: int
    fee_item: str                 # 租金/物业费/水电代收/推广费/滞纳金
    period: str                   # YYYY-MM
    due_date: date | None = None
    amount_due: float = 0
    amount_received: float = 0
    prepay_offset: float = 0
    overdue_days: int | None = None
    collect_status: str | None = None
    owner: str | None = None
    remark: str | None = None


class ReceivableOut(BaseModel):
    id: int
    receivable_code: str
    lease_id: int
    project_id: int
    fee_item: str
    period: str
    amount_due: float
    amount_received: float
    prepay_offset: float
    arrears: float
    overdue_days: int | None = None
    aging: str | None = None
    collect_status: str | None = None
    model_config = {"from_attributes": True}


# ---------- 项目成本 ----------
class ProjectCostIn(BaseModel):
    project_id: int
    period: str                   # YYYY-MM
    cost_type: str                # 物业成本/水电能耗/人力/维修/其他
    amount: float = 0
    remark: str | None = None


class ProjectCostOut(ProjectCostIn):
    id: int
    model_config = {"from_attributes": True}


# ---------- 铺位匹配 / 商户评估 ----------
class UnitMatchIn(BaseModel):
    unit_id: int
    brand_id: int
    dims: list[int]               # 5 维各 0-20：业态/物业/项目/商务/意愿
    condition_gap: str | None = None
    reno_suggestion: str | None = None
    leasing_suggestion: str | None = None


class UnitMatchOut(BaseModel):
    id: int
    unit_id: int
    brand_id: int
    dim_format: int | None = None
    dim_property: int | None = None
    dim_project: int | None = None
    dim_business: int | None = None
    dim_will: int | None = None
    total: int | None = None
    grade: str | None = None
    leasing_suggestion: str | None = None
    match_status: str | None = None
    model_config = {"from_attributes": True}


class MerchantAssessIn(BaseModel):
    merchant_id: int
    dims: list[int]               # 4 维各 0-25：业态贡献/租金水平/经营质量/品牌能级
    candidate_brand_id: int | None = None
    assessor: str | None = None
    note: str | None = None


class MerchantAssessOut(BaseModel):
    id: int
    assess_code: str
    merchant_id: int
    total: int | None = None
    conclusion: str | None = None
    action: str | None = None
    assessor: str | None = None
    model_config = {"from_attributes": True}
