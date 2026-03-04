import os
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkstemp()[1]}"
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.auth import get_password_hash  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import User, UserRole  # noqa: E402

Base.metadata.create_all(bind=engine)


def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            db.add(
                User(
                    username="admin",
                    password_hash=get_password_hash("admin123"),
                    role=UserRole.admin,
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


def login(client: TestClient) -> str:
    seed_admin()
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def create_project(client: TestClient, headers: dict[str, str]) -> str:
    payload = {
        "project_name": "情报测试项目",
        "city": "重庆市",
        "district": "渝北区",
        "total_area": 10000,
        "asset_distribution": "集中",
        "ownership_structure": "甲方",
        "competition_level": "中",
    }
    resp = client.post("/api/projects", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["project_id"]


def test_intel_sync_and_link_flow():
    client = TestClient(app)
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}
    project_id = create_project(client, headers)

    rule_payload = {
        "name": "重庆招标规则",
        "item_type": "tender",
        "keywords": "港莲广场,两江新区",
        "city": "重庆市",
        "district": "渝北区",
        "budget_min": 1000,
        "is_enabled": 1,
    }
    rule_resp = client.post("/api/intel/rules", json=rule_payload, headers=headers)
    assert rule_resp.status_code == 200, rule_resp.text

    sync_payload = {
        "source_system": "all",
        "item_type": "all",
        "payload_items": [
            {
                "item_type": "tender",
                "title": "港莲广场招商运营招标公告",
                "source_name": "重庆公共资源交易中心",
                "published_at": "2026-02-25 10:00:00",
                "city": "重庆市",
                "district": "渝北区",
                "summary": "项目公开招标",
                "budget_amount": 1500,
                "deadline_at": "2026-03-05 18:00:00",
                "issuer": "港莲广场项目公司",
                "raw_url": "https://example.com/tender/1",
            },
            {
                "item_type": "tender",
                "title": "港莲广场招商运营招标公告",
                "source_name": "重庆公共资源交易中心",
                "published_at": "2026-02-25 10:00:00",
                "city": "重庆市",
                "district": "渝北区",
                "summary": "项目公开招标（重复）",
                "budget_amount": 1550,
                "deadline_at": "2026-03-05 18:00:00",
                "issuer": "港莲广场项目公司",
                "raw_url": "https://example.com/tender/1?v=2",
            },
            {
                "item_type": "news",
                "title": "重庆商业体更新动态",
                "source_name": "重庆日报",
                "published_at": "2026-02-25 09:00:00",
                "city": "重庆市",
                "district": "渝中区",
                "summary": "商圈升级改造",
                "raw_url": "https://example.com/news/1",
            },
        ],
    }
    sync_resp = client.post("/api/intel/sync/run", json=sync_payload, headers=headers)
    assert sync_resp.status_code == 200, sync_resp.text
    sync_data = sync_resp.json()
    assert sync_data["source_system"] == "all"
    assert sync_data["pulled_count"] == 3
    assert sync_data["upserted_count"] == 2
    assert sync_data["deduped_count"] >= 1

    kpi_resp = client.get("/api/intel/kpis?city=重庆市", headers=headers)
    assert kpi_resp.status_code == 200, kpi_resp.text
    kpi_data = kpi_resp.json()
    assert kpi_data["total_count"] >= 2
    assert kpi_data["pending_follow_up_count"] >= 1

    items_resp = client.get("/api/intel/items?item_type=tender&city=重庆市", headers=headers)
    assert items_resp.status_code == 200, items_resp.text
    items_data = items_resp.json()
    assert items_data["total"] >= 1
    item_id = items_data["items"][0]["id"]

    detail_resp = client.get(f"/api/intel/items/{item_id}", headers=headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["item_type"] == "tender"

    link_resp = client.post(
        f"/api/intel/items/{item_id}/link-project",
        json={"project_id": project_id, "link_type": "manual"},
        headers=headers,
    )
    assert link_resp.status_code == 200, link_resp.text

    detail_resp2 = client.get(f"/api/intel/items/{item_id}", headers=headers)
    assert detail_resp2.status_code == 200, detail_resp2.text
    detail2 = detail_resp2.json()
    assert any(link["project_id"] == project_id for link in detail2["linked_projects"])

    jobs_resp = client.get("/api/intel/sync/jobs", headers=headers)
    assert jobs_resp.status_code == 200, jobs_resp.text
    assert len(jobs_resp.json()) >= 1
    assert jobs_resp.json()[0]["source_system"] in {"all", "bidmonitor", "folo"}
