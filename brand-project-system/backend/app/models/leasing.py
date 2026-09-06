"""出租经营域：铺位 / 商户 / 租约 / 收费欠租 / 项目成本。

对应业务模板 05/08/09/10 + 新增「项目月度成本台账」（模板无，用于算 NOI 经营利润）。
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, Date, DateTime, false, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from ..database import Base
from .base import utcnow

_NOW = func.now()


class Unit(Base):
    """铺位主数据 + 工程条件（模板 05）。"""
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("project_id", "unit_code", name="uq_unit_project_code"),)
    id = Column(Integer, primary_key=True)
    unit_code = Column(String(64), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    building = Column(String(64))
    floor = Column(String(32))
    name = Column(String(120))
    unit_type = Column(String(64))
    building_area_m2 = Column(Float)
    rentable_area_m2 = Column(Float)          # 计租面积
    frontage_m = Column(Float)
    depth_m = Column(Float)
    height_m = Column(Float)
    power_kw = Column(Float)
    has_water = Column(Boolean)
    has_drainage = Column(Boolean)
    has_grease_trap = Column(Boolean)
    has_exhaust = Column(Boolean)
    has_gas = Column(Boolean)
    external_unit = Column(String(120))       # 外机位条件
    loading = Column(String(120))             # 卸货条件
    streetfront = Column(String(120))         # 临街条件
    display_face = Column(String(120))        # 展示面
    fire_zone = Column(String(64))            # 防火分区
    status = Column(String(16), nullable=False, default="空置", server_default="空置")  # 空置/在租/自营/装修
    grade = Column(String(8))
    source_system = Column(String(64))
    source_record_id = Column(String(128))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    project = relationship("Project")


class Merchant(Base):
    """商户主数据（模板 08）：当前在租/自营/历史商户。"""
    __tablename__ = "merchants"
    id = Column(Integer, primary_key=True)
    merchant_code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id"), index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), index=True)
    contract_entity = Column(String(200))     # 合同主体
    contact_name = Column(String(64))
    contact_phone = Column(String(32))
    business_format = Column(String(64))      # 当前业态
    open_date = Column(Date)
    operating_status = Column(String(16), nullable=False, default="在营", server_default="在营")
    latest_assessment = Column(String(64))
    source_system = Column(String(64))
    source_record_id = Column(String(128))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    brand = relationship("Brand")
    project = relationship("Project")
    unit = relationship("Unit")


class Lease(Base):
    """合同租约台账（模板 09）。"""
    __tablename__ = "leases"
    id = Column(Integer, primary_key=True)
    lease_code = Column(String(64), unique=True, nullable=False, index=True)
    contract_no = Column(String(64))
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    rent_mode = Column(String(32))            # 固定/固定+提成/提成/纯扣点
    base_rent = Column(Float)                 # 月基础租金
    sales_commission_pct = Column(Float)      # 销售扣点 %
    management_fee = Column(Float)            # 月物业费
    deposit = Column(Float)
    free_rent_days = Column(Integer)
    increment_rule = Column(String(120))
    renewal_status = Column(String(32))
    alert_days = Column(Integer, default=90, server_default="90")
    lease_status = Column(String(16), nullable=False, default="生效", server_default="生效")  # 生效/到期/终止
    source_system = Column(String(64))
    source_record_id = Column(String(128))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    merchant = relationship("Merchant")
    unit = relationship("Unit")


class Receivable(Base):
    """收费与欠租台账（模板 10）：按租约+费项+账期。"""
    __tablename__ = "receivables"
    id = Column(Integer, primary_key=True)
    receivable_code = Column(String(64), unique=True, nullable=False, index=True)
    lease_id = Column(Integer, ForeignKey("leases.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)  # 冗余便于聚合
    fee_item = Column(String(32), nullable=False)      # 租金/物业费/水电代收/推广费/滞纳金
    period = Column(String(7), nullable=False, index=True)  # 账期 YYYY-MM
    due_date = Column(Date)
    amount_due = Column(Float, nullable=False, default=0, server_default="0")
    amount_received = Column(Float, nullable=False, default=0, server_default="0")
    prepay_offset = Column(Float, nullable=False, default=0, server_default="0")
    arrears = Column(Float, nullable=False, default=0, server_default="0")     # 欠租=应收-实收-预收抵扣
    overdue_days = Column(Integer, default=0, server_default="0")
    aging = Column(String(16))                          # 账龄档：0-30/30-60/60-90/90+
    collect_status = Column(String(16))                 # 已结清/催收中/欠费
    owner = Column(String(64))
    last_follow_date = Column(Date)
    next_follow_date = Column(Date)
    remark = Column(Text)
    source_system = Column(String(64))
    source_record_id = Column(String(128))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    lease = relationship("Lease")


class ProjectCost(Base):
    """项目月度成本台账（模板无 · 新增）：用于算 NOI 经营利润。"""
    __tablename__ = "project_costs"
    __table_args__ = (
        UniqueConstraint("project_id", "period", "cost_type", name="uq_cost_project_period_type"),
    )
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    period = Column(String(7), nullable=False, index=True)   # YYYY-MM
    cost_type = Column(String(32), nullable=False)           # 物业成本/水电能耗/人力/维修/其他
    amount = Column(Float, nullable=False, default=0, server_default="0")
    remark = Column(Text)
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    project = relationship("Project")
