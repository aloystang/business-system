"""核心资源模型：用户 / 品牌 / 项目 / 定位 / 匹配。"""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, DateTime, false, Float, ForeignKey, Integer, JSON, String, Text,
    true, UniqueConstraint, func, text,
)
from sqlalchemy.orm import relationship

from ..database import Base
from .base import utcnow

# 跨方言 server_default：false()/true() 在 Postgres 渲染 false/true、SQLite 渲染 0/1；
# func.now() 渲染 CURRENT_TIMESTAMP。
_FALSE = false()
_TRUE = true()
_NOW = func.now()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(64))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="admin")   # 主角色缓存（完整RBAC见 user_roles）
    email = Column(String(128))
    phone = Column(String(32))
    is_active = Column(Boolean, nullable=False, default=True, server_default=_TRUE)
    data_scope = Column(JSON)                                    # 数据范围隔离，NULL=全域
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, server_default=_NOW,
                        nullable=False)


class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True)
    brand_code = Column(String(64), unique=True, nullable=False, index=True)
    brand_name = Column(String(200), nullable=False)
    brand_short_name = Column(String(100))
    l1_category = Column(String(64))
    l2_category = Column(String(64))
    l3_category = Column(String(64))
    tags = Column(String(300))
    operating_status = Column(String(64))
    store_count = Column(Integer)
    hq_city = Column(String(120))
    brand_intro = Column(Text)
    cooperation_intent = Column(String(64))
    grade = Column(String(2))
    is_deleted = Column(Boolean, nullable=False, default=False, server_default=_FALSE)
    source_system = Column(String(64))
    source_record_id = Column(String(128))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    expansion = relationship("BrandExpansion", back_populates="brand", uselist=False,
                             cascade="all, delete-orphan")
    contacts = relationship("BrandContact", back_populates="brand",
                            cascade="all, delete-orphan")
    scores = relationship("BrandScore", back_populates="brand",
                          cascade="all, delete-orphan")


class BrandExpansion(Base):
    __tablename__ = "brand_expansion_requirements"
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), unique=True, nullable=False)
    target_cities = Column(String(300))
    acceptable_project_types = Column(String(300))
    accept_stadium_commercial = Column(Boolean)
    accept_new_project = Column(Boolean)
    area_min = Column(Float)
    area_max = Column(Float)
    power_req_kw = Column(Float)
    needs_gas = Column(Boolean)
    rent_tolerance = Column(String(120))
    property_preference = Column(String(200))   # 物业偏好：楼层/层高/临街等要求
    opening_plan = Column(String(100))          # 开店计划：签约后预计开业周期

    brand = relationship("Brand", back_populates="expansion")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    project_code = Column(String(64), unique=True, nullable=False, index=True)
    project_name = Column(String(200), nullable=False)
    project_short_name = Column(String(100))
    project_type = Column(String(64), nullable=False)
    project_status = Column(String(32), nullable=False)
    open_date = Column(String(20))
    asset_holder = Column(String(200))
    operator = Column(String(200))
    business_area_m2 = Column(Float)
    leasable_area_m2 = Column(Float)
    target_formats = Column(String(400))
    core_customers = Column(String(300))
    cooperation_will = Column(String(64))
    leasing_stage = Column(String(64))
    grade = Column(String(2))
    is_sensitive = Column(Boolean, nullable=False, default=False, server_default=_FALSE)
    is_deleted = Column(Boolean, nullable=False, default=False, server_default=_FALSE)
    source_system = Column(String(64))
    source_record_id = Column(String(128))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    location = relationship("ProjectLocation", back_populates="project", uselist=False,
                            cascade="all, delete-orphan")
    contacts = relationship("ProjectContact", back_populates="project",
                            cascade="all, delete-orphan")
    scores = relationship("ProjectScore", back_populates="project",
                          cascade="all, delete-orphan")


class ProjectLocation(Base):
    __tablename__ = "project_locations"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True, nullable=False)
    province = Column(String(64), nullable=False)
    city = Column(String(64), nullable=False)
    district = Column(String(64), nullable=False)
    address = Column(String(300), nullable=False)
    longitude = Column(Float)
    latitude = Column(Float)
    coordinate_system = Column(String(16), nullable=False, default="GCJ-02",
                               server_default=text("'GCJ-02'"))
    geocoding_status = Column(String(32), nullable=False, default="待定位",
                              server_default=text("'待定位'"))
    geocoding_provider = Column(String(32))
    manually_adjusted = Column(Boolean, nullable=False, default=False, server_default=_FALSE)

    project = relationship("Project", back_populates="location")


class Match(Base):
    __tablename__ = "brand_project_matches"
    __table_args__ = (UniqueConstraint("brand_id", "project_id", "rule_version",
                                       name="uq_match_brand_project_rule"),)
    id = Column(Integer, primary_key=True)
    match_code = Column(String(64))
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    dim_format = Column(Integer)
    dim_city_region = Column(Integer)
    dim_project_type = Column(Integer)
    dim_positioning_customer = Column(Integer)
    dim_property_condition = Column(Integer)
    dim_business_condition = Column(Integer)
    dim_expansion_plan = Column(Integer)
    dim_cooperation_will = Column(Integer)
    hard_gate_triggered = Column(Boolean, nullable=False, default=False, server_default=_FALSE)
    hard_gate_reason = Column(Text)
    weighted_score = Column(Float)
    data_coverage_rate = Column(Float)
    is_formal = Column(Boolean, nullable=False, default=True, server_default=_TRUE)
    match_grade = Column(String(16))
    satisfied_conditions = Column(Text)
    unsatisfied_conditions = Column(Text)
    pending_conditions = Column(Text)
    advantages = Column(Text)
    risks = Column(Text)
    recommend_reason = Column(Text)
    manual_adjust = Column(Float, nullable=False, default=0, server_default=text("0"))
    adjust_reason = Column(Text)
    final_score = Column(Float)
    priority = Column(String(16))
    rule_version = Column(String(32), nullable=False, default="v1.0",
                          server_default=text("'v1.0'"))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    brand = relationship("Brand")
    project = relationship("Project")
