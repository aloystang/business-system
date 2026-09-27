"""看板 / 系统管理 / 地图聚合周边 集成测试。"""
from __future__ import annotations


# ---------- 工作台看板 ----------

def test_dashboard_summary(client, auth):
    r = client.get("/api/v1/dashboard/summary", headers=auth)
    assert r.status_code == 200
    d = r.json()
    assert d["kpi"]["projects_total"] == 3          # conftest 播种 3 个项目
    assert d["kpi"]["geocode_failed"] == 1          # 御临河定位失败
    assert "招商中" in d["projects_by_status"]
    assert "my_tasks" in d


# ---------- 地图聚合 / 周边 / 卡片 / 图层 ----------

def test_map_aggregate_city(client, auth):
    r = client.get("/api/v1/map/aggregate?level=city", headers=auth)
    assert r.status_code == 200
    buckets = {b["name"]: b["count"] for b in r.json()["buckets"]}
    assert buckets.get("重庆市", 0) >= 2           # 龙兴 + 悦荟城（御临河无坐标不计）


def test_map_aggregate_bad_level(client, auth):
    assert client.get("/api/v1/map/aggregate?level=xx", headers=auth).status_code == 400


def test_map_nearby(client, auth):
    r = client.get("/api/v1/map/projects/1/nearby?radius=5000", headers=auth)
    assert r.status_code == 200
    names = {x["project_name"] for x in r.json()}
    assert "两江悦荟城" in names
    # 距离升序且带米数
    dists = [x["dist_m"] for x in r.json()]
    assert dists == sorted(dists)


def test_map_card(client, auth):
    r = client.get("/api/v1/map/projects/1/card", headers=auth)
    assert r.status_code == 200
    c = r.json()
    assert c["name"] == "龙兴足球场"
    assert "matched_brands" in c and "priority_brands" in c


def test_map_layers(client, auth):
    r = client.get("/api/v1/map/layers", headers=auth)
    assert {l["key"] for l in r.json()["layers"]} >= {"status", "type", "high_match"}


# ---------- 系统管理 ----------

def test_admin_list_roles_and_users(client, auth):
    assert client.get("/api/v1/admin/roles", headers=auth).status_code == 200
    codes = {r["code"] for r in client.get("/api/v1/admin/roles", headers=auth).json()}
    assert "admin" in codes and "viewer" in codes
    users = client.get("/api/v1/admin/users", headers=auth).json()
    assert any(u["username"] == "admin" for u in users)


def test_admin_create_user_and_rbac_guard(client, auth):
    r = client.post("/api/v1/admin/users", headers=auth, json={
        "username": "bd01", "password": "pw123456", "display_name": "拓展一",
        "role": "brand_bd"})
    assert r.status_code == 201 and r.json()["role"] == "brand_bd"

    # 非管理员访问 admin 接口 → 403
    tok = client.post("/api/v1/auth/login",
                      data={"username": "bd01", "password": "pw123456"}).json()["access_token"]
    forbidden = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {tok}"})
    assert forbidden.status_code == 403


def test_admin_create_user_bad_role(client, auth):
    r = client.post("/api/v1/admin/users", headers=auth,
                    json={"username": "x1", "password": "pw123456", "role": "nope"})
    assert r.status_code == 400


def test_admin_audit_logs(client, auth):
    # 先制造一条审计（建品牌）
    client.post("/api/v1/brands", headers=auth,
                json={"brand_code": "B-AUDIT", "brand_name": "审计品牌"})
    r = client.get("/api/v1/admin/audit-logs?entity_type=brand", headers=auth)
    assert r.status_code == 200
    assert any(x["action"] == "create" for x in r.json())


def test_risk_alerts_shape(client, auth):
    r = client.get("/api/v1/dashboard/risk-alerts", headers=auth)
    assert r.status_code == 200
    d = r.json()
    assert "summary" in d and "arrears_top" in d and "expiring_leases" in d and "vacant_top" in d
    assert d["summary"]["total_arrears"] >= 0
