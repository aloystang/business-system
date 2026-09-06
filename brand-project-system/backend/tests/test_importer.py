"""Excel 导入管线单元测试（内存工作簿 + 隔离内存库）。"""
from __future__ import annotations

import openpyxl
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Brand, Dictionary, Project
from app.services import importer


@pytest.fixture
def db():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng, future=True)()
    for label in ["购物中心", "商业街区"]:
        s.add(Dictionary(dict_type="project_type", code=label, label=label))
    for label in ["招商中", "已开业"]:
        s.add(Dictionary(dict_type="project_status", code=label, label=label))
    s.commit()
    yield s
    s.close()


def _workbook():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    ps = wb.create_sheet("5-项目档案")
    ps.append(["project_code", "project_name", "project_type", "project_status",
               "province", "city", "district", "address"])
    ps.append(["P-100", "悦荟城", "购物中心", "招商中", "重庆市", "重庆市", "两江新区", "龙兴"])
    ps.append(["", "缺编码", "购物中心", "招商中", "重庆市", "重庆市", "两江新区", "x"])
    ps.append(["P-101", "枚举错", "综合体", "招商中", "重庆市", "重庆市", "两江新区", "x"])
    ps.append(["P-100", "重复码", "购物中心", "招商中", "重庆市", "重庆市", "两江新区", "x"])
    bs = wb.create_sheet("1-品牌档案")
    bs.append(["brand_code", "brand_name", "l1_业态"])
    bs.append(["B-100", "迪卡侬", "零售"])
    bs.append(["B-101", "", "零售"])          # 缺名称
    return wb


def test_validate_counts_and_errors(db):
    report, parsed = importer.validate(_workbook(), db)
    proj, brand = report.summary["projects"], report.summary["brands"]
    assert (proj.total, proj.valid, proj.error) == (4, 1, 3)
    assert (brand.total, brand.valid, brand.error) == (2, 1, 1)
    fields = {(e.field) for e in report.errors}
    assert "project_code" in fields          # 必填缺失
    assert "project_type" in fields          # 枚举非法
    assert len(parsed["projects"]) == 1 and len(parsed["brands"]) == 1


class _FailedGeocode:
    """离线桩：地址解析永远失败，避免单测联网打高德。"""
    ok = False
    provider = "test"


@pytest.fixture
def offline_geocode(monkeypatch):
    monkeypatch.setattr(importer, "geocode_address", lambda *a, **k: _FailedGeocode())


def test_commit_writes_rows_and_collects_geocode_failures(db, offline_geocode):
    report, parsed = importer.validate(_workbook(), db)
    importer.commit(parsed, db, report)
    db.commit()
    assert db.query(Project).filter(Project.project_code == "P-100").count() == 1
    assert db.query(Brand).filter(Brand.brand_code == "B-100").count() == 1
    b = db.query(Brand).filter(Brand.brand_code == "B-100").first()
    assert b.source_system == "excel_import" and b.l1_category == "零售"
    # 地址解析失败 → 进 geocode_failed（离线桩，不依赖高德 Key）
    assert any(g["project_code"] == "P-100" for g in report.geocode_failed)


def test_commit_is_idempotent(db, offline_geocode):
    report, parsed = importer.validate(_workbook(), db)
    importer.commit(parsed, db, report)
    db.commit()
    # 二次导入同一编码不新增
    report2, parsed2 = importer.validate(_workbook(), db)
    importer.commit(parsed2, db, report2)
    db.commit()
    assert db.query(Project).filter(Project.project_code == "P-100").count() == 1
