"""四大模块 API 集成测试：CRUD/评分、候选、沟通、任务、字典、审核、导入。"""
from __future__ import annotations

import io

import openpyxl


# ---------- 品牌 CRUD + 评分 ----------

def test_brand_crud_and_scoring(client, auth):
    r = client.post("/api/v1/brands", headers=auth,
                    json={"brand_code": "B-NEW", "brand_name": "名创优品", "l1_category": "零售"})
    assert r.status_code == 201
    bid = r.json()["id"]

    upd = client.patch(f"/api/v1/brands/{bid}", headers=auth, json={"store_count": 500})
    assert upd.status_code == 200 and upd.json()["store_count"] == 500

    sc = client.post(f"/api/v1/brands/{bid}/scores", headers=auth,
                     json={"dims": [19, 18, 17, 18, 17], "basis": "头部品牌"})
    assert sc.status_code == 201
    assert sc.json()["total_score"] == 89 and sc.json()["grade"] == "A"
    assert client.get(f"/api/v1/brands/{bid}", headers=auth).json()["grade"] == "A"


def test_brand_score_out_of_range_rejected(client, auth):
    r = client.post("/api/v1/brands/1/scores", headers=auth, json={"dims": [21, 0, 0, 0, 0]})
    assert r.status_code == 400


# ---------- 候选清单 ----------

def test_candidate_flow(client, auth):
    r = client.post("/api/v1/candidate-lists", headers=auth,
                    json={"list_name": "龙兴候选", "target_project_id": 1})
    lid = r.json()["id"]
    it = client.post(f"/api/v1/candidate-lists/{lid}/items", headers=auth,
                     json={"brand_id": 1, "item_status": "储备"})
    assert it.status_code == 201
    iid = it.json()["id"]
    dup = client.post(f"/api/v1/candidate-lists/{lid}/items", headers=auth, json={"brand_id": 1})
    assert dup.status_code == 409          # 品牌已在清单
    mv = client.patch(f"/api/v1/candidate-lists/{lid}/items/{iid}", headers=auth,
                      json={"item_status": "洽谈中"})
    assert mv.json()["item_status"] == "洽谈中"


# ---------- 沟通 / 任务 ----------

def test_communication_create(client, auth):
    r = client.post("/api/v1/communications", headers=auth, json={
        "related_type": "project", "project_id": 1, "comm_date": "2026-09-05",
        "channel": "电话", "summary": "洽谈迪卡侬"})
    assert r.status_code == 201


def test_task_overdue_filter(client, auth):
    client.post("/api/v1/tasks", headers=auth,
                json={"title": "补龙兴资料", "project_id": 1, "plan_date": "2020-01-01"})
    r = client.get("/api/v1/tasks?overdue=true", headers=auth)
    assert r.status_code == 200
    assert any(t["title"] == "补龙兴资料" for t in r.json())


def test_task_bad_date_rejected(client, auth):
    r = client.post("/api/v1/tasks", headers=auth, json={"title": "x", "plan_date": "2026/1/1"})
    assert r.status_code == 400


# ---------- 字典 / 审核 ----------

def test_dicts_list(client, auth):
    r = client.get("/api/v1/dicts?type=project_type", headers=auth)
    labels = {d["label"] for d in r.json()}
    assert "购物中心" in labels


def test_approval_flow(client, auth):
    r = client.post("/api/v1/approvals", headers=auth,
                    params={"target_type": "brand", "target_id": 1})
    assert r.status_code == 201
    aid = r.json()["id"]
    d = client.post(f"/api/v1/approvals/{aid}/decide", headers=auth, json={"action": "approve"})
    assert d.json()["status"] == "通过"


# ---------- 导入管线 ----------

def _xlsx_bytes():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    ps = wb.create_sheet("5-项目档案")
    ps.append(["project_code", "project_name", "project_type", "project_status",
               "province", "city", "district", "address"])
    ps.append(["IMP-P1", "导入项目一", "购物中心", "招商中", "重庆市", "重庆市", "两江新区", "地址"])
    ps.append(["", "缺码", "购物中心", "招商中", "重庆市", "重庆市", "两江新区", "x"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_import_dry_run_then_commit(client, auth):
    up = client.post("/api/v1/import/batches", headers=auth,
                     files={"file": ("t.xlsx", _xlsx_bytes(),
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert up.status_code == 201
    body = up.json()
    assert body["status"] == "待确认" and body["total_rows"] == 2
    assert body["valid_rows"] == 1 and body["error_rows"] == 1
    bid = body["id"]

    ok = client.post(f"/api/v1/import/batches/{bid}/commit", headers=auth)
    assert ok.status_code == 200 and ok.json()["status"] == "已导入"
    # 已入库
    lst = client.get("/api/v1/projects?q=导入项目一", headers=auth)
    assert any(p["project_code"] == "IMP-P1" for p in lst.json())


def test_import_rejects_non_xlsx(client, auth):
    r = client.post("/api/v1/import/batches", headers=auth,
                    files={"file": ("t.csv", b"a,b", "text/csv")})
    assert r.status_code == 400
