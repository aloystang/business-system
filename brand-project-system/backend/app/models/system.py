"""系统支撑：导入批次 / 审核记录 / 操作日志。"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from ..database import Base
from .base import utcnow


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id = Column(Integer, primary_key=True)
    batch_no = Column(String(64), unique=True, nullable=False, index=True)
    template_version = Column(String(32))
    file_name = Column(String(300))
    status = Column(String(16), nullable=False, default="校验中")  # 校验中/待确认/已导入/已回滚/失败
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    dry_run = Column(Boolean, nullable=False, default=True)
    result_summary = Column(JSON)
    error_detail = Column(JSON)
    geocode_failed = Column(JSON)
    operator_id = Column(Integer)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    committed_at = Column(DateTime)


class ApprovalRecord(Base):
    __tablename__ = "approval_records"
    id = Column(Integer, primary_key=True)
    target_type = Column(String(32), nullable=False)   # brand/project/brand_score/import_batch
    target_id = Column(Integer, nullable=False)
    action = Column(String(32), nullable=False, default="submit")
    status = Column(String(16), nullable=False, default="待审核")  # 待审核/通过/驳回
    submitter_id = Column(Integer)
    approver_id = Column(Integer)
    comment = Column(Text)
    submitted_at = Column(DateTime, default=utcnow, nullable=False)
    decided_at = Column(DateTime)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, index=True)
    actor_name = Column(String(64))
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64))
    detail = Column(JSON)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
