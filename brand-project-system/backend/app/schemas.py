"""Pydantic Schema。"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    role: str
    model_config = {"from_attributes": True}


class BrandOut(BaseModel):
    id: int
    brand_code: str
    brand_name: str
    brand_short_name: str | None = None
    l1_category: str | None = None
    l2_category: str | None = None
    l3_category: str | None = None
    tags: str | None = None
    operating_status: str | None = None
    store_count: int | None = None
    hq_city: str | None = None
    cooperation_intent: str | None = None
    grade: str | None = None
    model_config = {"from_attributes": True}


class LocationOut(BaseModel):
    province: str
    city: str
    district: str
    address: str
    longitude: float | None = None
    latitude: float | None = None
    coordinate_system: str | None = None
    geocoding_status: str
    model_config = {"from_attributes": True}


class ProjectOut(BaseModel):
    id: int
    project_code: str
    project_name: str
    project_short_name: str | None = None
    project_type: str
    project_status: str
    open_date: str | None = None
    asset_holder: str | None = None
    operator: str | None = None
    business_area_m2: float | None = None
    leasable_area_m2: float | None = None
    target_formats: str | None = None
    core_customers: str | None = None
    cooperation_will: str | None = None
    leasing_stage: str | None = None
    grade: str | None = None
    is_sensitive: bool = False
    location: LocationOut | None = None
    model_config = {"from_attributes": True}


class MarkerOut(BaseModel):
    id: int
    project_code: str
    name: str
    type: str
    status: str
    grade: str | None = None
    lng: float
    lat: float
    is_sensitive: bool = False
    blurred: bool = False


class MatchOut(BaseModel):
    id: int | None = None
    brand_id: int
    project_id: int
    brand_name: str | None = None
    project_name: str | None = None
    dims: dict[str, int | None]
    hard_gate_triggered: bool
    hard_gate_reason: str | None = None
    weighted_score: float | None = None
    data_coverage_rate: float
    is_formal: bool
    match_grade: str
    satisfied: list[str] = []
    unsatisfied: list[str] = []
    pending: list[str] = []
    manual_adjust: float = 0
    final_score: float | None = None
    priority: str | None = None
    rule_version: str


class ComputeIn(BaseModel):
    brand_id: int
    project_id: int


class AdjustIn(BaseModel):
    manual_adjust: float
    reason: str


class GeocodeIn(BaseModel):
    address: str
    city: str | None = None


class ReverseIn(BaseModel):
    longitude: float
    latitude: float


class GeocodeResultOut(BaseModel):
    longitude: float | None = None
    latitude: float | None = None
    coordinate_system: str = "GCJ-02"
    provider: str = "amap"
    level: str | None = None
    accuracy: str | None = None
    geocoding_status: str
    formatted_address: str | None = None
    candidates: list[dict] = []


class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    project_short_name: str | None = None
    project_type: str
    project_status: str = "招商中"
    operator: str | None = None
    asset_holder: str | None = None
    business_area_m2: float | None = None
    target_formats: str | None = None
    core_customers: str | None = None
    cooperation_will: str | None = None
    is_sensitive: bool = False
    # 定位（新建时自动解析坐标）
    province: str
    city: str
    district: str
    address: str


class LocationUpdateIn(BaseModel):
    province: str
    city: str
    district: str
    address: str
    longitude: float | None = None
    latitude: float | None = None
    geocoding_status: str = "人工修正"
    manually_adjusted: bool = True


# ---------- 品牌 CRUD ----------

class BrandCreate(BaseModel):
    brand_code: str
    brand_name: str
    brand_short_name: str | None = None
    l1_category: str | None = None
    l2_category: str | None = None
    l3_category: str | None = None
    tags: str | None = None
    operating_status: str | None = None
    store_count: int | None = None
    hq_city: str | None = None
    brand_intro: str | None = None
    cooperation_intent: str | None = None


class BrandUpdate(BaseModel):
    brand_name: str | None = None
    brand_short_name: str | None = None
    l1_category: str | None = None
    l2_category: str | None = None
    l3_category: str | None = None
    tags: str | None = None
    operating_status: str | None = None
    store_count: int | None = None
    hq_city: str | None = None
    brand_intro: str | None = None
    cooperation_intent: str | None = None


class ContactIn(BaseModel):
    contact_name: str
    dept: str | None = None
    title: str | None = None
    mobile: str | None = None
    wechat: str | None = None
    email: str | None = None
    region: str | None = None
    party_type: str | None = None
    is_primary: bool = False
    valid_status: str = "有效"


class ContactOut(ContactIn):
    id: int
    model_config = {"from_attributes": True}


class ExpansionIn(BaseModel):
    target_cities: str | None = None
    acceptable_project_types: str | None = None
    accept_stadium_commercial: bool | None = None
    accept_new_project: bool | None = None
    area_min: float | None = None
    area_max: float | None = None
    power_req_kw: float | None = None
    needs_gas: bool | None = None
    rent_tolerance: str | None = None


class ExpansionOut(ExpansionIn):
    id: int
    brand_id: int
    model_config = {"from_attributes": True}


class ScoreIn(BaseModel):
    dims: list[int]           # 5 维，各 0..20
    basis: str | None = None


class ScoreOut(BaseModel):
    id: int
    total_score: int | None = None
    grade: str | None = None
    basis: str | None = None
    rule_version: str
    is_current: bool
    model_config = {"from_attributes": True}


# ---------- 候选 / 沟通 / 任务 ----------

class CandidateListIn(BaseModel):
    list_name: str
    target_project_id: int | None = None
    description: str | None = None


class CandidateItemIn(BaseModel):
    brand_id: int
    project_id: int | None = None
    match_id: int | None = None
    item_status: str = "储备"
    note: str | None = None


class CandidateItemStatusIn(BaseModel):
    item_status: str


class CandidateItemOut(BaseModel):
    id: int
    brand_id: int | None = None
    brand_name: str | None = None
    item_status: str
    note: str | None = None
    model_config = {"from_attributes": True}


class CandidateListOut(BaseModel):
    id: int
    list_name: str
    target_project_id: int | None = None
    description: str | None = None
    items: list[CandidateItemOut] = []
    model_config = {"from_attributes": True}


class CommIn(BaseModel):
    related_type: str          # brand/project/match
    brand_id: int | None = None
    project_id: int | None = None
    match_id: int | None = None
    contact_name: str | None = None
    comm_date: str
    channel: str | None = None
    summary: str | None = None
    cooperation_will: str | None = None
    obstacle: str | None = None
    next_action: str | None = None
    plan_date: str | None = None


class CommOut(BaseModel):
    id: int
    related_type: str
    brand_id: int | None = None
    project_id: int | None = None
    match_id: int | None = None
    contact_name: str | None = None
    comm_date: date
    channel: str | None = None
    summary: str | None = None
    cooperation_will: str | None = None
    obstacle: str | None = None
    next_action: str | None = None
    plan_date: date | None = None
    model_config = {"from_attributes": True}


class TaskIn(BaseModel):
    title: str
    related_type: str | None = None
    brand_id: int | None = None
    project_id: int | None = None
    match_id: int | None = None
    owner_id: int | None = None
    priority: str | None = None
    plan_date: str | None = None
    detail: str | None = None


class TaskUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    plan_date: str | None = None
    detail: str | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    status: str
    priority: str | None = None
    owner_id: int | None = None
    plan_date: date | None = None
    related_type: str | None = None
    brand_id: int | None = None
    project_id: int | None = None
    model_config = {"from_attributes": True}


# ---------- 字典 / 审核 / 导入 ----------

class DictIn(BaseModel):
    dict_type: str
    code: str
    label: str
    sort_no: int = 0
    is_active: bool = True


class DictOut(DictIn):
    id: int
    model_config = {"from_attributes": True}


class ApprovalDecideIn(BaseModel):
    action: str                # approve/reject
    comment: str | None = None


class ApprovalOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    status: str
    comment: str | None = None
    model_config = {"from_attributes": True}


class ImportBatchOut(BaseModel):
    id: int
    batch_no: str
    status: str
    dry_run: bool
    total_rows: int | None = None
    valid_rows: int | None = None
    error_rows: int | None = None
    result_summary: dict | None = None
    error_detail: list | dict | None = None
    geocode_failed: list | None = None
    model_config = {"from_attributes": True}


# ---------- 用户 / 角色 / 审计 ----------

class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    role: str = "viewer"
    email: str | None = None
    phone: str | None = None


class UserUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class UserAdminOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    role: str
    email: str | None = None
    phone: str | None = None
    is_active: bool
    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    model_config = {"from_attributes": True}


class PermissionOut(BaseModel):
    id: int
    code: str
    name: str
    resource: str
    action: str
    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None = None
    actor_name: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    detail: dict | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
