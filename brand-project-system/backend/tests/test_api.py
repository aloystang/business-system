"""API 集成测试。"""
from __future__ import annotations

from app.services.map.base import GEO_AUTO, GeocodeResult


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["coordinate_system"] == "GCJ-02"


def test_login_and_me(client, auth):
    r = client.get("/api/v1/auth/me", headers=auth)
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


def test_login_bad_password(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_map_viewport_excludes_failed_geocode(client, auth):
    r = client.get("/api/v1/map/projects?bbox=106.3,29.4,106.9,29.9", headers=auth)
    assert r.status_code == 200
    names = {m["name"] for m in r.json()}
    assert "龙兴足球场" in names and "两江悦荟城" in names
    assert "御临河商业" not in names          # 定位失败不上图


def test_map_requires_auth(client):
    r = client.get("/api/v1/map/projects?bbox=106,29,107,30")
    assert r.status_code == 401


def test_recommended_brands_hard_gate(client, auth):
    r = client.get("/api/v1/matches/by-project/1", headers=auth)   # 龙兴足球场
    assert r.status_code == 200
    by_brand = {m["brand_name"]: m for m in r.json()}
    assert by_brand["迪卡侬"]["match_grade"] == "优先推进"
    assert by_brand["海底捞"]["hard_gate_triggered"] is True
    assert by_brand["海底捞"]["match_grade"] == "暂不匹配"


def test_compute_and_adjust_guard(client, auth):
    r = client.post("/api/v1/matches/compute", json={"brand_id": 2, "project_id": 2}, headers=auth)
    assert r.status_code == 200
    m = r.json()
    assert m["hard_gate_triggered"] is False
    mid = m["id"]

    ok = client.post(f"/api/v1/matches/{mid}/adjust",
                     json={"manual_adjust": 5, "reason": "片区主力"}, headers=auth)
    assert ok.status_code == 200
    assert ok.json()["final_score"] == round((m["weighted_score"] or 0) + 5, 2)

    bad = client.post(f"/api/v1/matches/{mid}/adjust",
                      json={"manual_adjust": 15, "reason": "x"}, headers=auth)
    assert bad.status_code == 400

    noreason = client.post(f"/api/v1/matches/{mid}/adjust",
                           json={"manual_adjust": 3, "reason": "  "}, headers=auth)
    assert noreason.status_code == 400


def test_create_project_geocodes(client, auth, monkeypatch):
    import app.routers.projects as pr

    def fake_geocode(address, city=None):
        return GeocodeResult(longitude=106.55, latitude=29.60, status=GEO_AUTO,
                             provider="amap", level="乡镇", accuracy="中")

    monkeypatch.setattr(pr, "geocode_address", fake_geocode)
    r = client.post("/api/v1/projects", headers=auth, json={
        "project_code": "P-NEW", "project_name": "三洞桥PARK", "project_type": "商业街区",
        "province": "重庆市", "city": "重庆市", "district": "两江新区", "address": "江北嘴"})
    assert r.status_code == 201
    loc = r.json()["location"]
    assert loc["geocoding_status"] == "自动定位"
    assert loc["longitude"] == 106.55


def test_update_location_invariant_rejected(client, auth):
    # 定位失败却带坐标 → 400
    r = client.put("/api/v1/projects/2/location", headers=auth, json={
        "province": "重庆市", "city": "重庆市", "district": "两江新区", "address": "x",
        "longitude": 106.7, "latitude": 29.6, "geocoding_status": "定位失败"})
    assert r.status_code == 400
