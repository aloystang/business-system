"""业态调改计划（逐铺位·单一现行计划）：记录每个铺位未来的调铺改铺安排。

区别于 assessment.py 的"评估"（现状打分→动作建议），本表是"计划"（要落地的目标业态/
品牌/预期租金/时间/状态），用于算现状业态构成 → 调改后预测（租金/坪效/出租率/NOI）。
"""
from __future__ import annotations

from sqlalchemy import (
    Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from ..database import Base
from .base import utcnow

_NOW = func.now()

# 调改动作枚举
ADJUST_ACTIONS = ["保留", "升级", "置换", "改造", "合并", "拆分", "新招商"]
PLAN_STATUSES = ["草案", "审批中", "已定", "执行中", "完成"]


class UnitAdjustmentPlan(Base):
    """铺位调改计划：每个铺位至多一条现行计划（unit_id 唯一）。"""
    __tablename__ = "unit_adjustment_plans"
    __table_args__ = (UniqueConstraint("unit_id", name="uq_adjust_plan_unit"),)

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False, index=True)
    action = Column(String(16), nullable=False)          # 见 ADJUST_ACTIONS
    from_format = Column(String(64))                     # 现业态快照（空置则空）
    to_format = Column(String(64))                       # 目标业态
    target_brand_id = Column(Integer, ForeignKey("brands.id"))   # 目标候选品牌，可空
    expected_rent = Column(Float)                        # 预期月租金（元/月）
    expected_rent_psm = Column(Float)                    # 预期坪效（元/㎡/月）
    plan_status = Column(String(16), nullable=False, default="草案",
                         server_default="草案")
    plan_date = Column(Date)                             # 计划落位/完成时间
    reason = Column(Text)
    owner = Column(String(64))
    created_at = Column(DateTime, default=utcnow, server_default=_NOW, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, server_default=_NOW,
                        nullable=False)

    unit = relationship("Unit")
    target_brand = relationship("Brand")
