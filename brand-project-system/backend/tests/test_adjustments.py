"""业态构成 + 调改计划测算：服务单测(隔离库) + API 校验/权限。"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    Lease, Merchant, Project, Role, Unit, UnitAdjustmentPlan, User, UserRole,
)
from app.security import hash_password
from app.services import tenant_mix


@pytest.fixture
def sdb():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False},
                        poolclass=StaticPool, future=True)
    Base.metadata.create_all(eng)
    s = sessionmaker(bind=eng, future=True)()
    p = Project(project_code="PX", project_name="测试项目", project_type="购物中心",
                project_status="招商中")
    s.add(p); s.flush()
    # 2 在租(带商户+生效租约) + 1 空置
    specs = [("U1", "在租", 100.0, "餐饮", 50000), ("U2", "在租", 200.0, "零售", 90000),
             ("U3", "空置", 150.0, None, 0)]
    for i, (code, st, area, fmt, rent) in enumerate(specs, 1):
        u = Unit(unit_code=code, project_id=p.id, status=st, rentable_area_m2=area)
        s.add(u); s.flush()
        if fmt:
            m = Merchant(merchant_code=f"M{i}", name=f"商户{i}", project_id=p.id,
                         unit_id=u.id, business_format=fmt)
            s.add(m); s.flush()
            s.add(Lease(lease_code=f"L{i}", merchant_id=m.id, project_id=p.id, unit_id=u.id,
                        base_rent=rent, lease_status="生效"))
    s.commit()
    yield s, p
    s.close()


def test_current_mix_totals_and_formats(sdb):
    s, p = sdb
    mix = tenant_mix.current_mix(s, p.id)
    assert mix["totals"]["unit_total"] == 3
    assert mix["totals"]["rented_units"] == 2
    assert mix["totals"]["occupancy_rate"] == round(2 / 3, 4)
    assert mix["vacant"]["units"] == 1
    fmts = {r["format"]: r for r in mix["by_format"]}
    assert set(fmts) == {"餐饮", "零售"}
    assert fmts["零售"]["rent"] == 90000


def test_unit_layout_shape(sdb):
    s, p = sdb
    lay = tenant_mix.unit_layout(s, p.id)
    assert lay["floors"] and len(lay["units"]) == 3
    u1 = next(u for u in lay["units"] if u["status"] == "在租" and u["tenant"])
    assert u1["format"] and u1["rent"] > 0
    vac = next(u for u in lay["units"] if u["status"] == "空置")
    assert vac["tenant"] is None and vac["format"] is None


def test_plan_summary_forecasts_uplift(sdb):
    s, p = sdb
    vacant = s.query(Unit).filter(Unit.project_id == p.id, Unit.status == "空置").first()
    s.add(UnitAdjustmentPlan(project_id=p.id, unit_id=vacant.id, action="新招商",
                             to_format="餐饮", expected_rent_psm=200, plan_status="审批中"))
    s.commit()
    out = tenant_mix.plan_summary(s, p.id)
    assert out["summary"]["plan_items"] == 1
    # 空置铺招商后：出租率与租金都应上升
    assert out["summary"]["planned"]["occupancy_rate"] > out["summary"]["current"]["occupancy_rate"]
    assert out["summary"]["delta"]["rent_total"] == 30000.0   # 150㎡ × 200 元/㎡
    assert out["summary"]["delta"]["noi"] == 30000.0


# ---------- API 层 ----------

def _session():
    return next(app.dependency_overrides[get_db]())


def _make_unit(project_code: str) -> tuple[int, int]:
    db = _session()
    p = db.query(Project).filter(Project.project_code == project_code).first()
    u = db.query(Unit).filter(Unit.project_id == p.id, Unit.unit_code == "ADJ-U1").first()
    if not u:
        u = Unit(unit_code="ADJ-U1", project_id=p.id, status="空置", rentable_area_m2=120.0)
        db.add(u); db.commit()
    ids = (p.id, u.id)
    db.close()
    return ids


def test_put_plan_ok_and_bad_action(client, auth):
    pid, uid = _make_unit("P-1")
    ok = client.put(f"/api/v1/projects/{pid}/adjustment-plan/{uid}", headers=auth,
                    json={"action": "新招商", "to_format": "餐饮", "expected_rent_psm": 180})
    assert ok.status_code == 200
    assert ok.json()["summary"]["plan_items"] >= 1
    bad = client.put(f"/api/v1/projects/{pid}/adjustment-plan/{uid}", headers=auth,
                     json={"action": "乱写", "to_format": "餐饮"})
    assert bad.status_code == 400


def test_viewer_cannot_edit_plan(client):
    db = _session()
    if not db.query(User).filter(User.username == "viewer_adj").first():
        role = db.query(Role).filter(Role.code == "viewer").first()
        u = User(username="viewer_adj", display_name="查看者",
                 password_hash=hash_password("pw123456"), role="viewer")
        db.add(u); db.flush()
        db.add(UserRole(user_id=u.id, role_id=role.id))
        db.commit()
    db.close()
    pid, uid = _make_unit("P-1")
    tok = client.post("/api/v1/auth/login",
                      data={"username": "viewer_adj", "password": "pw123456"}).json()["access_token"]
    r = client.put(f"/api/v1/projects/{pid}/adjustment-plan/{uid}",
                   headers={"Authorization": f"Bearer {tok}"},
                   json={"action": "新招商", "to_format": "餐饮"})
    assert r.status_code == 403
