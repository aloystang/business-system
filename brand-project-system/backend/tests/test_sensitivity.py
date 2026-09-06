"""敏感项目脱敏 + 登录失败限流。"""
from __future__ import annotations

import pytest

from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import Project, ProjectLocation, Role, User, UserRole
from app.security import hash_password

SENS_LNG, SENS_LAT = 106.5031, 29.6012
BBOX = "106.0,29.0,107.0,30.0"


def _session():
    return next(app.dependency_overrides[get_db]())


@pytest.fixture(autouse=True)
def _fixtures():
    db = _session()
    if not db.query(Project).filter(Project.project_code == "SENS-1").first():
        p = Project(project_code="SENS-1", project_name="敏感军工配套", project_type="商业街区",
                    project_status="招商中", is_sensitive=True)
        db.add(p); db.flush()
        db.add(ProjectLocation(project_id=p.id, province="重庆市", city="重庆市",
                               district="两江新区", address="真实机密地址88号",
                               longitude=SENS_LNG, latitude=SENS_LAT,
                               geocoding_status="人工确认"))
    if not db.query(User).filter(User.username == "viewer_s").first():
        role = db.query(Role).filter(Role.code == "viewer").first()
        u = User(username="viewer_s", display_name="查看者",
                 password_hash=hash_password("pw123456"), role="viewer")
        db.add(u); db.flush()
        db.add(UserRole(user_id=u.id, role_id=role.id))
    db.commit()
    db.close()


def _auth(client, username, password="pw123456"):
    r = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _find(markers, code):
    return next(m for m in markers if m["project_code"] == code)


def test_admin_sees_exact_sensitive_coords(client, auth):
    markers = client.get(f"/api/v1/map/projects?bbox={BBOX}", headers=auth).json()
    m = _find(markers, "SENS-1")
    assert m["blurred"] is False
    assert m["lng"] == SENS_LNG and m["lat"] == SENS_LAT


def test_viewer_gets_blurred_sensitive_coords(client):
    h = _auth(client, "viewer_s")
    markers = client.get(f"/api/v1/map/projects?bbox={BBOX}", headers=h).json()
    m = _find(markers, "SENS-1")
    assert m["is_sensitive"] is True and m["blurred"] is True
    assert (m["lng"], m["lat"]) != (SENS_LNG, SENS_LAT)  # 坐标被模糊


def test_viewer_card_address_masked(client):
    h = _auth(client, "viewer_s")
    pid = client.get(f"/api/v1/map/projects?bbox={BBOX}", headers=h).json()
    sid = _find(pid, "SENS-1")["id"]
    card = client.get(f"/api/v1/map/projects/{sid}/card", headers=h).json()
    assert "真实机密地址" not in (card["address"] or "")
    assert "脱敏" in card["address"]


def test_login_rate_limited_after_failures(client):
    limit = get_settings().login_max_failures
    for _ in range(limit):
        r = client.post("/api/v1/auth/login",
                        data={"username": "ghost_attacker", "password": "wrong"})
        assert r.status_code == 401
    blocked = client.post("/api/v1/auth/login",
                          data={"username": "ghost_attacker", "password": "wrong"})
    assert blocked.status_code == 429
