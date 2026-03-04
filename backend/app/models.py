from __future__ import annotations

from datetime import datetime, date
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    pm = "pm"
    member = "member"
    viewer = "viewer"


class Stage(str, Enum):
    evaluation = "evaluation"
    estimation = "estimation"
    initiation = "initiation"
    planning = "planning"
    bidding = "bidding"
    contracting = "contracting"
    preopen = "preopen"
    operation = "operation"
    review = "review"


class IssueCategory(str, Enum):
    risk = "risk"
    complaint = "complaint"
    public_opinion = "public_opinion"
    other = "other"


class IssuePriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IssueStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class IntakeStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SqlEnum(UserRole, native_enum=False), default=UserRole.member, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    region = Column(String(100), nullable=False)
    asset_type = Column(String(100), nullable=False)
    client_name = Column(String(200), nullable=False)
    address = Column(String(255), nullable=True)
    area_m2 = Column(Float, nullable=True)
    population_index = Column(String(100), nullable=True)
    current_stage = Column(SqlEnum(Stage, native_enum=False), default=Stage.evaluation, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    external_summary = Column(Text, nullable=True)
    external_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", back_populates="projects")
    transitions = relationship("StageTransition", back_populates="project", cascade="all, delete-orphan")
    deliverables = relationship("Deliverable", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")


class StageTransition(Base):
    __tablename__ = "stage_transitions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    from_stage = Column(String(50), nullable=False)
    to_stage = Column(String(50), nullable=False)
    transitioned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    transitioned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    note = Column(Text, nullable=True)

    project = relationship("Project", back_populates="transitions")


class Deliverable(Base):
    __tablename__ = "deliverables"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    stage = Column(String(50), nullable=False)
    type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    is_external_visible = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="deliverables")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category = Column(SqlEnum(IssueCategory, native_enum=False), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SqlEnum(IssuePriority, native_enum=False), default=IssuePriority.medium, nullable=False)
    status = Column(SqlEnum(IssueStatus, native_enum=False), default=IssueStatus.open, nullable=False)
    assignee_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    escalated = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="issues")


class ProjectMetric(Base):
    __tablename__ = "project_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    metric_type = Column(String(20), nullable=False)
    contract_amount = Column(Float, nullable=True)
    cost_budget = Column(Float, nullable=True)
    cost_actual = Column(Float, nullable=True)
    occupancy_target = Column(Float, nullable=True)
    occupancy_actual = Column(Float, nullable=True)
    complaint_count = Column(Integer, nullable=True)
    period = Column(String(20), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ExternalShare(Base):
    __tablename__ = "external_shares"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=True)
    metadata_json = Column(Text, nullable=True)
    ip = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectIntake(Base):
    __tablename__ = "project_intakes"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(Text, nullable=False)
    status = Column(SqlEnum(IntakeStatus, native_enum=False), default=IntakeStatus.pending)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProjectProfile(Base):
    __tablename__ = "project_profiles"

    id = Column(Integer, primary_key=True, index=True)
    intake_id = Column(Integer, ForeignKey("project_intakes.id"), nullable=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    location_desc = Column(Text, nullable=True)
    total_area_m2 = Column(Float, nullable=True)
    rentable_area_m2 = Column(Float, nullable=True)
    core_area_m2 = Column(Float, nullable=True)
    distribution_form = Column(String(50), nullable=True)
    ownership_structure = Column(String(50), nullable=True)
    vacancy_rate = Column(Float, nullable=True)
    rent_range = Column(String(100), nullable=True)
    primary_business_types = Column(Text, nullable=True)
    competitors = Column(Text, nullable=True)
    competition_intensity = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ProjectBaseInfo(Base):
    __tablename__ = "project_base_info"

    project_id = Column(String(64), primary_key=True, index=True)
    project_name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    location_desc = Column(Text, nullable=True)
    total_area = Column(Float, nullable=False)
    rentable_area = Column(Float, nullable=True)
    core_area = Column(Float, nullable=True)
    asset_distribution = Column(String(20), nullable=False)
    ownership_structure = Column(String(20), nullable=False)
    vacancy_rate = Column(Float, nullable=True)
    rent_min = Column(Float, nullable=True)
    rent_max = Column(Float, nullable=True)
    main_business_type = Column(String(200), nullable=True)
    competitor_list = Column(Text, nullable=True)
    competition_level = Column(String(10), nullable=False)
    city_population_10k = Column(Float, nullable=True)
    population_5km_10k = Column(Float, nullable=True)
    population_3km_10k = Column(Float, nullable=True)
    city_circle_level = Column(String(100), nullable=True)
    competition_market_level = Column(String(150), nullable=True)
    housing_price_5km = Column(Float, nullable=True)
    disposable_income_10k = Column(Float, nullable=True)
    regional_function_level = Column(String(100), nullable=True)
    commercial_planning_level = Column(String(100), nullable=True)
    rail_access_level = Column(String(100), nullable=True)
    arterial_access_level = Column(String(100), nullable=True)
    bus_access_level = Column(String(120), nullable=True)
    operation_retrofit_potential_level = Column(String(100), nullable=True)
    asset_rights_complexity_level = Column(String(100), nullable=True)
    remark = Column(Text, nullable=True)
    is_confirmed = Column(Integer, nullable=False, default=0)
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)


class GeocodeCache(Base):
    __tablename__ = "geocode_cache"

    id = Column(Integer, primary_key=True, index=True)
    full_address = Column(Text, unique=True, index=True, nullable=False)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    created_at = Column(Text, nullable=True)


class SurveySubmission(Base):
    __tablename__ = "survey_submission"

    id = Column(String(80), primary_key=True, index=True)
    project_id = Column(String(64), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(Text, nullable=True)
    delete_reason = Column(Text, nullable=True)


class SurveyMerchantItem(Base):
    __tablename__ = "survey_merchant_item"

    id = Column(String(100), primary_key=True, index=True)
    submission_id = Column(String(80), nullable=False, index=True)
    project_id = Column(String(64), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    area_m2 = Column(Float, nullable=False)
    rent_unit_price = Column(Float, nullable=False)
    daily_flow = Column(Integer, nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    note = Column(Text, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    geocode_status = Column(String(30), nullable=False, default="pending")
    geocode_message = Column(String(255), nullable=True)
    geocoded_at = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(Text, nullable=True)
    delete_reason = Column(Text, nullable=True)


class SurveyCompetitorItem(Base):
    __tablename__ = "survey_competitor_item"

    id = Column(String(100), primary_key=True, index=True)
    submission_id = Column(String(80), nullable=False, index=True)
    project_id = Column(String(64), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    scale_m2 = Column(Float, nullable=False)
    avg_rent_unit_price = Column(Float, nullable=False)
    vacancy_rate = Column(Float, nullable=False)
    business_type = Column(String(120), nullable=False)
    distance_km = Column(Float, nullable=False)
    target_people = Column(String(200), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    geocode_status = Column(String(30), nullable=False, default="pending")
    geocode_message = Column(String(255), nullable=True)
    geocoded_at = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(Text, nullable=True)
    delete_reason = Column(Text, nullable=True)


class MarketSubmission(Base):
    __tablename__ = "market_submission"

    id = Column(String(80), primary_key=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    source_mode = Column(String(20), nullable=False, default="standalone")
    project_id = Column(String(64), nullable=True, index=True)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(Text, nullable=True)
    delete_reason = Column(Text, nullable=True)


class MarketMerchantItem(Base):
    __tablename__ = "market_merchant_item"

    id = Column(String(100), primary_key=True, index=True)
    submission_id = Column(String(80), nullable=False, index=True)
    project_id = Column(String(64), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    area_m2 = Column(Float, nullable=False)
    rent_unit_price = Column(Float, nullable=False)
    daily_flow = Column(Integer, nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    note = Column(Text, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    geocode_status = Column(String(30), nullable=False, default="pending")
    geocode_message = Column(String(255), nullable=True)
    geocoded_at = Column(Text, nullable=True)
    signature = Column(String(255), nullable=False, index=True)
    created_at = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(Text, nullable=True)
    delete_reason = Column(Text, nullable=True)


class MarketCompetitorItem(Base):
    __tablename__ = "market_competitor_item"

    id = Column(String(100), primary_key=True, index=True)
    submission_id = Column(String(80), nullable=False, index=True)
    project_id = Column(String(64), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    scale_m2 = Column(Float, nullable=False)
    avg_rent_unit_price = Column(Float, nullable=False)
    vacancy_rate = Column(Float, nullable=False)
    business_type = Column(String(120), nullable=False)
    distance_km = Column(Float, nullable=False)
    target_people = Column(String(200), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    geocode_status = Column(String(30), nullable=False, default="pending")
    geocode_message = Column(String(255), nullable=True)
    geocoded_at = Column(Text, nullable=True)
    signature = Column(String(255), nullable=False, index=True)
    created_at = Column(Text, nullable=True)
    deleted = Column(Integer, nullable=False, default=0)
    deleted_by = Column(Integer, nullable=True)
    deleted_at = Column(Text, nullable=True)
    delete_reason = Column(Text, nullable=True)


class ProjectSnapshot(Base):
    __tablename__ = "project_snapshot"

    id = Column(String(80), primary_key=True, index=True)
    project_id = Column(String(64), nullable=False, index=True)
    snapshot_type = Column(String(40), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    payload_json = Column(Text, nullable=False)
    created_by = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=True)


class MetricDictionary(Base):
    __tablename__ = "metric_dictionary"

    id = Column(String(80), primary_key=True, index=True)
    metric_key = Column(String(100), nullable=False, unique=True, index=True)
    metric_name = Column(String(120), nullable=False)
    metric_unit = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    metric_version = Column(String(50), nullable=True, default="v1")
    enabled = Column(Integer, nullable=False, default=1)
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)


class IntelSource(Base):
    __tablename__ = "intel_source"

    id = Column(String(80), primary_key=True, index=True)
    source_name = Column(String(150), nullable=False, unique=True, index=True)
    source_type = Column(String(20), nullable=False)  # news | tender
    source_url = Column(String(500), nullable=True)
    is_enabled = Column(Integer, nullable=False, default=1)
    sync_interval_hours = Column(Integer, nullable=False, default=6)
    last_success_at = Column(Text, nullable=True)
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)


class IntelItem(Base):
    __tablename__ = "intel_item"

    id = Column(String(80), primary_key=True, index=True)
    item_type = Column(String(20), nullable=False, index=True)  # news | tender
    title = Column(String(500), nullable=False, index=True)
    source_name = Column(String(150), nullable=False, index=True)
    published_at = Column(Text, nullable=False, index=True)
    city = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    summary = Column(Text, nullable=True)
    raw_url = Column(String(1000), nullable=True)
    budget_amount = Column(Float, nullable=True)
    deadline_at = Column(Text, nullable=True)
    issuer = Column(String(255), nullable=True)
    dedupe_key = Column(String(255), nullable=False, unique=True, index=True)
    payload_json = Column(Text, nullable=True)
    matched_rule_count = Column(Integer, nullable=False, default=0)
    follow_up_status = Column(String(20), nullable=False, default="none")  # none | pending | done | ignored
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)


class IntelSyncJob(Base):
    __tablename__ = "intel_sync_job"

    id = Column(String(80), primary_key=True, index=True)
    trigger_type = Column(String(20), nullable=False, default="manual")  # manual | scheduled
    started_at = Column(Text, nullable=False)
    ended_at = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running | success | failed
    window_start = Column(Text, nullable=True)
    window_end = Column(Text, nullable=True)
    pulled_count = Column(Integer, nullable=False, default=0)
    upserted_count = Column(Integer, nullable=False, default=0)
    deduped_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    source_system = Column(String(50), nullable=False, default="bidmonitor")
    details_json = Column(Text, nullable=True)


class IntelProjectLink(Base):
    __tablename__ = "intel_project_link"

    id = Column(String(80), primary_key=True, index=True)
    intel_item_id = Column(String(80), nullable=False, index=True)
    project_id = Column(String(64), nullable=False, index=True)
    link_type = Column(String(20), nullable=False, default="manual")  # manual | rule
    created_by = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=True)


class IntelWatchRule(Base):
    __tablename__ = "intel_watch_rule"

    id = Column(String(80), primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    item_type = Column(String(20), nullable=False, default="all")  # all | news | tender
    keywords = Column(Text, nullable=True)  # comma-separated keywords
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    is_enabled = Column(Integer, nullable=False, default=1)
    created_by = Column(Integer, nullable=False)
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)


class ProjectScreeningResult(Base):
    __tablename__ = "project_screening_result"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), nullable=False)
    total_score = Column(Float, nullable=True)
    conclusion = Column(String(20), nullable=True)
    risk_note = Column(Text, nullable=True)
    overall_summary = Column(Text, nullable=True)
    score_version = Column(String(40), nullable=True)
    data_source_breakdown = Column(Text, nullable=True)
    calc_version = Column(Integer, nullable=True, default=1)
    created_at = Column(Text, nullable=True)


class ProjectScreeningDetail(Base):
    __tablename__ = "project_screening_detail"

    id = Column(String(128), primary_key=True, index=True)
    result_id = Column(String(64), nullable=False)
    project_id = Column(String(64), nullable=False)
    indicator_key = Column(String(64), nullable=False)
    category = Column(String(50), nullable=False)
    indicator_name = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)
    mapped_score = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    weighted_score = Column(Float, nullable=False)
    note = Column(String(255), nullable=True)
    source_field = Column(String(100), nullable=True)
    source_value = Column(Text, nullable=True)
    manual_override = Column(Boolean, default=False, nullable=False)


class CalcAssetOwner(Base):
    __tablename__ = "calc_asset_owner"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), nullable=False)
    target_rent = Column(Float, nullable=True)
    target_occupancy = Column(Float, nullable=True)
    annual_rent_income = Column(Float, nullable=True)
    invest_cost = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    payback_year = Column(Float, nullable=True)
    details_json = Column(Text, nullable=True)
    params_json = Column(Text, nullable=True)
    calc_basis = Column(String(40), nullable=True)
    calc_version = Column(Integer, nullable=True, default=1)
    created_at = Column(Text, nullable=True)


class CalcInternalOperation(Base):
    __tablename__ = "calc_internal_operation"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), nullable=False)
    service_fee_rate = Column(Float, nullable=True)
    manage_fee_rate = Column(Float, nullable=True)
    annual_rent_for_calc = Column(Float, nullable=True)
    service_income = Column(Float, nullable=True)
    manage_income = Column(Float, nullable=True)
    staff_cost = Column(Float, nullable=True)
    other_cost = Column(Float, nullable=True)
    total_income = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    total_profit = Column(Float, nullable=True)
    profit_margin = Column(Float, nullable=True)
    details_json = Column(Text, nullable=True)
    params_json = Column(Text, nullable=True)
    calc_basis = Column(String(40), nullable=True)
    calc_version = Column(Integer, nullable=True, default=1)
    created_at = Column(Text, nullable=True)


class CalcMerchant(Base):
    __tablename__ = "calc_merchant"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(String(64), nullable=False)
    shop_area = Column(Float, nullable=True)
    shop_rent = Column(Float, nullable=True)
    daily_flow = Column(Integer, nullable=True)
    avg_ticket = Column(Float, nullable=True)
    annual_revenue = Column(Float, nullable=True)
    annual_cost = Column(Float, nullable=True)
    break_even_rent = Column(Float, nullable=True)
    calc_version = Column(Integer, nullable=True, default=1)
    created_at = Column(Text, nullable=True)
