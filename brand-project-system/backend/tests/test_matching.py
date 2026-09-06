"""匹配引擎单元测试（无需数据库，构造瞬态对象）。"""
from __future__ import annotations

import pytest

from app import matching
from app.models import Brand, BrandExpansion, Project, ProjectLocation


def _brand(*, l1="零售", intent="较强", cities="重庆", types="体育场馆商业;购物中心",
           stadium=True, amin=800, amax=2500):
    b = Brand(brand_code="B", brand_name="测试品牌", l1_category=l1, cooperation_intent=intent)
    b.expansion = BrandExpansion(target_cities=cities, acceptable_project_types=types,
                                 accept_stadium_commercial=stadium, area_min=amin, area_max=amax)
    return b


def _project(*, ptype="体育场馆商业", city="重庆市", formats="零售;文体娱乐;餐饮",
             customers="球迷", will="强", area=160958):
    p = Project(project_code="P", project_name="测试项目", project_type=ptype,
                project_status="招商中", business_area_m2=area, leasable_area_m2=area,
                target_formats=formats, core_customers=customers, cooperation_will=will)
    p.location = ProjectLocation(province="重庆市", city=city, district="两江新区",
                                 address="x", longitude=106.7, latitude=29.6)
    return p


def test_hard_gate_stadium_rejected():
    b = _brand(stadium=False)
    r = matching.compute(b, _project(ptype="体育场馆商业"))
    assert r.hard_gate_triggered is True
    assert r.match_grade == "暂不匹配"
    assert r.weighted_score == 0.0


def test_hard_gate_type_not_accepted():
    b = _brand(types="购物中心;商业街区", stadium=True)
    r = matching.compute(b, _project(ptype="体育场馆商业"))
    assert r.hard_gate_triggered is True
    assert r.match_grade == "暂不匹配"


def test_good_match_not_gated_and_graded():
    r = matching.compute(_brand(), _project())
    assert r.hard_gate_triggered is False
    assert r.weighted_score is not None and 0 <= r.weighted_score <= 100
    assert r.match_grade in {"优先推进", "重点储备", "持续观察", "暂不匹配"}
    assert r.data_coverage_rate == 100.0
    assert r.is_formal is True


def test_coverage_below_threshold_not_formal():
    b = Brand(brand_code="B", brand_name="缺资料品牌", l1_category="零售",
              cooperation_intent="强")           # 无 expansion
    r = matching.compute(b, _project())
    assert r.data_coverage_rate < matching.COVERAGE_MIN
    assert r.is_formal is False
    assert "城市区域" in r.pending


def test_weight_renormalization_ignores_missing_dims():
    # 缺失维度不按 0；权重在有资料维度间重新归一
    b = Brand(brand_code="B", brand_name="B", l1_category="零售", cooperation_intent="强")
    r = matching.compute(b, _project())
    present = {k: v for k, v in r.dims.items() if v is not None}
    total_w = sum(matching.WEIGHTS[k] for k in present)
    expect = round(sum(v * matching.WEIGHTS[k] for k, v in present.items()) / total_w, 2)
    assert r.weighted_score == expect


@pytest.mark.parametrize("score,grade", [
    (85, "优先推进"), (84.9, "重点储备"), (70, "重点储备"),
    (55, "持续观察"), (54.9, "暂不匹配"), (0, "暂不匹配"),
])
def test_grade_thresholds(score, grade):
    assert matching._grade_of(score) == grade


def test_weights_sum_to_one():
    assert round(sum(matching.WEIGHTS.values()), 6) == 1.0
