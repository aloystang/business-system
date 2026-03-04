from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import IssueCategory, IssuePriority, IssueStatus, Stage, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    username: str
    role: UserRole
    is_active: bool = True


class UserOut(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProjectBase(BaseModel):
    code: str
    name: str
    region: str
    asset_type: str
    client_name: str
    address: Optional[str] = None
    area_m2: Optional[float] = None
    population_index: Optional[str] = None
    external_summary: Optional[str] = None
    external_enabled: bool = False


class ProjectCreate(ProjectBase):
    owner_user_id: int


class ProjectUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    region: Optional[str] = None
    asset_type: Optional[str] = None
    client_name: Optional[str] = None
    address: Optional[str] = None
    area_m2: Optional[float] = None
    population_index: Optional[str] = None
    current_stage: Optional[Stage] = None
    owner_user_id: Optional[int] = None
    external_summary: Optional[str] = None
    external_enabled: Optional[bool] = None


class ProjectOut(ProjectBase):
    id: int
    current_stage: Stage
    owner_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectList(BaseModel):
    items: List[ProjectOut]
    total: int
    page: int
    page_size: int


class StageTransitionCreate(BaseModel):
    to_stage: Stage
    note: Optional[str] = None


class StageTransitionOut(BaseModel):
    id: int
    project_id: int
    from_stage: str
    to_stage: str
    transitioned_by: int
    transitioned_at: datetime
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeliverableOut(BaseModel):
    id: int
    project_id: int
    stage: str
    type: str
    title: str
    version: int
    file_path: str
    file_name: str
    mime_type: Optional[str] = None
    is_external_visible: bool
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueCreate(BaseModel):
    category: IssueCategory
    title: str
    description: Optional[str] = None
    priority: IssuePriority = IssuePriority.medium
    status: IssueStatus = IssueStatus.open
    assignee_user_id: Optional[int] = None
    due_date: Optional[date] = None
    escalated: bool = False


class IssueUpdate(BaseModel):
    category: Optional[IssueCategory] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[IssuePriority] = None
    status: Optional[IssueStatus] = None
    assignee_user_id: Optional[int] = None
    due_date: Optional[date] = None
    escalated: Optional[bool] = None


class IssueOut(BaseModel):
    id: int
    project_id: int
    category: IssueCategory
    title: str
    description: Optional[str] = None
    priority: IssuePriority
    status: IssueStatus
    assignee_user_id: Optional[int] = None
    due_date: Optional[date] = None
    escalated: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    metadata_json: Optional[str] = None
    ip: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StageCheckResult(BaseModel):
    current_stage: Stage
    target_stage: Stage
    required_fields: List[str]
    required_deliverables: List[str]
    missing_fields: List[str]
    missing_deliverables: List[str]
    ok: bool


class ShareCreateRequest(BaseModel):
    expires_in_days: Optional[int] = 7


class ShareResponse(BaseModel):
    share_url: str
    token: str
    expires_at: Optional[datetime] = None


class PublicProjectOut(BaseModel):
    code: str
    name: str
    region: str
    asset_type: str
    client_name: str
    address: Optional[str] = None
    area_m2: Optional[float] = None
    population_index: Optional[str] = None
    current_stage: Stage
    external_summary: Optional[str] = None


class PublicDeliverableOut(BaseModel):
    id: int
    title: str
    type: str
    version: int
    created_at: datetime
    file_name: str

    model_config = ConfigDict(from_attributes=True)


class IntakeCreate(BaseModel):
    raw_text: str


class IntakeOut(BaseModel):
    id: int
    raw_text: str
    parsed_fields: Dict[str, Any]
    unknown_lines: List[str]
    status: str
    created_by: int
    created_at: datetime


class ProjectProfileBase(BaseModel):
    name: str
    city: Optional[str] = None
    district: Optional[str] = None
    location_desc: Optional[str] = None
    total_area_m2: Optional[float] = None
    rentable_area_m2: Optional[float] = None
    core_area_m2: Optional[float] = None
    distribution_form: Optional[str] = None
    ownership_structure: Optional[str] = None
    vacancy_rate: Optional[float] = None
    rent_range: Optional[str] = None
    primary_business_types: Optional[str] = None
    competitors: Optional[str] = None
    competition_intensity: Optional[str] = None
    notes: Optional[str] = None


class ProjectProfileCreate(ProjectProfileBase):
    intake_id: Optional[int] = None


class ProjectProfileUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    location_desc: Optional[str] = None
    total_area_m2: Optional[float] = None
    rentable_area_m2: Optional[float] = None
    core_area_m2: Optional[float] = None
    distribution_form: Optional[str] = None
    ownership_structure: Optional[str] = None
    vacancy_rate: Optional[float] = None
    rent_range: Optional[str] = None
    primary_business_types: Optional[str] = None
    competitors: Optional[str] = None
    competition_intensity: Optional[str] = None
    notes: Optional[str] = None


class ProjectProfileOut(ProjectProfileBase):
    id: int
    intake_id: Optional[int] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectBaseInfoBase(BaseModel):
    project_name: str
    city: str
    district: str
    location_desc: Optional[str] = None
    total_area: float
    rentable_area: Optional[float] = None
    core_area: Optional[float] = None
    asset_distribution: str
    ownership_structure: str
    vacancy_rate: Optional[float] = None
    rent_min: Optional[float] = None
    rent_max: Optional[float] = None
    main_business_type: Optional[str] = None
    competitor_list: Optional[str] = None
    competition_level: str
    city_population_10k: Optional[float] = None
    population_5km_10k: Optional[float] = None
    population_3km_10k: Optional[float] = None
    city_circle_level: Optional[str] = None
    competition_market_level: Optional[str] = None
    housing_price_5km: Optional[float] = None
    disposable_income_10k: Optional[float] = None
    regional_function_level: Optional[str] = None
    commercial_planning_level: Optional[str] = None
    rail_access_level: Optional[str] = None
    arterial_access_level: Optional[str] = None
    bus_access_level: Optional[str] = None
    operation_retrofit_potential_level: Optional[str] = None
    asset_rights_complexity_level: Optional[str] = None
    remark: Optional[str] = None
    is_confirmed: Optional[int] = 0


class SurveyMerchantRowIn(BaseModel):
    name: str
    category: str
    area_m2: float
    rent_unit_price: float
    daily_flow: int
    address: str
    city: str
    district: str
    note: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class SurveyCompetitionRowIn(BaseModel):
    name: str
    scale_m2: float
    avg_rent_unit_price: float
    vacancy_rate: float
    business_type: str
    distance_km: float
    target_people: str
    address: str
    city: str
    district: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class SurveyMerchantRowOut(SurveyMerchantRowIn):
    geocode_status: Optional[str] = None
    geocode_message: Optional[str] = None
    geocoded_at: Optional[str] = None
    created_at: Optional[str] = None


class SurveyCompetitionRowOut(SurveyCompetitionRowIn):
    geocode_status: Optional[str] = None
    geocode_message: Optional[str] = None
    geocoded_at: Optional[str] = None
    created_at: Optional[str] = None


class ProjectBaseInfoCreate(ProjectBaseInfoBase):
    project_id: Optional[str] = None
    merchant_rows: Optional[List[SurveyMerchantRowIn]] = None
    competition_rows: Optional[List[SurveyCompetitionRowIn]] = None


class ProjectBaseInfoUpdate(BaseModel):
    project_name: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    location_desc: Optional[str] = None
    total_area: Optional[float] = None
    rentable_area: Optional[float] = None
    core_area: Optional[float] = None
    asset_distribution: Optional[str] = None
    ownership_structure: Optional[str] = None
    vacancy_rate: Optional[float] = None
    rent_min: Optional[float] = None
    rent_max: Optional[float] = None
    main_business_type: Optional[str] = None
    competitor_list: Optional[str] = None
    competition_level: Optional[str] = None
    city_population_10k: Optional[float] = None
    population_5km_10k: Optional[float] = None
    population_3km_10k: Optional[float] = None
    city_circle_level: Optional[str] = None
    competition_market_level: Optional[str] = None
    housing_price_5km: Optional[float] = None
    disposable_income_10k: Optional[float] = None
    regional_function_level: Optional[str] = None
    commercial_planning_level: Optional[str] = None
    rail_access_level: Optional[str] = None
    arterial_access_level: Optional[str] = None
    bus_access_level: Optional[str] = None
    operation_retrofit_potential_level: Optional[str] = None
    asset_rights_complexity_level: Optional[str] = None
    remark: Optional[str] = None
    is_confirmed: Optional[int] = None
    merchant_rows: Optional[List[SurveyMerchantRowIn]] = None
    competition_rows: Optional[List[SurveyCompetitionRowIn]] = None


class ProjectBaseInfoOut(ProjectBaseInfoBase):
    project_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    calc_warning: Optional[str] = None
    merchant_rows: Optional[List[SurveyMerchantRowOut]] = None
    competition_rows: Optional[List[SurveyCompetitionRowOut]] = None


class ScreeningCalcRequest(BaseModel):
    risk_note: Optional[str] = None
    manual_scores: Optional[Dict[str, int]] = None


class ScreeningIndicatorOut(BaseModel):
    key: str
    category: str
    name: str
    level: int
    mapped_score: int
    weight: float
    weighted_score: float
    note: str
    source_field: Optional[str] = None
    source_value: Optional[Any] = None
    manual_override: bool = False


class ProjectScreeningResultOut(BaseModel):
    id: str
    project_id: str
    total_score: Optional[float] = None
    conclusion: Optional[str] = None
    risk_note: Optional[str] = None
    overall_summary: Optional[str] = None
    score_version: Optional[str] = None
    data_source_breakdown: Optional[Dict[str, int]] = None
    calc_version: Optional[int] = None
    created_at: Optional[str] = None
    indicators: List[ScreeningIndicatorOut] = Field(default_factory=list)


class ScreeningHistoryKpis(BaseModel):
    total_projects: int
    screened_projects: int
    avg_score: Optional[float] = None
    high_recommend_rate: Optional[float] = None


class ScreeningHistoryItem(BaseModel):
    project_id: str
    project_name: str
    city: Optional[str] = None
    district: Optional[str] = None
    is_confirmed: int
    screening_status: str
    total_score: Optional[float] = None
    conclusion: Optional[str] = None
    calc_version: Optional[int] = None
    screening_created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ScreeningHistoryPagination(BaseModel):
    page: int
    page_size: int
    total: int


class ScreeningHistoryResponse(BaseModel):
    kpis: ScreeningHistoryKpis
    items: List[ScreeningHistoryItem] = Field(default_factory=list)
    pagination: ScreeningHistoryPagination


class OverviewMapKpisOut(BaseModel):
    total_points: int
    merchant_count: int
    competitor_count: int
    covered_district_count: int
    avg_rent_unit_price: Optional[float] = None
    median_rent_unit_price: Optional[float] = None
    avg_vacancy_rate: Optional[float] = None
    avg_daily_flow: Optional[float] = None


class OverviewMapPointOut(BaseModel):
    point_id: str
    point_type: str
    item_id: str
    project_id: str
    project_name: Optional[str] = None
    name: str
    city: str
    district: str
    address: str
    longitude: float
    latitude: float
    rent_unit_price: Optional[float] = None
    vacancy_rate: Optional[float] = None
    daily_flow: Optional[int] = None
    created_at: Optional[str] = None


class OverviewMapPointsResponse(BaseModel):
    items: List[OverviewMapPointOut] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    aggregates: Dict[str, int] = Field(default_factory=dict)


class OverviewMapPointDetailOut(BaseModel):
    point_id: str
    point_type: str
    project_id: str
    project_name: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class SurveyHistorySubmissionOut(BaseModel):
    submission_id: str
    project_id: str
    project_name: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    version: int
    merchant_count: int
    competitor_count: int
    total_count: int
    created_at: Optional[str] = None
    deleted: bool = False
    deleted_at: Optional[str] = None
    deleted_by: Optional[int] = None
    delete_reason: Optional[str] = None


class SurveyHistoryPointOut(BaseModel):
    point_id: str
    point_type: str
    item_id: str
    submission_id: str
    project_id: str
    project_name: Optional[str] = None
    name: str
    city: str
    district: str
    address: str
    created_at: Optional[str] = None
    deleted: bool = False
    deleted_at: Optional[str] = None
    deleted_by: Optional[int] = None
    delete_reason: Optional[str] = None


class SurveyHistorySummaryOut(BaseModel):
    total_submissions: int
    active_submissions: int
    deleted_submissions: int
    total_points: int
    active_points: int
    deleted_points: int


class SurveyHistoryResponse(BaseModel):
    summary: SurveyHistorySummaryOut
    submissions: List[SurveyHistorySubmissionOut] = Field(default_factory=list)
    points: List[SurveyHistoryPointOut] = Field(default_factory=list)
    page: int
    page_size: int
    total_points: int


class SurveyDeleteIn(BaseModel):
    reason: Optional[str] = None


class SurveyDeleteActionOut(BaseModel):
    ok: bool = True
    target: str
    id: str
    deleted: bool
    affected_count: int = 1
    message: Optional[str] = None


class MarketBulkActionIn(BaseModel):
    city: Optional[str] = None
    district: Optional[str] = None
    industry: Optional[str] = None
    type: str = Field(default="all", pattern="^(all|merchant|competitor)$")
    keyword: Optional[str] = None
    reason: Optional[str] = None


class MarketBulkActionOut(BaseModel):
    ok: bool = True
    action: str
    target: str = "items"
    affected_count: int = 0
    merchant_affected: int = 0
    competitor_affected: int = 0
    message: Optional[str] = None


class MarketMerchantRowIn(BaseModel):
    name: str
    category: str
    area_m2: float
    rent_unit_price: float
    daily_flow: int
    address: str
    city: Optional[str] = None
    district: Optional[str] = None
    note: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class MarketCompetitorRowIn(BaseModel):
    name: str
    scale_m2: float
    avg_rent_unit_price: float
    vacancy_rate: float
    business_type: str
    distance_km: float
    target_people: str
    address: str
    city: Optional[str] = None
    district: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class MarketSubmissionCreateIn(BaseModel):
    source_mode: str = Field(pattern="^(project|standalone)$")
    project_id: Optional[str] = None
    city: str
    district: str
    merchant_rows: List[MarketMerchantRowIn] = Field(default_factory=list)
    competitor_rows: List[MarketCompetitorRowIn] = Field(default_factory=list)


class MarketSubmissionCreateOut(BaseModel):
    submission_id: str
    source_mode: str
    project_id: Optional[str] = None
    city: str
    district: str
    merchant_count: int
    competitor_count: int
    created_at: Optional[str] = None


class MarketHistorySummaryOut(BaseModel):
    total_submissions: int
    active_submissions: int
    deleted_submissions: int
    total_points: int
    active_points: int
    deleted_points: int


class MarketHistorySubmissionOut(BaseModel):
    submission_id: str
    source_mode: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    city: str
    district: str
    created_at: Optional[str] = None
    merchant_count: int
    competitor_count: int
    total_count: int
    deleted: bool = False
    deleted_at: Optional[str] = None
    deleted_by: Optional[int] = None
    delete_reason: Optional[str] = None


class MarketHistoryPointOut(BaseModel):
    point_id: str
    point_type: str
    item_id: str
    submission_id: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    name: str
    city: str
    district: str
    industry: Optional[str] = None
    target_people: Optional[str] = None
    address: str
    created_at: Optional[str] = None
    deleted: bool = False
    deleted_at: Optional[str] = None
    deleted_by: Optional[int] = None
    delete_reason: Optional[str] = None


class MarketHistoryResponse(BaseModel):
    summary: MarketHistorySummaryOut
    submissions: List[MarketHistorySubmissionOut] = Field(default_factory=list)
    points: List[MarketHistoryPointOut] = Field(default_factory=list)
    page: int
    page_size: int
    total_points: int


class IntelKpisOut(BaseModel):
    total_count: int
    today_count: int
    pending_follow_up_count: int
    due_soon_count: int
    hit_rate: float


class IntelItemListOut(BaseModel):
    id: str
    item_type: str
    title: str
    source_name: str
    source_category: Optional[str] = None
    source_tags: List[str] = Field(default_factory=list)
    published_at: str
    city: Optional[str] = None
    district: Optional[str] = None
    summary: Optional[str] = None
    raw_url: Optional[str] = None
    budget_amount: Optional[float] = None
    deadline_at: Optional[str] = None
    issuer: Optional[str] = None
    matched_rule_count: int
    follow_up_status: str
    linked_project_count: int
    created_at: Optional[str] = None


class IntelItemsResponse(BaseModel):
    items: List[IntelItemListOut] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


class IntelLinkedProjectOut(BaseModel):
    project_id: str
    project_name: Optional[str] = None
    linked_at: Optional[str] = None
    link_type: str


class IntelItemDetailOut(BaseModel):
    id: str
    item_type: str
    title: str
    source_name: str
    source_category: Optional[str] = None
    source_tags: List[str] = Field(default_factory=list)
    published_at: str
    city: Optional[str] = None
    district: Optional[str] = None
    summary: Optional[str] = None
    raw_url: Optional[str] = None
    budget_amount: Optional[float] = None
    deadline_at: Optional[str] = None
    issuer: Optional[str] = None
    payload_json: Optional[str] = None
    matched_rule_count: int
    follow_up_status: str
    linked_projects: List[IntelLinkedProjectOut] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class IntelSyncRunIn(BaseModel):
    item_type: str = Field(default="all", pattern="^(all|news|tender)$")
    source_system: str = Field(default="bidmonitor", pattern="^(bidmonitor|folo|all)$")
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    payload_items: Optional[List[Dict[str, Any]]] = None


class IntelSyncRunOut(BaseModel):
    job_id: str
    source_system: str
    status: str
    pulled_count: int
    upserted_count: int
    deduped_count: int
    failed_count: int
    matched_rule_hits: int
    started_at: str
    ended_at: Optional[str] = None


class IntelSyncJobOut(BaseModel):
    id: str
    source_system: str
    trigger_type: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    pulled_count: int
    upserted_count: int
    deduped_count: int
    failed_count: int
    error_message: Optional[str] = None
    created_by: Optional[int] = None


class IntelLinkProjectIn(BaseModel):
    project_id: str
    link_type: str = Field(default="manual", pattern="^(manual|rule)$")


class IntelFollowUpIn(BaseModel):
    status: str = Field(pattern="^(none|pending|done|ignored)$")


class IntelLinkProjectOut(BaseModel):
    ok: bool = True
    intel_item_id: str
    project_id: str
    link_type: str


class IntelWatchRuleBase(BaseModel):
    name: str
    item_type: str = Field(default="all", pattern="^(all|news|tender)$")
    keywords: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    is_enabled: int = 1


class IntelWatchRuleCreate(IntelWatchRuleBase):
    pass


class IntelWatchRuleUpdate(BaseModel):
    name: Optional[str] = None
    item_type: Optional[str] = Field(default=None, pattern="^(all|news|tender)$")
    keywords: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    is_enabled: Optional[int] = None


class IntelWatchRuleOut(IntelWatchRuleBase):
    id: str
    created_by: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DataQualityOverviewOut(BaseModel):
    completeness_score: float
    geo_accuracy_score: float
    dedupe_health_score: float
    freshness_score: float
    overall_score: float
    sample_count: int


class DataQualityDistrictOut(BaseModel):
    district: str
    completeness_score: float
    geo_accuracy_score: float
    dedupe_health_score: float
    freshness_score: float
    overall_score: float
    sample_count: int


class CalcAssetOwnerRequest(BaseModel):
    target_rent: float
    target_occupancy: float
    invest_cost: float


class CalcYearlyOut(BaseModel):
    year_index: int
    year_label: str
    revenue: Optional[float] = None
    cost: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    tax: Optional[float] = None


class CalcSummaryOut(BaseModel):
    total_revenue: Optional[float] = None
    total_cost: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    tax_after_profit: Optional[float] = None


class CalcAssetOwnerOut(BaseModel):
    id: str
    project_id: str
    target_rent: float
    target_occupancy: float
    annual_rent_income: Optional[float] = None
    invest_cost: float
    roi: Optional[float] = None
    payback_year: Optional[float] = None
    calc_version: Optional[int] = None
    created_at: Optional[str] = None
    summary: Optional[CalcSummaryOut] = None
    yearly: List[CalcYearlyOut] = Field(default_factory=list)
    params_used: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    calc_basis: Optional[str] = None


class CalcInternalOperationRequest(BaseModel):
    service_fee_rate: float
    manage_fee_rate: float
    staff_cost: float
    other_cost: float


class CalcInternalOperationOut(BaseModel):
    id: str
    project_id: str
    service_fee_rate: float
    manage_fee_rate: float
    annual_rent_for_calc: Optional[float] = None
    service_income: Optional[float] = None
    manage_income: Optional[float] = None
    staff_cost: float
    other_cost: float
    total_income: Optional[float] = None
    total_cost: Optional[float] = None
    total_profit: Optional[float] = None
    profit_margin: Optional[float] = None
    calc_version: Optional[int] = None
    created_at: Optional[str] = None
    summary: Optional[CalcSummaryOut] = None
    yearly: List[CalcYearlyOut] = Field(default_factory=list)
    params_used: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    calc_basis: Optional[str] = None


class CalcMerchantRequest(BaseModel):
    shop_area: float
    shop_rent: float
    daily_flow: int
    avg_ticket: float
    annual_cost: float


class CalcMerchantOut(BaseModel):
    id: str
    project_id: str
    shop_area: float
    shop_rent: float
    daily_flow: int
    avg_ticket: float
    annual_revenue: Optional[float] = None
    annual_cost: float
    break_even_rent: Optional[float] = None
    calc_version: Optional[int] = None
    created_at: Optional[str] = None


class CalcAutoOverrides(BaseModel):
    rent_base: Optional[float] = None
    occupancy_curve: Optional[List[float]] = None
    rent_growth_curve: Optional[List[float]] = None
    leasing_commission_months: Optional[float] = None
    operation_commission_rate: Optional[float] = None


class CalcAutoRequest(BaseModel):
    overrides: Optional[CalcAutoOverrides] = None


class CalcAutoResultOut(BaseModel):
    summary: CalcSummaryOut
    yearly: List[CalcYearlyOut] = Field(default_factory=list)
    params_used: Dict[str, Any] = Field(default_factory=dict)
    source: str
    calc_basis: str


class CalcAutoResponse(BaseModel):
    project_id: str
    calc_version: int
    external: CalcAutoResultOut
    internal: CalcAutoResultOut


class CalcParamDefOut(BaseModel):
    key: str
    label: str
    type: str
    unit: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    description: Optional[str] = None
    default: Optional[Any] = None


class CalcConfigOut(BaseModel):
    calc_config_version: str
    planning_years: int
    defaults: Dict[str, Any]
    advanced_params: List[CalcParamDefOut] = Field(default_factory=list)
