"""联系人与评分：品牌/项目 联系人、五维评分（保留历史版本）。"""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, SmallInteger, String, Text,
)
from sqlalchemy.orm import relationship

from ..database import Base
from .base import utcnow


class BrandContact(Base):
    __tablename__ = "brand_contacts"
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False, index=True)
    contact_name = Column(String(64), nullable=False)
    dept = Column(String(120))
    title = Column(String(120))
    mobile = Column(String(32))
    wechat = Column(String(64))
    email = Column(String(128))
    region = Column(String(120))
    is_primary = Column(Boolean, nullable=False, default=False)
    valid_status = Column(String(32), nullable=False, default="有效")
    cooperation_intent = Column(String(64))
    next_action = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    brand = relationship("Brand", back_populates="contacts")


class ProjectContact(Base):
    __tablename__ = "project_contacts"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    contact_name = Column(String(64), nullable=False)
    party_type = Column(String(32))
    dept = Column(String(120))
    title = Column(String(120))
    mobile = Column(String(32))
    wechat = Column(String(64))
    email = Column(String(128))
    is_primary = Column(Boolean, nullable=False, default=False)
    valid_status = Column(String(32), nullable=False, default="有效")
    created_at = Column(DateTime, default=utcnow, nullable=False)

    project = relationship("Project", back_populates="contacts")


class BrandScore(Base):
    __tablename__ = "brand_scores"
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False, index=True)
    score_market_influence = Column(SmallInteger)
    score_tenant_capability = Column(SmallInteger)
    score_growth_potential = Column(SmallInteger)
    score_credit = Column(SmallInteger)
    score_cooperation_will = Column(SmallInteger)
    total_score = Column(SmallInteger)
    grade = Column(String(2))
    basis = Column(Text)
    scorer_id = Column(Integer)
    scored_at = Column(DateTime, default=utcnow, nullable=False)
    rule_version = Column(String(32), nullable=False, default="v1.0")
    is_current = Column(Boolean, nullable=False, default=True)

    brand = relationship("Brand", back_populates="scores")


class ProjectScore(Base):
    __tablename__ = "project_scores"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    score_location_traffic = Column(SmallInteger)
    score_scale_condition = Column(SmallInteger)
    score_positioning_customer = Column(SmallInteger)
    score_operation_resource = Column(SmallInteger)
    score_cooperation_opportunity = Column(SmallInteger)
    total_score = Column(SmallInteger)
    grade = Column(String(2))
    basis = Column(Text)
    scorer_id = Column(Integer)
    scored_at = Column(DateTime, default=utcnow, nullable=False)
    rule_version = Column(String(32), nullable=False, default="v1.0")
    is_current = Column(Boolean, nullable=False, default=True)

    project = relationship("Project", back_populates="scores")
