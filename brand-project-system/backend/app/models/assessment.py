"""铺位级匹配（模板 12）与商户盘点评估（模板 13）。"""
from __future__ import annotations

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from ..database import Base
from .base import utcnow

_NOW = func.now()


class UnitBrandMatch(Base):
    """品牌×铺位匹配矩阵（模板 12）：五维各 0-20，输出改造建议与招商结论。"""
    __tablename__ = "unit_brand_matches"
    __table_args__ = (
        UniqueConstraint("unit_id", "brand_id", name="uq_unit_brand_match"),
    )
    id = Column(Integer, primary_key=True)
    match_code = Column(String(64))
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    dim_format = Column(Integer)        # 业态匹配 0-20
    dim_property = Column(Integer)      # 物业匹配
    dim_project = Column(Integer)       # 项目匹配
    dim_business = Column(Integer)      # 商务匹配
    dim_will = Column(Integer)          # 合作意愿
    total = Column(Integer)
    grade = Column(String(16))
    condition_gap = Column(Text)        # 条件差异
    reno_suggestion = Column(Text)      # 改造建议
    leasing_suggestion = Column(Text)   # 招商建议
    match_status = Column(String(16))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    unit = relationship("Unit")
    brand = relationship("Brand")


class MerchantAssessment(Base):
    """现有商户盘点与提档评估（模板 13）：四维各 0-25，输出升级/维持/置换。"""
    __tablename__ = "merchant_assessments"
    id = Column(Integer, primary_key=True)
    assess_code = Column(String(64), unique=True, nullable=False, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    dim_format_contribution = Column(Integer)   # 业态贡献 0-25
    dim_rent_level = Column(Integer)            # 租金水平
    dim_operation_quality = Column(Integer)     # 经营质量
    dim_brand_grade = Column(Integer)           # 品牌能级
    total = Column(Integer)
    conclusion = Column(String(32))            # 评估结论
    action = Column(String(16))                # 升级/维持/置换
    candidate_brand_id = Column(Integer, ForeignKey("brands.id"))
    assess_date = Column(Date)
    assessor = Column(String(64))
    note = Column(Text)
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)

    merchant = relationship("Merchant")
