"""字典与分类：通用枚举 / 三级业态树 / 标签。"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, SmallInteger, String, Text

from ..database import Base


class Dictionary(Base):
    __tablename__ = "dictionaries"
    id = Column(Integer, primary_key=True)
    dict_type = Column(String(64), nullable=False, index=True)
    code = Column(String(64), nullable=False)
    label = Column(String(128), nullable=False)
    sort_no = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    remark = Column(Text)


class BrandCategory(Base):
    __tablename__ = "brand_categories"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("brand_categories.id"))
    level = Column(SmallInteger, nullable=False)   # 1/2/3
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    sort_no = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)


class BrandTag(Base):
    __tablename__ = "brand_tags"
    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    sort_no = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)


class ProjectTag(Base):
    __tablename__ = "project_tags"
    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    sort_no = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
