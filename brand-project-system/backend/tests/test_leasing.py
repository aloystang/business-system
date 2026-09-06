"""出租经营台账 + 经营聚合 集成测试。每个用例用独立项目+唯一编码，保证聚合可断言。"""
from __future__ import annotations

import itertools

_seq = itertools.count(1)


def _new_project(client, auth) -> int:
    n = next(_seq)
    r = client.post("/api/v1/projects", headers=auth, json={
        "project_code": f"OPS-P{n}", "project_name": f"台账项目{n}", "project_type": "购物中心",
        "province": "重庆市", "city": "重庆市", "district": "两江新区", "address": "x"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _scenario(client, auth, pid: int, tag: str):
    """在指定项目建 铺位→商户→租约→收费(欠租)→成本。"""
    uid = client.post("/api/v1/units", headers=auth, json={
        "unit_code": f"U-{tag}", "project_id": pid, "rentable_area_m2": 100.0,
        "status": "空置"}).json()["id"]
    mid = client.post("/api/v1/merchants", headers=auth, json={
        "merchant_code": f"M-{tag}", "name": "台账商户", "project_id": pid,
        "unit_id": uid}).json()["id"]
    lid = client.post("/api/v1/leases", headers=auth, json={
        "lease_code": f"L-{tag}", "merchant_id": mid, "project_id": pid, "unit_id": uid,
        "base_rent": 10000, "management_fee": 1000}).json()["id"]
    r1 = client.post("/api/v1/receivables", headers=auth, json={
        "receivable_code": f"R-{tag}-1", "lease_id": lid, "project_id": pid, "fee_item": "租金",
        "period": "2026-08", "due_date": "2026-08-05", "amount_due": 10000,
        "amount_received": 8000}).json()
    client.post("/api/v1/receivables", headers=auth, json={
        "receivable_code": f"R-{tag}-2", "lease_id": lid, "project_id": pid, "fee_item": "物业费",
        "period": "2026-08", "amount_due": 1000, "amount_received": 1000})
    client.post("/api/v1/project-costs", headers=auth, json={
        "project_id": pid, "period": "2026-08", "cost_type": "物业成本", "amount": 3000})
    client.post("/api/v1/project-costs", headers=auth, json={
        "project_id": pid, "period": "2026-08", "cost_type": "水电能耗", "amount": 500})
    return uid, mid, lid, r1


def test_lease_sets_unit_rented(client, auth):
    pid = _new_project(client, auth)
    uid, *_ = _scenario(client, auth, pid, "A")
    assert client.get(f"/api/v1/units/{uid}", headers=auth).json()["status"] == "在租"


def test_receivable_arrears_computed(client, auth):
    pid = _new_project(client, auth)
    *_, r1 = _scenario(client, auth, pid, "B")
    assert r1["arrears"] == 2000 and r1["collect_status"] == "催收中"


def test_project_operations_math(client, auth):
    pid = _new_project(client, auth)
    _scenario(client, auth, pid, "C")
    op = client.get(f"/api/v1/projects/{pid}/operations", headers=auth).json()
    assert op["revenue"]["revenue_received_total"] == 9000
    assert op["revenue"]["revenue_due_total"] == 11000
    assert op["revenue"]["arrears_total"] == 2000
    assert op["cost"]["cost_total"] == 3500
    assert op["noi"] == 5500
    assert op["occupancy"]["rented"] == 1 and op["occupancy"]["unit_total"] == 1


def test_portfolio_operations(client, auth):
    pid = _new_project(client, auth)
    _scenario(client, auth, pid, "D")
    d = client.get("/api/v1/dashboard/operations", headers=auth).json()
    assert d["kpi"]["project_count"] >= 1
    assert any(p["project_id"] == pid for p in d["projects"])
    assert "物业成本" in d["cost_structure"]


def test_unit_match_compute(client, auth):
    pid = _new_project(client, auth)
    uid = client.post("/api/v1/units", headers=auth, json={
        "unit_code": "MU-1", "project_id": pid, "status": "空置"}).json()["id"]
    r = client.post("/api/v1/unit-matches", headers=auth,
                    json={"unit_id": uid, "brand_id": 1, "dims": [20, 15, 15, 10, 15]})
    assert r.status_code == 201
    assert r.json()["total"] == 75 and r.json()["grade"] == "重点储备"


def test_unit_match_bad_dims(client, auth):
    pid = _new_project(client, auth)
    uid = client.post("/api/v1/units", headers=auth, json={
        "unit_code": "MU-2", "project_id": pid, "status": "空置"}).json()["id"]
    r = client.post("/api/v1/unit-matches", headers=auth,
                    json={"unit_id": uid, "brand_id": 1, "dims": [25, 0, 0, 0, 0]})
    assert r.status_code == 400


def test_merchant_assessment(client, auth):
    pid = _new_project(client, auth)
    mid = client.post("/api/v1/merchants", headers=auth, json={
        "merchant_code": "AM-1", "name": "评估商户", "project_id": pid}).json()["id"]
    r = client.post("/api/v1/merchant-assessments", headers=auth,
                    json={"merchant_id": mid, "dims": [20, 18, 17, 15]})
    assert r.status_code == 201
    assert r.json()["total"] == 70 and r.json()["action"] == "维持"
