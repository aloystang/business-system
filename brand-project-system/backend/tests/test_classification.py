"""业态/状态口径服务单测（隔离内存库）+ 项目类型 API 校验。"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import BrandCategory, Dictionary, Project, Unit
from app.services import classification as cls
from app.services.classification import ClassificationError


@pytest.fixture
def cdb():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng, future=True)()
    # 一条业态路径：零售 → 服饰鞋包 → 运动户外
    n1 = BrandCategory(parent_id=None, level=1, code="L1", name="零售", sort_no=1)
    s.add(n1); s.flush()
    n2 = BrandCategory(parent_id=n1.id, level=2, code="L1-1", name="服饰鞋包", sort_no=1)
    s.add(n2); s.flush()
    s.add(BrandCategory(parent_id=n2.id, level=3, code="L1-1-1", name="运动户外", sort_no=1))
    for label in ["体育场馆商业", "商业街区"]:
        s.add(Dictionary(dict_type="project_type", code=label, label=label))
    for label in ["招商中", "已开业", "筹备"]:
        s.add(Dictionary(dict_type="project_status", code=label, label=label))
    s.commit()
    yield s
    s.close()


# ---------- 品牌三级业态树校验 ----------

def test_valid_category_path_passes(cdb):
    cls.validate_brand_category(cdb, "零售", "服饰鞋包", "运动户外")  # 不抛异常


def test_unknown_l1_raises(cdb):
    with pytest.raises(ClassificationError):
        cls.validate_brand_category(cdb, "餐饮", None, None)


def test_l3_not_under_l2_raises(cdb):
    with pytest.raises(ClassificationError):
        cls.validate_brand_category(cdb, "零售", "服饰鞋包", "火锅")


def test_skip_level_raises(cdb):
    with pytest.raises(ClassificationError):
        cls.validate_brand_category(cdb, "零售", None, "运动户外")


def test_empty_tree_is_noop():
    eng = create_engine("sqlite://", poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng, future=True)()
    cls.validate_brand_category(s, "任意", "随便", "都行")  # 树为空 → 不校验
    s.close()


# ---------- 字典枚举校验 ----------

def test_project_type_rejects_unknown(cdb):
    with pytest.raises(ClassificationError):
        cls.validate_project_type(cdb, "不存在的类型")


def test_project_type_accepts_known(cdb):
    cls.validate_project_type(cdb, "商业街区")


# ---------- 状态自动重分 ----------

def _project(cdb, code, status):
    p = Project(project_code=code, project_name=code, project_type="商业街区",
                project_status=status)
    cdb.add(p); cdb.flush()
    return p


def test_status_becomes_operating_with_active_unit(cdb):
    p = _project(cdb, "P-OP", "招商中")
    cdb.add(Unit(unit_code="U1", project_id=p.id, status="在租"))
    cdb.flush()
    assert cls.derive_project_status(cdb, p) == "已开业"


def test_status_stays_leasing_without_activity(cdb):
    p = _project(cdb, "P-EMPTY", "招商中")
    cdb.add(Unit(unit_code="U2", project_id=p.id, status="空置"))
    cdb.flush()
    assert cls.derive_project_status(cdb, p) == "招商中"


def test_manual_status_not_overridden(cdb):
    p = _project(cdb, "P-PREP", "筹备")
    cdb.add(Unit(unit_code="U3", project_id=p.id, status="在租"))
    cdb.flush()
    assert cls.derive_project_status(cdb, p) == "筹备"  # 人工状态保持


def test_recompute_reports_changes(cdb):
    p = _project(cdb, "P-CH", "招商中")
    cdb.add(Unit(unit_code="U4", project_id=p.id, status="自营"))
    cdb.flush()
    changes = cls.recompute_all_statuses(cdb)
    codes = {c["project_code"]: c for c in changes}
    assert "P-CH" in codes and codes["P-CH"]["to"] == "已开业"


# ---------- 业态细分口径 ----------

def test_derive_type_by_keyword():
    assert cls.derive_project_type("两江国际影视城一期", 14132, "商业街区") == "文旅商业"
    assert cls.derive_project_type("龙兴足球训练场", 35112, "商业街区") == "体育场馆商业"
    assert cls.derive_project_type("溪岸云蔚E09底商", 4017, "商业街区") == "社区商业"
    assert cls.derive_project_type("三洞桥风情外街项目", 5966, "购物中心") == "商业街区"


def test_derive_type_by_area_fallback():
    assert cls.derive_project_type("某大体量综合体", 40000, "商业街区") == "购物中心"
    assert cls.derive_project_type("某小微铺", 1200, "商业街区") == "社区商业"


def test_derive_type_keeps_current_when_unsure():
    # 无关键词、面积落在中间带 → 保持原类型（不乱改）
    assert cls.derive_project_type("金融城2号", 20582, "商业街区") == "商业街区"


# ---------- API 层：项目类型校验 ----------

def test_create_project_rejects_unknown_type(client, auth):
    r = client.post("/api/v1/projects", headers=auth, json={
        "project_code": "P-BADTYPE", "project_name": "非法类型项目",
        "project_type": "不存在类型", "project_status": "招商中",
        "province": "重庆市", "city": "重庆市", "district": "两江新区", "address": "测试",
    })
    assert r.status_code == 400
