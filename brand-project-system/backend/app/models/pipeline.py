"""匹配闭环：候选清单 / 清单条目 / 沟通记录 / 跟进任务。"""
from __future__ import annotations

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base
from .base import utcnow


class CandidateList(Base):
    __tablename__ = "candidate_lists"
    id = Column(Integer, primary_key=True)
    list_name = Column(String(200), nullable=False)
    owner_id = Column(Integer)
    target_project_id = Column(Integer, ForeignKey("projects.id"))
    description = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    items = relationship("CandidateListItem", back_populates="list",
                         cascade="all, delete-orphan")


class CandidateListItem(Base):
    __tablename__ = "candidate_list_items"
    __table_args__ = (UniqueConstraint("list_id", "brand_id", name="uq_candidate_list_brand"),)
    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey("candidate_lists.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    match_id = Column(Integer, ForeignKey("brand_project_matches.id"))
    item_status = Column(String(32), nullable=False, default="储备")
    note = Column(Text)
    added_by = Column(Integer)
    added_at = Column(DateTime, default=utcnow, nullable=False)

    list = relationship("CandidateList", back_populates="items")
    brand = relationship("Brand")


class CommunicationRecord(Base):
    __tablename__ = "communication_records"
    id = Column(Integer, primary_key=True)
    related_type = Column(String(16), nullable=False)   # brand/project/match
    brand_id = Column(Integer, ForeignKey("brands.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    match_id = Column(Integer, ForeignKey("brand_project_matches.id"))
    contact_name = Column(String(64))
    comm_date = Column(Date, nullable=False)
    channel = Column(String(32))
    summary = Column(Text)
    cooperation_will = Column(String(64))
    obstacle = Column(Text)
    next_action = Column(Text)
    owner_id = Column(Integer)
    plan_date = Column(Date)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class FollowupTask(Base):
    __tablename__ = "followup_tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    related_type = Column(String(16))
    brand_id = Column(Integer, ForeignKey("brands.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    match_id = Column(Integer, ForeignKey("brand_project_matches.id"))
    owner_id = Column(Integer, index=True)
    status = Column(String(16), nullable=False, default="待办")   # 待办/进行中/已完成/已取消
    priority = Column(String(16))
    plan_date = Column(Date)
    done_at = Column(DateTime)
    detail = Column(Text)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=utcnow, nullable=False)
